from celery import shared_task
import subprocess
import os
import signal
from .storage import save_task_result, load_task_result
from celery.exceptions import Ignore,SoftTimeLimitExceeded

@shared_task(bind=True)
def install_package(self, package_name):
    # Initialize metadata
    meta = {
        'status': 'STARTED',
        'message': f'Starting {package_name} installation',
        'output': [],
        'pid': None,
        'partial': True,
        'task_id': self.request.id  # Include task ID in metadata
    }
    save_task_result(self.request.id, meta)
    
    def preexec_function():
        os.setpgrp()  # Create new process group

    try:
        process = subprocess.Popen(
            # ['ping', '10.0.0.1'],
            ['sudo','apt','update'],
            # ['sudo', 'apt','install','postgresql'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            preexec_fn=preexec_function
        )
        
        # Update metadata
        meta.update({
            'pid': process.pid,
            'pgid': os.getpgid(process.pid),
            'status': 'PROGRESS'
        })
        save_task_result(self.request.id, meta)
        
        # Process output
        while True:
            # if ['is_aborted','request'] in self or   self.request.called_directly:
            #     if self.is_aborted():
            #         meta.update({
            #             'status': 'CANCELLED',
            #             'message': 'Task cancelled by user',
            #             'partial': False
            #         })
            #         save_task_result(self.request.id, meta)
            #         os.killpg(meta['pgid'], signal.SIGTERM)
            #         raise Ignore()
            
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            if line:
                meta['output'].append(line.strip())
                meta['message'] = line.strip()
                save_task_result(self.request.id, meta)
        
        # Success case
        result = {
            'status': 'SUCCESS',
            'package': package_name,
            'output': meta['output'],
            'message': f'{package_name} operation completed',
            'partial': False
        }
        save_task_result(self.request.id, result)
        return result

    except SoftTimeLimitExceeded:
        error_result = {
            'status': 'FAILURE',
            'package': package_name,
            'message': str(e),
            'output': meta['output'],
            'partial': False
        }
        save_task_result(self.request.id, error_result)
        
        raise
        
    except Exception as e:
        error_result = {
            'status': 'FAILURE',
            'package': package_name,
            'message': str(e),
            'output': meta['output'],
            'partial': False
        }
        save_task_result(self.request.id, error_result)
        return error_result