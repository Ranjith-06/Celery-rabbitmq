# custom_result.py
from celery.result import AsyncResult
from celery_rabbitmq.custom_file_backend import OrganizedFilesystemBackend
from .celery import app as celery_app

class CustomAsyncResult(AsyncResult):
    def __init__(self, task_id, app=None):
        
        app = app or celery_app
        super().__init__(task_id, app=app)
        self.custom_backend = app.backend

    @property
    def state(self):
        # Check custom backend first
        custom_result = self.custom_backend.get_task_result(self.id)
        if custom_result:
            return custom_result.get('status', super().state)
        return super().state

    @property
    def status(self):
        # Check custom backend first
        custom_result = self.custom_backend.get_task_result(self.id)
        if custom_result:
            return custom_result.get('status', super().status)
        return super().status

    @property
    def result(self):
        # Check custom backend first
        custom_result = self.custom_backend.get_task_result(self.id)
        if custom_result:
            return custom_result
        return super().result

    
        