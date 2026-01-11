"""Background job manager for reindexing with status tracking

Design:
- Uses ThreadPoolExecutor to run reindex jobs in background (simple and reliable
  for demo). Jobs tracked in-memory with status and result metadata.
- API: start_reindex(callable) -> job_id, get_status(job_id) -> dict

Note: this is intentionally small; for production consider a proper job
queue (Redis/DB + worker processes).
"""
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Dict, Any
import uuid
import time


class ReindexJobManager:
    def __init__(self, max_workers: int = 1):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs: Dict[str, Dict[str, Any]] = {}

    def start_reindex(self, fn: Callable[..., Dict[str, Any]], *args, **kwargs) -> str:
        job_id = str(uuid.uuid4())
        started_at = time.time()
        future: Future = self.executor.submit(fn, *args, **kwargs)
        self.jobs[job_id] = {
            "future": future,
            "status": "running",
            "created_at": started_at,
            "started_at": started_at,
            "finished_at": None,
            "result": None,
            "error": None,
        }

        def _cb(fut: Future):
            try:
                res = fut.result()
                self.jobs[job_id]["status"] = "finished"
                self.jobs[job_id]["result"] = res
                self.jobs[job_id]["finished_at"] = time.time()
            except Exception as e:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["error"] = str(e)
                self.jobs[job_id]["finished_at"] = time.time()

        future.add_done_callback(_cb)
        return job_id

    def get_status(self, job_id: str) -> Dict[str, Any]:
        j = self.jobs.get(job_id)
        if not j:
            return {"status": "not_found"}
        info = {
            "status": j.get("status"),
            "created_at": j.get("created_at"),
            "started_at": j.get("started_at"),
            "finished_at": j.get("finished_at"),
            "result": j.get("result"),
            "error": j.get("error"),
        }
        return info


# singleton manager for the app
manager = ReindexJobManager()