
import threading
from contextlib import contextmanager, ExitStack


class ResourceManager:
    """
    Operating System resource synchronization engine.

    Uses mutex locks and semaphores to coordinate
    concurrent access to shared booking resources.

    These locks are process-local. Database row locks
    remain responsible for cross-process synchronization.
    """

    def __init__(self):
        self._registry_lock = threading.Lock()
        self._resource_locks = {}
        self._semaphores = {}

    def get_mutex(self, resource_id):
        """Get or create a mutex for a resource."""

        with self._registry_lock:
            if resource_id not in self._resource_locks:
                self._resource_locks[resource_id] = threading.RLock()

            return self._resource_locks[resource_id]

    def get_semaphore(self, resource_id, capacity):
        """Get or create a semaphore for a resource."""

        if capacity <= 0:
            raise ValueError("Semaphore capacity must be positive.")

        with self._registry_lock:
            if resource_id not in self._semaphores:
                self._semaphores[resource_id] = (
                    threading.BoundedSemaphore(capacity)
                )

            return self._semaphores[resource_id]

    @contextmanager
    def acquire_resources(self, resource_ids):
        """
        Acquire multiple resource mutexes safely.

        Sorted acquisition order helps prevent deadlocks.
        """

        locks = [
            self.get_mutex(resource_id)
            for resource_id in sorted(set(resource_ids))
        ]

        with ExitStack() as stack:
            for lock in locks:
                stack.enter_context(lock)

            yield

    @contextmanager
    def acquire_semaphore(self, resource_id, capacity, timeout=None):
        """Temporarily acquire a limited resource."""

        semaphore = self.get_semaphore(resource_id, capacity)

        acquired = semaphore.acquire(timeout=timeout)

        if not acquired:
            raise TimeoutError(
                f"Resource {resource_id} is currently unavailable."
            )

        try:
            yield
        finally:
            semaphore.release()


# Shared manager instance
resource_manager = ResourceManager()


def get_resource_manager():
    """Return the shared resource manager."""
    return resource_manager
