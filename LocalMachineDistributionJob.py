
import os
import time

from SendorQueue import SendorJob
from tasks import CopyFileTask

class DelayedCopyFileTask(CopyFileTask):

    def __init__(self, source, target):
        super(DelayedCopyFileTask, self).__init__(source, target)

    def run(self):
        time.sleep(5)
        super(DelayedCopyFileTask, self).run()
        time.sleep(5)

def create_local_machine_distribution_job(filename, upload_file_full_path, upload_file_task, targets):

    tasks = [upload_file_task]

    for target in targets:
        task = DelayedCopyFileTask(source = upload_file_full_path,
                            target = os.path.join(target, filename))
        tasks.append(task)

    job = SendorJob(tasks)

    return job
