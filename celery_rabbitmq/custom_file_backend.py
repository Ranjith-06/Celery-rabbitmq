# celery_rabbitmq/custom_backend.py
import json
from celery.backends.filesystem import FilesystemBackend
import os
from threading import Lock
from collections import deque
from pathlib import Path

LATEST_DIR = "latest"
LATEST_LIMIT = 5
BASE_DIR = Path("/var/mytasks")

class OrganizedFilesystemBackend(FilesystemBackend):
    _latest_lock = Lock()
    _latest_tasks = deque(maxlen=LATEST_LIMIT)
    def __init__(self, app=None, url=None, **kwargs):
        # Ensure url is properly set
        print("???????????",app)
        self.location=BASE_DIR
        if not url:
            url = 'file:///var/mytasks'
        super().__init__(app=app, url=url, **kwargs)

    def get_path_for_task(self, task_id):
        # Create a two-level directory structure based on task_id
        # Example: abcdef -> ab/cd/abcdef
        location =  BASE_DIR
        # Shard based on first 2 chars of task_id
        shard_dir = os.path.join(location, f"shard_{task_id[:2]}")
        os.makedirs(shard_dir, exist_ok=True)
        return os.path.join(shard_dir, task_id)

    def get_task_result(self, task_id):
        """Get task result directly from backend storage"""
        try:
            filename = self.get_path_for_task(task_id)
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _store_result(self, task_id, result, state, traceback=None, request=None, **kwargs):
        # path = self.get_path_for_task(task_id)
        # print(path,task_id)
        # dirname = os.path.dirname(path)
        # print('dirname----------------')
        # print(dirname)
        # print(os.path.exists(dirname))
        # if not os.path.exists(dirname):
        #     os.makedirs(dirname, 0o755, exist_ok=True)
            
        # return super()._store_result(
        #     task_id=task_id,
        #     result=result,
        #     state=state,
        #     traceback=traceback,
        #     request=request,
        #     **kwargs
        # )
        # print(state,'??????????--------------------------------------------------------????',result)
        
        # filename = self.get_path_for_task(task_id)
        # content = self.encode_result(result, state)
        # with open(filename, 'w') as f:
        #     json.dump(content, f)

        # with open(filename, 'w') as f:
        #     json.dump(content, f, indent=2)

        # # Also store a copy in "latest" folder
        # latest_path = os.path.join(self.location, LATEST_DIR)
        # os.makedirs(latest_path, exist_ok=True)
        # copy_path = os.path.join(latest_path, task_id)
        # with self._latest_lock:
        #     self._latest_tasks.append(task_id)
        #     with open(copy_path, 'w') as f:
        #         json.dump(content, f)
            

        #     # Clean up if >100
        #     if len(self._latest_tasks) == self._latest_tasks.maxlen + 1:
        #         oldest = self._latest_tasks.popleft()
        #         old_file = os.path.join(latest_path, oldest)
        #         if os.path.exists(old_file):
        #             os.remove(old_file)

        # return result
        try:
            filename = self.get_path_for_task(task_id)
            content = {
                'result': result,
                'status': state,
                'traceback': traceback,
                'task_id': task_id
            }
            print(state,"=====================",result)
            if state=="REVOKED"  :
                if isinstance(result, Exception) or (
                    isinstance(result, dict) and result.get('exc_type') == 'TaskRevokedError'
                ):
                    return result

            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Write to main storage
            with open(filename, 'w') as f:
                json.dump(content, f, indent=2)

            # Store in latest directory
            latest_path = os.path.join(self.location, LATEST_DIR)
            os.makedirs(latest_path, exist_ok=True)
            copy_path = os.path.join(latest_path, task_id)
            
            with self._latest_lock:
                self._latest_tasks.append(task_id)
                with open(copy_path, 'w') as f:
                    json.dump(content, f)

                # Clean up old files
                if len(self._latest_tasks) > LATEST_LIMIT:
                    oldest = self._latest_tasks.popleft()
                    old_file = os.path.join(latest_path, oldest)
                    try:
                        if os.path.exists(old_file):
                            os.remove(old_file)
                    except OSError as e:
                        
                        print(f"Couldn't remove old task file {old_file}: {e}")

            return result
        except Exception as e:
            print(f"Failed to store result for task {task_id}: {e}")
            raise