
from Queue import Queue
import thread
from fabric.api import local, settings
import os

class SendorJob:

    def __init__(self, tasks=[], started=None, completed=None):
        self.tasks = tasks
        self.started = started
        self.completed = completed

class SendorTask(object):

    def __init__(self, started=None, completed=None):
        self.started = started
        self.completed = completed

    def run(self):
        pass

class CopyFileTask(SendorTask):

    def __init__(self, source, target, started=None, completed=None):
        super(CopyFileTask, self).__init__(started, completed)
        self.source = source
        self.target = target

    def run(self):
        local('cp ' + self.source + ' ' + self.target)

class SendorQueue():

    def __init__(self):

        self.jobs = Queue()
        thread.start_new_thread((lambda sendor_queue: sendor_queue.job_worker_thread()), (self,))

    def job_worker_thread(self):
	while True:

            job = self.jobs.get()

            if job.started:
                job.started()

            for task in job.tasks:

                if task.started:
                    task.started()

                task.run()

                if task.completed:
                    task.completed()

            if job.completed:
                job.completed()

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
            def __init__(self):
                self.state = NOT_STARTED_JOB

        state = State()
        
        def started_job_func():
            self.assertEquals(state.state, NOT_STARTED_JOB)
            state.state = STARTED_JOB

        def completed_job_func():
            self.assertEquals(state.state, STARTED_JOB)
            state.state = COMPLETED_JOB

        job = SendorJob([],
                        started_job_func,
                        completed_job_func)

        self.sendor_queue.add(job)

        self.sendor_queue.wait()

        self.assertEquals(state.state, COMPLETED_JOB)

    def test_job_with_single_task(self):

        NOT_STARTED_JOB = 0
        STARTED_JOB = 1
        STARTED_TASK = 2
        COMPLETED_TASK = 3
        COMPLETED_JOB = 4

        class State:
            def __init__(self):
                self.state = NOT_STARTED_JOB

        state = State()
        
        def started_job_func():
            self.assertEquals(state.state, NOT_STARTED_JOB)
            state.state = STARTED_JOB

        def started_task_func():
            self.assertEquals(state.state, STARTED_JOB)
            state.state = STARTED_TASK

        def completed_task_func():
            self.assertEquals(state.state, STARTED_TASK)
            state.state = COMPLETED_TASK

        def completed_job_func():
            self.assertEquals(state.state, COMPLETED_TASK)
            state.state = COMPLETED_JOB

        class State:
            def __init__(self):
                self.state = NOT_STARTED_JOB

        state = State()

        task = SendorTask(started_task_func,
                          completed_task_func)

        job = SendorJob([task],
                        started_job_func,
                        completed_job_func)

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
