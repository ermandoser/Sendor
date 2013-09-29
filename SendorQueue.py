
from Queue import Queue
import thread
import os

from fabric.api import local, settings

from flask import render_template

class SendorJob(object):

    def __init__(self, tasks=[]):
        self.tasks = tasks

    def started(self):
        pass

    def completed(self):
        pass

    def progress(self):
        status = []

        for task in self.tasks[0:]:
            status.append({ 'description' : task.string_description(),
                            'state' : task.string_state() })
            
        return status

    def visualize_progress(self):
        progress = self.progress()
        return render_template('SendorJob.html', tasks = progress)

class SendorTask(object):

    NOT_STARTED = 0
    STARTED = 1
    COMPLETED = 2
    FAILED = 3
    
    def __init__(self):
        self.state = self.NOT_STARTED

    def started(self):
        self.state = self.STARTED

    def completed(self):
        self.state = self.COMPLETED

    def failed(self):
        self.state = self.FAILED


    def run(self):
        pass

    def string_description(self):
        raise Exception("No description given")

    def string_state(self):
        if self.state == self.NOT_STARTED:
            return 'not_started'
        elif self.state == self.STARTED:
            return 'in_progress'
        elif self.state == self.COMPLETED:
            return 'completed'
        elif self.state == self.FAILED:
            return 'failed'
        else:
            raise Exception("Unknown state" + str(self.state))

class CopyFileTask(SendorTask):

    def __init__(self, source, target):
        super(CopyFileTask, self).__init__()
        self.source = source
        self.target = target

    def run(self):
        local('cp ' + self.source + ' ' + self.target)

    def string_description(self):
        return "Copy file " + self.source + " to " + self.target

class SendorQueue():

    def __init__(self):

        self.jobs = Queue()
        thread.start_new_thread((lambda sendor_queue: sendor_queue.job_worker_thread()), (self,))
        self.current_job = None

    def job_worker_thread(self):
	while True:

            job = self.jobs.get()
            self.current_job = job

            job.started()

            for task in job.tasks:

                task.started()
                try:
                    task.run()
                    task.completed()
                except:
                    task.failed()
                    raise

            job.completed()

            self.current_job = None

            self.jobs.task_done()


    def add(self, job):
        self.jobs.put(job)

    def wait(self):
        self.jobs.join()
        

import unittest

class SendorQueueUnitTest(unittest.TestCase):

    def setUp(self):
        self.sendor_queue = SendorQueue()

    def test_empty_job(self):

        NOT_STARTED_JOB = 0
        STARTED_JOB = 1
        COMPLETED_JOB = 2

        class State:
            def __init__(self, unittest):
                self.state = NOT_STARTED_JOB
                self.unittest = unittest

        state = State(self)
        
        class InstrumentedSendorJob(SendorJob):

            def started(self):
                state.unittest.assertEquals(state.state, NOT_STARTED_JOB)
                state.state = STARTED_JOB
                super(InstrumentedSendorJob, self).started()

            def completed(self):
                super(InstrumentedSendorJob, self).completed()
                state.unittest.assertEquals(state.state, STARTED_JOB)
                state.state = COMPLETED_JOB

        job = InstrumentedSendorJob([])
        self.sendor_queue.add(job)
        self.sendor_queue.wait()
        self.assertEquals(state.state, COMPLETED_JOB)

    def test_job_with_single_task(self):

        NOT_STARTED_JOB = 0
        STARTED_JOB = 1
        STARTED_TASK = 2
        COMPLETED_TASK = 3
        COMPLETED_JOB = 4

        class State(object):
            def __init__(self, unittest):
                self.state = NOT_STARTED_JOB
                self.unittest = unittest

        state = State(self)

        class InstrumentedSendorJob(SendorJob):

            def started(self):
                state.unittest.assertEquals(state.state, NOT_STARTED_JOB)
                state.state = STARTED_JOB
                super(InstrumentedSendorJob, self).started()

            def completed(self):
                super(InstrumentedSendorJob, self).completed()
                state.unittest.assertEquals(state.state, COMPLETED_TASK)
                state.state = COMPLETED_JOB

        class InstrumentedSendorTask(SendorTask):
            
            def started(self):
                state.unittest.assertEquals(state.state, STARTED_JOB)
                state.state = STARTED_TASK
                super(InstrumentedSendorTask, self).started()

            def completed(self):
                super(InstrumentedSendorTask, self).completed()
                state.unittest.assertEquals(state.state, STARTED_TASK)
                state.state = COMPLETED_TASK
        
        task = InstrumentedSendorTask()
        job = InstrumentedSendorJob([task])
        self.sendor_queue.add(job)
        self.sendor_queue.wait()
        self.assertEquals(state.state, COMPLETED_JOB)

class CopyFileTaskUnitTest(unittest.TestCase):

    def setUp(self):
        local('mkdir unittest')
        local('echo abc123 > unittest/source')

    def test_copy_file_task(self):

        self.assertFalse(os.path.exists('unittest/target'))
        task = CopyFileTask('unittest/source', 'unittest/target')
        task.run()
        self.assertTrue(os.path.exists('unittest/target'))

    def tearDown(self):
        local('rm -rf unittest')

if __name__ == '__main__':
    unittest.main()
