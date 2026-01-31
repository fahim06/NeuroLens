"""
Experiment Runner

MLflow-based experiment tracking and management.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


logger = logging.getLogger(__name__)

try:
    import mlflow
    from mlflow.tracking import MlflowClient
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False
    mlflow = None
    MlflowClient = None


@dataclass
class ExperimentConfig:
    """
    Experiment configuration.
    
    Attributes:
        name: Experiment name
        tracking_uri: MLflow tracking URI
        artifact_location: Artifact storage location
        tags: Experiment tags
        description: Experiment description
    """
    
    name: str = "neurolens"
    tracking_uri: str = "mlruns"
    artifact_location: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    description: str = ""
    
    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "ExperimentConfig":
        """Create from dictionary."""
        mlflow_config = config.get("mlflow", config)
        return cls(
            name=mlflow_config.get("experiment_name", "neurolens"),
            tracking_uri=mlflow_config.get("tracking_uri", "mlruns"),
            artifact_location=mlflow_config.get("artifact_location"),
            tags=mlflow_config.get("tags", {}),
        )


class ExperimentRunner:
    """
    MLflow-based experiment runner.
    
    Manages experiment lifecycle:
    - Creating/loading experiments
    - Starting/ending runs
    - Logging parameters, metrics, and artifacts
    - Model registration
    
    Example:
        >>> runner = ExperimentRunner(ExperimentConfig(name="my_exp"))
        >>> with runner.start_run("efficientnet_v1"):
        ...     runner.log_params({"epochs": 100, "lr": 0.001})
        ...     runner.log_metrics({"accuracy": 0.95})
        ...     runner.log_model(model, "model")
    """
    
    def __init__(self, config: ExperimentConfig) -> None:
        """
        Initialize experiment runner.
        
        Args:
            config: Experiment configuration
        """
        if not HAS_MLFLOW:
            raise ImportError("MLflow is required. Install with: pip install mlflow")
        
        self.config = config
        self._active_run: mlflow.ActiveRun | None = None
        self._experiment_id: str | None = None
        
        # Set tracking URI
        mlflow.set_tracking_uri(config.tracking_uri)
        
        # Create or get experiment
        self._setup_experiment()
    
    def _setup_experiment(self) -> None:
        """Set up MLflow experiment."""
        experiment = mlflow.get_experiment_by_name(self.config.name)
        
        if experiment is None:
            self._experiment_id = mlflow.create_experiment(
                name=self.config.name,
                artifact_location=self.config.artifact_location,
                tags=self.config.tags,
            )
            logger.info(f"Created experiment: {self.config.name}")
        else:
            self._experiment_id = experiment.experiment_id
            logger.info(f"Using existing experiment: {self.config.name}")
        
        mlflow.set_experiment(self.config.name)
    
    @property
    def experiment_id(self) -> str | None:
        """Get experiment ID."""
        return self._experiment_id
    
    @property
    def active_run(self) -> mlflow.ActiveRun | None:
        """Get active run."""
        return self._active_run
    
    def start_run(
        self,
        run_name: str | None = None,
        tags: dict[str, str] | None = None,
        nested: bool = False,
    ) -> mlflow.ActiveRun:
        """
        Start a new run.
        
        Args:
            run_name: Optional run name
            tags: Optional run tags
            nested: Whether this is a nested run
        
        Returns:
            Active run context
        """
        if run_name is None:
            run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self._active_run = mlflow.start_run(
            run_name=run_name,
            tags=tags,
            nested=nested,
        )
        
        logger.info(f"Started run: {run_name}")
        return self._active_run
    
    def end_run(self, status: str = "FINISHED") -> None:
        """
        End the active run.
        
        Args:
            status: Run status (FINISHED, FAILED, KILLED)
        """
        if self._active_run:
            mlflow.end_run(status=status)
            logger.info(f"Ended run with status: {status}")
            self._active_run = None
    
    def log_params(self, params: dict[str, Any]) -> None:
        """
        Log parameters.
        
        Args:
            params: Dictionary of parameters
        """
        # Flatten nested dictionaries
        flat_params = self._flatten_dict(params)
        
        # MLflow has a limit on param value length
        for key, value in flat_params.items():
            str_value = str(value)
            if len(str_value) > 250:
                str_value = str_value[:247] + "..."
            mlflow.log_param(key, str_value)
    
    def log_metrics(
        self,
        metrics: dict[str, float],
        step: int | None = None,
    ) -> None:
        """
        Log metrics.
        
        Args:
            metrics: Dictionary of metrics
            step: Optional step number
        """
        mlflow.log_metrics(metrics, step=step)
    
    def log_artifact(self, local_path: str | Path, artifact_path: str | None = None) -> None:
        """
        Log an artifact file.
        
        Args:
            local_path: Path to local file
            artifact_path: Path within artifact store
        """
        mlflow.log_artifact(str(local_path), artifact_path)
    
    def log_artifacts(self, local_dir: str | Path, artifact_path: str | None = None) -> None:
        """
        Log all files in a directory as artifacts.
        
        Args:
            local_dir: Local directory path
            artifact_path: Path within artifact store
        """
        mlflow.log_artifacts(str(local_dir), artifact_path)
    
    def log_model(
        self,
        model: Any,
        artifact_path: str,
        registered_model_name: str | None = None,
    ) -> None:
        """
        Log a model.
        
        Args:
            model: Model to log
            artifact_path: Artifact path
            registered_model_name: Name for model registry
        """
        # Try to determine model type
        try:
            import tensorflow as tf
            if isinstance(model, tf.keras.Model):
                mlflow.tensorflow.log_model(
                    model,
                    artifact_path,
                    registered_model_name=registered_model_name,
                )
                return
        except ImportError:
            pass
        
        # Fallback to generic model logging
        mlflow.log_artifact(str(model), artifact_path)
    
    def log_dict(self, dictionary: dict[str, Any], artifact_file: str) -> None:
        """
        Log a dictionary as a YAML artifact.
        
        Args:
            dictionary: Dictionary to log
            artifact_file: Artifact filename
        """
        mlflow.log_dict(dictionary, artifact_file)
    
    def log_config(self, config_path: str | Path) -> None:
        """
        Log a config file as artifact.
        
        Args:
            config_path: Path to config file
        """
        config_path = Path(config_path)
        if config_path.exists():
            mlflow.log_artifact(str(config_path), "config")
    
    def log_training_history(
        self,
        history: dict[str, list[float]],
    ) -> None:
        """
        Log training history epoch by epoch.
        
        Args:
            history: Training history dictionary
        """
        # Get number of epochs
        num_epochs = len(next(iter(history.values())))
        
        for epoch in range(num_epochs):
            epoch_metrics = {
                key: values[epoch]
                for key, values in history.items()
            }
            self.log_metrics(epoch_metrics, step=epoch + 1)
    
    def set_tag(self, key: str, value: str) -> None:
        """Set a tag on the active run."""
        mlflow.set_tag(key, value)
    
    def set_tags(self, tags: dict[str, str]) -> None:
        """Set multiple tags."""
        mlflow.set_tags(tags)
    
    def get_run_id(self) -> str | None:
        """Get current run ID."""
        if self._active_run:
            return self._active_run.info.run_id
        return None
    
    def get_artifact_uri(self) -> str | None:
        """Get artifact URI for current run."""
        if self._active_run:
            return mlflow.get_artifact_uri()
        return None
    
    def list_runs(
        self,
        max_results: int = 100,
        filter_string: str = "",
    ) -> list[dict[str, Any]]:
        """
        List runs in the experiment.
        
        Args:
            max_results: Maximum number of runs
            filter_string: Filter expression
        
        Returns:
            List of run information
        """
        client = MlflowClient()
        runs = client.search_runs(
            experiment_ids=[self._experiment_id],
            filter_string=filter_string,
            max_results=max_results,
        )
        
        return [
            {
                "run_id": run.info.run_id,
                "run_name": run.info.run_name,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "metrics": run.data.metrics,
                "params": run.data.params,
            }
            for run in runs
        ]
    
    def get_best_run(
        self,
        metric: str = "val_accuracy",
        ascending: bool = False,
    ) -> dict[str, Any] | None:
        """
        Get the best run based on a metric.
        
        Args:
            metric: Metric to optimize
            ascending: If True, lower is better
        
        Returns:
            Best run information
        """
        order = "ASC" if ascending else "DESC"
        filter_string = f"metrics.{metric} IS NOT NULL"
        
        client = MlflowClient()
        runs = client.search_runs(
            experiment_ids=[self._experiment_id],
            filter_string=filter_string,
            order_by=[f"metrics.{metric} {order}"],
            max_results=1,
        )
        
        if runs:
            run = runs[0]
            return {
                "run_id": run.info.run_id,
                "run_name": run.info.run_name,
                "metrics": run.data.metrics,
                "params": run.data.params,
            }
        return None
    
    @staticmethod
    def _flatten_dict(
        d: dict[str, Any],
        parent_key: str = "",
        sep: str = ".",
    ) -> dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(
                    ExperimentRunner._flatten_dict(v, new_key, sep).items()
                )
            else:
                items.append((new_key, v))
        return dict(items)
    
    def __enter__(self) -> "ExperimentRunner":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        if exc_type:
            self.end_run(status="FAILED")
        else:
            self.end_run(status="FINISHED")
