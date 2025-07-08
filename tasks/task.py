from celery import shared_task
import subprocess
import os
import signal
import json
from celery.exceptions import Ignore

from celery_rabbitmq.custom_result import CustomAsyncResult
from celery.exceptions import TaskRevokedError

@shared_task(bind=True, acks_late=False)
def install_package(self, package_name):
    # Initialize metadata with serializable types only
    
    meta = {
        'status': 'STARTED',
        'message': f'Starting {package_name} installation',
        'output': [],
        'pid': None,
        'partial': True
    }
    self.update_state(state='PROGRESS', meta=meta)
    
    def preexec_function():
        os.setpgrp()  # Create new process group

    

    try:
        process = subprocess.Popen(
            ['ping', '10.0.0.1'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            preexec_fn=preexec_function
        )
        
        meta.update({
            'pid': process.pid,
            'pgid': os.getpgid(process.pid),
            'status': 'PROGRESS'
        })
        self.update_state(state='PROGRESS', meta=meta)

       
        
        while True:
            
            # task = CustomAsyncResult(self.request.id)
            # print(task.state,task.status)
            # print(meta['pgid'],"I am try")
            # if task.status=='REVOKED':  # Will be set by revoke()
            #     meta.update({
            #         'status': 'CANCELLED',
            #         'message': 'Installation cancelled by user',
            #         'output': meta['output'],
            #         'partial': False  # Mark as final state
            #     })
            #     self.update_state(state='CANCELLED', meta=meta)
                
            #     # Cleanup process
            #     try:
            #         print(meta['pgid'],"I am try")
            #         os.killpg(meta['pgid'], signal.SIGTERM)
            #     except ProcessLookupError:
            #         pass
                    
            #     return meta  # Preserve all cancellation data
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            if line:
                meta['output'].append(line.strip())
                meta['message'] = line.strip()
                self.update_state(state='PROGRESS', meta=meta)
        
        return {
            'status': 'SUCCESS',
            'package': package_name,
            'output': meta['output'],
            'message': f'{package_name} installed successfully',
            'partial': False
        }

    # except TaskRevokedError as e:
    #     print("KHJJJJJJJJJJJJJJJJJJJJJ")
    #     return {
    #         'status': 'FAILURE',
    #         'package': package_name,
    #         'message': str(e),
    #         'output': meta['output'],
    #         'partial': False
    #     }
        
    except Exception as e:
        return {
            'status': 'FAILURE',
            'package': package_name,
            'message': str(e),
            'output': meta['output'],
            'partial': False
        }