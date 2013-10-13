
import datetime

from SendorQueue import SendorTask

class StashFileTask(SendorTask):

    def __init__(self, path, source, file_stash):
        super(StashFileTask, self).__init__()
        self.path = path
        self.source = source
        self.file_stash = file_stash

    def run(self):
        self.file_stash.add(self.path, self.source, datetime.datetime.utcnow())

    def string_description(self):
        return "Add file " + self.source + " to stash"

class DistributeFileTask(SendorTask):

    def __init__(self, source, target):
        super(DistributeFileTask, self).__init__()
        self.source = source
        self.target = target

    def string_description(self):
        return "Distribute file " + self.source + " to " + self.target
