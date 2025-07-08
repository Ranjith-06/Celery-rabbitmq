from django.contrib import admin
from django.urls import path
from tasks.views import CancelTaskAPI, InstallPackageAPI, TaskStatusAPI


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/install/', InstallPackageAPI.as_view(), name='install-package'),
    path('api/tasks/<str:task_id>/', TaskStatusAPI.as_view(), name='task-status'),
    path('api/tasks/<str:task_id>/cancel/', CancelTaskAPI.as_view(), name='cancel-task'),
]