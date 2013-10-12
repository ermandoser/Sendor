
import json
import os
import shutil
import time
import unittest

import paramiko
import fabric.api
from fabric.api import local

from SendorQueue import SendorTask
from FileStash import FileStash

class StashFileTask(SendorTask):

    def __init__(self, path, source, file_stash):
        super(StashFileTask, self).__init__()
        self.path = path
        self.source = source
        self.file_stash = file_stash

    def run(self):
        self.file_stash.add(self.path, self.source)

    def string_description(self):
        return "Add file " + self.source + " to stash"

class DistributeFileTask(SendorTask):

    def __init__(self, source, target):
        super(DistributeFileTask, self).__init__()
        self.source = source
        self.target = target

    def string_description(self):
        return "Distribute file " + self.source + " to " + self.target
