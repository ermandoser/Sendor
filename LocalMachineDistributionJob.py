
from SendorQueue import SendorJob, CopyFileTask
import os
import time

from flask import render_template

class LocalMachineDistributionJob(SendorJob):

    def __init__(self, tasks=[], started=None, completed=None):
        super(LocalMachineDistributionJob, self).__init__(tasks, started, completed)

    def progress(self):

        status = { 'upload_done' : True,
                   'distributions_done' : [] }

        for task in self.tasks[1:]:
            status['distributions_done'].append({ 'name' : task.target,
                                                'done' : task.done() })
            
        return status

    def visualize_progress(self):
        progress = self.progress()
        return render_template('LocalMachineDistributionJob.html',
                               upload_done = progress['upload_done'],
                               distributions_done = progress['distributions_done'])

class CopyFileTaskWithProgress(CopyFileTask):

    NOT_STARTED = 0
    STARTED = 1
    COMPLETED = 2
    
    def __init__(self, source, target):
        self.state = self.NOT_STARTED

        def started():
            self.state = self.STARTED

        def completed():
            self.state = self.COMPLETED

        super(CopyFileTaskWithProgress, self).__init__(source, target, started, completed)

    def run(self):
        time.sleep(5)
        super(CopyFileTaskWithProgress, self).run()
        time.sleep(5)

    def done(self):
        return self.state == self.COMPLETED


def create_local_machine_distribution_job(filename, upload_file_full_path, upload_file_task, targets):

    tasks = [upload_file_task]

    for target in targets:
        task = CopyFileTaskWithProgress(source = upload_file_full_path,
                            target = os.path.join(target, filename))
        tasks.append(task)

    job = LocalMachineDistributionJob(tasks)

    return job
