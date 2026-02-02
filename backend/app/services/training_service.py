"""
Training Service

Handles the training pipeline:
Dataset → Validation → Feature Pipeline → Training → Evaluation → Registry

Responsibilities:
- Job management
- Training orchestration
- Progress tracking
- Model registration
"""

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.core.config import settings
from app.schemas.training import (
    TrainingConfig,
    TrainingJobResponse,
    TrainingStatus,
)


class TrainingService:
    """
    Service for handling training jobs.
    
    Follows ML System Boundaries:
    - Deterministic pipelines
    - Explicit input/output contracts
    - No UI logic
    """
    
    def __init__(
        self,
        model_path: Path | None = None,
        dataset_path: Path | None = None,
    ) -> None:
        """
        Initialize training service.
        
        Args:
            model_path: Path to model registry
            dataset_path: Path to datasets
        """
        self.model_path = model_path or settings.ml_model_path
        self.dataset_path = dataset_path or settings.ml_dataset_path
        self._jobs: dict[UUID, TrainingJobResponse] = {}
    
    async def start_training(self, config: TrainingConfig) -> TrainingJobResponse:
        """
        Start a new training job.
        
        Args:
            config: Training configuration
        
        Returns:
            Training job response
        """
        job_id = uuid4()
        
        job = TrainingJobResponse(
            job_id=job_id,
            status=TrainingStatus.QUEUED,
            config=config,
            total_epochs=config.hyperparameters.epochs,
            message="Job queued for processing",
        )
        
        self._jobs[job_id] = job
        
        # TODO: Submit to job queue (Celery, etc.)
        
        return job
    
    async def get_job(self, job_id: UUID) -> TrainingJobResponse | None:
        """
        Get training job by ID.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job response or None
        """
        return self._jobs.get(job_id)
    
    async def list_jobs(
        self,
        status_filter: TrainingStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[TrainingJobResponse], int]:
        """
        List training jobs.
        
        Args:
            status_filter: Optional status filter
            skip: Pagination offset
            limit: Max results
        
        Returns:
            Tuple of (jobs, total_count)
        """
        jobs = list(self._jobs.values())
        
        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]
        
        total = len(jobs)
        jobs = jobs[skip:skip + limit]
        
        return jobs, total
    
    async def cancel_job(self, job_id: UUID) -> bool:
        """
        Cancel a training job.
        
        Args:
            job_id: Job identifier
        
        Returns:
            True if cancelled, False if not found
        """
        job = self._jobs.get(job_id)
        if not job:
            return False
        
        if job.status in {TrainingStatus.COMPLETED, TrainingStatus.FAILED}:
            return False
        
        job.status = TrainingStatus.CANCELLED
        job.message = "Job cancelled by user"
        
        # TODO: Actually cancel the running job
        
        return True
    
    async def get_metrics(self, job_id: UUID) -> dict[str, Any]:
        """
        Get training metrics for a job.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Metrics dictionary
        """
        # TODO: Implement metrics storage and retrieval
        return {
            "job_id": str(job_id),
            "metrics": {},
            "history": [],
        }


# Service singleton
_training_service: TrainingService | None = None


def get_training_service() -> TrainingService:
    """Get or create training service instance."""
    global _training_service
    if _training_service is None:
        _training_service = TrainingService()
    return _training_service
