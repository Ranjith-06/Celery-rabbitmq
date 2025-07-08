import os
import json
from celery.backends.file import FileBackend
from threading import Lock
from collections import deque

LATEST_DIR = "latest"
LATEST_LIMIT = 100

class CustomFileBackend(FileBackend):
    _latest_lock = Lock()
    _latest_tasks = deque(maxlen=LATEST_LIMIT)

    def _get_task_filename(self, task_id):
        location = self.location
        # Shard based on first 2 chars of task_id
        shard_dir = os.path.join(location, f"shard_{task_id[:2]}")
        os.makedirs(shard_dir, exist_ok=True)
        return os.path.join(shard_dir, task_id)

    def store_result(self, task_id, result, status, traceback=None, request=None, **kwargs):
        # Store main result file
        filename = self._get_task_filename(task_id)
        content = self.encode_result(result, status, traceback)
        with open(filename, 'w') as f:
            json.dump(content, f)

        # Also store a copy in "latest" folder
        latest_path = os.path.join(self.location, LATEST_DIR)
        os.makedirs(latest_path, exist_ok=True)
        copy_path = os.path.join(latest_path, task_id)
        with self._latest_lock:
            self._latest_tasks.append(task_id)
            with open(copy_path, 'w') as f:
                json.dump(content, f)

            # Clean up if >100
            if len(self._latest_tasks) == self._latest_tasks.maxlen + 1:
                oldest = self._latest_tasks.popleft()
                old_file = os.path.join(latest_path, oldest)
                if os.path.exists(old_file):
                    os.remove(old_file)

        return result
