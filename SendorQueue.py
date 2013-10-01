
import thread
import unittest

from Queue import Queue

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
                            'state' : task.string_state(),
                            'details' : task.string_details() })
            
        return status

    def visualize_progress(self):
        progress = self.progress()
        return render_template('SendorJob.html', tasks = progress)

class SendorTask(object):

    NOT_STARTED = 0
    STARTED = 1
    COMPLETED = 2
    FAILED = 3
    CANCELED = 4
    
    def __init__(self):
        self.state = self.NOT_STARTED
        self.details = ""

    def started(self):
        self.state = self.STARTED

    def completed(self):
        self.state = self.COMPLETED

    def failed(self):
        self.state = self.FAILED

    def canceled(self):
        self.state = self.CANCELED

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
        elif self.state == self.CANCELED:
            return 'canceled'
        else:
            raise Exception("Unknown state" + str(self.state))

    def string_details(self):
        return self.details

    def append_details(self, string):
        self.details = self.details + string


class SendorQueue():

    def __init__(self):

        self.pending_jobs = Queue()
        self.current_job = None
        self.past_jobs = Queue()
        thread.start_new_thread((lambda sendor_queue: sendor_queue.job_worker_thread()), (self,))

    def job_worker_thread(self):
	while True:

            job = self.pending_jobs.get()
            self.current_job_is_canceled = False
            self.current_job = job

            job.started()

            for task in job.tasks:

                if self.current_job_is_canceled:
                    task.canceled()
                else:
                    try:
                        task.started()
                        task.run()
                        task.completed()
                    except:
                        task.failed()
                        self.cancel_current_job()

            job.completed()

            self.current_job = None

            self.pending_jobs.task_done()

            self.past_jobs.put(job)

    def add(self, job):
        self.pending_jobs.put(job)

    def wait(self):
        self.pending_jobs.join()

    def cancel_current_job(self):
        self.current_job_is_canceled = True
        

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

if __name__ == '__main__':
    unittest.main()
