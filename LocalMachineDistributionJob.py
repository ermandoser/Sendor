
from SendorQueue import SendorJob, CopyFileTask
import os
import time

from flask import render_template

class LocalMachineDistributionJob(SendorJob):

    def __init__(self, tasks=[], started=None, completed=None):
        super(LocalMachineDistributionJob, self).__init__(tasks, started, completed)

    def progress(self):

        status = []

        for task in self.tasks[0:]:
            status.append({ 'description' : task.string_description(),
                            'state' : task.string_state() })
            
        return status

    def visualize_progress(self):
        progress = self.progress()
        return render_template('LocalMachineDistributionJob.html',
                               tasks = progress)

class CopyFileTaskWithProgress(CopyFileTask):

    NOT_STARTED = 0
    STARTED = 1
    COMPLETED = 2
    FAILED = 3
    
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

    def string_description(self):
        return "Copy file " + self.source + " to " + self.target

    def string_state(self):
        if self.state == self.NOT_STARTED:
            return 'not_started'
        elif self.state == self.STARTED:
            return 'in_progress'
        elif self.state == self.COMPLETED:
            return 'done'
        else:
            return 'unknown'


def create_local_machine_distribution_job(filename, upload_file_full_path, upload_file_task, targets):

    tasks = [upload_file_task]

    for target in targets:
        task = CopyFileTaskWithProgress(source = upload_file_full_path,
                            target = os.path.join(target, filename))
        tasks.append(task)

    job = LocalMachineDistributionJob(tasks)

    return job
