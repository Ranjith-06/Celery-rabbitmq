# custom_backend.py

import os
import json
from pathlib import Path
from celery.backends.filesystem import FilesystemBackend

MAX_TASKS_PER_SHARD = 10
BASE_DIR = Path("/var/mytasks")

class ShardedFileBackend(FilesystemBackend):
    def __init__(self, app, location=None, **kwargs):
        self.app = app
        self.location = location or str(BASE_DIR)
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        (BASE_DIR / "active").mkdir(exist_ok=True)
        super().__init__(app, self.location, **kwargs)

    def _find_or_create_shard(self):
        for i in range(100000):  # supports up to 1 million folders
            shard_dir = BASE_DIR / f"shard_{i}"
            shard_dir.mkdir(exist_ok=True)
            files = list(shard_dir.iterdir())
            task_count = sum(1 for f in files if f.is_file())
            if task_count < MAX_TASKS_PER_SHARD:
                return shard_dir
        raise RuntimeError("All shard folders are full")

    def _get_task_filename(self, task_id):
        shard_dir = self._find_or_create_shard()
        task_path = shard_dir / task_id
        return str(task_path)

    def _store_result(self, task_id, result, state, traceback, request=None, **kwargs):
        filename = Path(self._get_task_filename(task_id))

        # Save result as JSON
        with open(filename, "w") as f:
            json.dump({
                "task_id": task_id,
                "status": state,
                "result": result,
                "traceback": traceback,
            }, f)

        # If still running, create symlink in active/
        if state in ("PENDING", "STARTED"):
            active_link = BASE_DIR / "active" / task_id
            if not active_link.exists():
                os.symlink(filename, active_link)

        # Remove symlink if task completed
        if state in ("SUCCESS", "FAILURE", "REVOKED"):
            active_link = BASE_DIR / "active" / task_id
            if active_link.exists():
                active_link.unlink()

        return result
