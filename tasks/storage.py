import json
import os
from datetime import datetime

TASK_STORAGE_PATH = '/var/mytasks/latest'  # Adjust as needed

def ensure_storage_path():
    os.makedirs(TASK_STORAGE_PATH, exist_ok=True)

def save_task_result(task_id, result):
    ensure_storage_path()
    filename = f"{TASK_STORAGE_PATH}/{task_id}.json"
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'result': result
        }, f, indent=2)
def load_task_result(task_id):
    filename = f"{TASK_STORAGE_PATH}/{task_id}"
    try:
        with open(filename) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
# def load_task_result(task_id):
#     filename = f"{TASK_STORAGE_PATH}/celery-task-meta-{task_id}"
#     try:
#         with open(filename) as f:
#             return json.load(f)
#     except (FileNotFoundError, json.JSONDecodeError):
#         return None

def delete_task_result(task_id):
    filename = f"{TASK_STORAGE_PATH}/{task_id}.json"
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass