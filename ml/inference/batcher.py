"""
Inference Batcher

Efficient batching for inference requests.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Iterator

import numpy as np
from numpy.typing import NDArray


logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """
    Batching configuration.
    
    Attributes:
        batch_size: Maximum batch size
        timeout_ms: Timeout for batch accumulation
        dynamic_batching: Enable dynamic batch sizing
        min_batch_size: Minimum batch size for dynamic batching
    """
    
    batch_size: int = 32
    timeout_ms: float = 100.0
    dynamic_batching: bool = False
    min_batch_size: int = 1


class InferenceBatcher:
    """
    Efficient batching for inference.
    
    Features:
    - Configurable batch sizes
    - Automatic padding for incomplete batches
    - Generator-based iteration for memory efficiency
    
    Example:
        >>> batcher = InferenceBatcher(BatchConfig(batch_size=16))
        >>> for batch in batcher.batch(images):
        ...     predictions = model.predict(batch)
    """
    
    def __init__(self, config: BatchConfig) -> None:
        """
        Initialize batcher.
        
        Args:
            config: Batching configuration
        """
        self.config = config
    
    def batch(
        self,
        items: list[NDArray[np.float32]] | NDArray[np.float32],
    ) -> Iterator[tuple[NDArray[np.float32], int]]:
        """
        Batch items for inference.
        
        Args:
            items: List of images or array of images
        
        Yields:
            Tuple of (batch, actual_size) where actual_size is the
            number of real items (excluding padding)
        """
        if isinstance(items, np.ndarray):
            items = list(items)
        
        n_items = len(items)
        batch_size = self.config.batch_size
        
        for start_idx in range(0, n_items, batch_size):
            end_idx = min(start_idx + batch_size, n_items)
            batch_items = items[start_idx:end_idx]
            actual_size = len(batch_items)
            
            # Stack into batch
            batch = np.stack(batch_items, axis=0)
            
            yield batch, actual_size
    
    def batch_with_indices(
        self,
        items: list[NDArray[np.float32]] | NDArray[np.float32],
    ) -> Iterator[tuple[NDArray[np.float32], list[int]]]:
        """
        Batch items with original indices.
        
        Args:
            items: List of images or array of images
        
        Yields:
            Tuple of (batch, indices)
        """
        if isinstance(items, np.ndarray):
            items = list(items)
        
        n_items = len(items)
        batch_size = self.config.batch_size
        
        for start_idx in range(0, n_items, batch_size):
            end_idx = min(start_idx + batch_size, n_items)
            batch_items = items[start_idx:end_idx]
            indices = list(range(start_idx, end_idx))
            
            batch = np.stack(batch_items, axis=0)
            yield batch, indices
    
    def optimal_batch_size(
        self,
        n_items: int,
        memory_limit_mb: float = 1024.0,
        item_size_mb: float | None = None,
    ) -> int:
        """
        Calculate optimal batch size based on memory.
        
        Args:
            n_items: Number of items to process
            memory_limit_mb: Memory limit in MB
            item_size_mb: Size of single item in MB
        
        Returns:
            Optimal batch size
        """
        if not self.config.dynamic_batching:
            return min(self.config.batch_size, n_items)
        
        if item_size_mb is None:
            # Assume 224x224x3 float32 image
            item_size_mb = 224 * 224 * 3 * 4 / (1024 * 1024)
        
        # Calculate max batch that fits in memory
        max_batch = int(memory_limit_mb / item_size_mb)
        
        # Clamp between min and max
        optimal = max(
            self.config.min_batch_size,
            min(max_batch, self.config.batch_size, n_items),
        )
        
        logger.debug(f"Optimal batch size: {optimal}")
        return optimal


class AsyncBatcher:
    """
    Asynchronous batcher for accumulating requests.
    
    Useful for serving scenarios where requests arrive over time.
    """
    
    def __init__(self, config: BatchConfig) -> None:
        """
        Initialize async batcher.
        
        Args:
            config: Batching configuration
        """
        self.config = config
        self._pending: list[tuple[NDArray[np.float32], Any]] = []
        self._last_flush: float = time.time()
    
    def add(
        self,
        item: NDArray[np.float32],
        context: Any = None,
    ) -> list[tuple[NDArray[np.float32], list[Any]]] | None:
        """
        Add item to pending batch.
        
        Args:
            item: Image to add
            context: Optional context to return with results
        
        Returns:
            Batch ready for processing, or None if accumulating
        """
        self._pending.append((item, context))
        
        # Check if batch is ready
        if self._should_flush():
            return self._flush()
        
        return None
    
    def _should_flush(self) -> bool:
        """Check if batch should be flushed."""
        # Full batch
        if len(self._pending) >= self.config.batch_size:
            return True
        
        # Timeout
        elapsed_ms = (time.time() - self._last_flush) * 1000
        if elapsed_ms >= self.config.timeout_ms and len(self._pending) > 0:
            return True
        
        return False
    
    def _flush(self) -> list[tuple[NDArray[np.float32], list[Any]]]:
        """Flush pending items as batches."""
        batches = []
        
        while self._pending:
            batch_items = self._pending[:self.config.batch_size]
            self._pending = self._pending[self.config.batch_size:]
            
            images = np.stack([item[0] for item in batch_items], axis=0)
            contexts = [item[1] for item in batch_items]
            
            batches.append((images, contexts))
        
        self._last_flush = time.time()
        return batches
    
    def flush_remaining(self) -> list[tuple[NDArray[np.float32], list[Any]]] | None:
        """Flush any remaining items."""
        if self._pending:
            return self._flush()
        return None
