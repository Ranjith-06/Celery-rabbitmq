from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from celery_rabbitmq.custom_result import CustomAsyncResult
from .task import install_package
from celery.result import AsyncResult



class InstallPackageAPI(APIView):
    def post(self, request):
        package_name = request.data.get('package_name', 'nginx')
        task = install_package.delay(package_name)
        return Response({
            'task_id': task.id,
            'status': 'Job started',
            'package': package_name
        }, status=status.HTTP_202_ACCEPTED)
        
class TaskStatusAPI(APIView):
    def get(self, request, task_id):
        
        task_data = CustomAsyncResult(task_id)
        print(task_data.state)
        response_data = {
            'task_id': task_id,
            'status': task_data.state,
        }
        print(task_data.result,'????????????????????')
        if task_data.state == 'PROGRESS':
            response_data.update(task_data.result)
        elif task_data.state == 'SUCCESS':
            response_data.update(task_data.result)
        elif task_data.state == 'FAILURE':
            response_data.update(task_data.result)
        elif task_data.state == 'CANCELLED':
            response_data.update(task_data.result)
            response_data['message'] = (task_data.result['message'])
        elif task_data.state == 'REVOKED':
            response_data.update(task_data.result)  
        # print(response_data)
        return Response(response_data)
        
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult
from kombu.exceptions import EncodeError
import json,os,signal
from celery.exceptions import InvalidTaskError


class CancelTaskAPI(APIView):
    def post(self, request, task_id):
        try:
            task = CustomAsyncResult(task_id)
            current_result = task.result
            
            if not current_result:
                return Response({
                    'task_id': task_id,
                    'status': 'ERROR',
                    'message': 'No task result found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if task.state in ('PROGRESS', 'STARTED'):
                # Prepare cancellation data
                current_result['result'].update({
                        'status': 'CANCELLED',
                        'message': 'Cancelled by user request',
                        'partial': True
                    })
                
                try:
                    task.backend._store_result(
                        task_id=task_id,
                        result=current_result['result'],
                        state='REVOKED'
                    )
                except Exception as e:
                    print(f"Failed to store cancellation result: {str(e)}")
                    return Response({
                        'task_id': task_id,
                        'status': 'ERROR',
                        'message': f'Failed to store cancellation: {str(e)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # Terminate process group if exists
                if 'pgid' in current_result:
                    try:
                        os.killpg(current_result['pgid'], signal.SIGTERM)
                    except ProcessLookupError:
                        pass  # Process already dead

                # Revoke the task
                try:
                    task.revoke(terminate=True,signal='SIGTERM')
                except Exception as e:
                    print(f"Task revoke failed: {str(e)}")

                return Response({
                    'task_id': task_id,
                    'status': 'CANCELLED',
                    'message': 'Task cancellation completed',
                    'existing_data': {**current_result}
                }, status=status.HTTP_200_OK)

                
            elif task.state == 'SUCCESS':
                task.result.update({
                        'status': 'CANCELLED',
                        'message': 'Cancelled by user request',
                        'partial': True
                    })
                print(task.result,"LLLLLLLLLLLLLLLLLLLLLLLLL")
                return Response({
                    'task_id': task_id,
                    'status': task.state,
                    'result': task.result,
                    'message': 'Task already completed successfully'
                }, status=status.HTTP_200_OK)
                
            elif task.state in ('FAILURE', 'REVOKED', 'CANCELLED'):
                
                return Response({
                    'task_id': task_id,
                    'status': task.state,
                    'result': task.result,
                    'message': f'Task is already in {task.state} state'
                }, status=status.HTTP_200_OK)
                
            else:
                return Response({
                    'task_id': task_id,
                    'status': task.state,
                    'message': 'Task in unexpected state'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except InvalidTaskError:
            return Response({'error': 'Invalid task ID'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from .storage import load_task_result,delete_task_result,save_task_result
class CancelTaskAPIOld(APIView):
    
    def post(self, request, task_id):
        try:
            task_data = load_task_result(task_id)
            if not task_data:
                return Response(
                    {'error': 'Task not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if task_data['result']['status'] in ('STARTED', 'PROGRESS'):
                # Update task status to cancelled
                task_data['result'].update({
                    'status': 'CANCELLED',
                    'message': 'Cancelled by user',
                    'partial': False
                })
                save_task_result(task_id, task_data['result'])
                
                # Try to kill the process if possible
                if 'pgid' in task_data['result']:
                    try:
                        os.killpg(task_data['result']['pgid'], signal.SIGTERM)
                        
                    except ProcessLookupError:
                        pass
                
                return Response({
                    'task_id': task_id,
                    'status': 'CANCELLED',
                    'result': task_data['result']
                })
            
            return Response({
                'task_id': task_id,
                'status': task_data['result']['status'],
                'message': f'Task already in {task_data["result"]["status"]} state'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except EncodeError:
            return Response({
                'error': 'Task result serialization error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)