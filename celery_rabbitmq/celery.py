from celery import Celery
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celery_rabbitmq.settings')

app=Celery('celery_rabbitmq')

# RabbitMq configuration
app.conf.update(
    result_backend='celery_rabbitmq.custom_file_backend:OrganizedFilesystemBackend',
    result_backend_options={
        'url': '/var/mytasks',
    },
    result_extended=True,
    result_serializer='json',
    task_serializer='json',
    accept_content=['json'],
    result_persistent=True,
    task_track_started=True,
    task_ignore_result=False
)
app.conf.broker_url='amqp://hci:hci@123@localhost:5672/hcivhost'
# app.conf.result_backend = 'rpc://'  # Using RPC backend for results
# app.conf.result_backend='file:///var/celery_results'
# app.conf.update(
    
#     result_backend=f'file:///var/celery_results',
#      result_extended=True,
#     result_filename_template='{task_id}' ,
#     result_serializer='json',
#     task_serializer='json',
#     accept_content=['json'],)
# app.conf.result_persistent = True  # Persist results
# app.conf.task_track_started = True
# app.conf.task_ignore_result = False

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()