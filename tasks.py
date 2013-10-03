
import os
import unittest
import time

import fabric.api

from fabric.api import local

from SendorQueue import SendorTask

class FabricTask(SendorTask):
    
    def fabric_local(self, command):
        with fabric.api.settings(warn_only = True):
            result = local(command, capture = True)
            self.append_details(command)
            self.append_details(result)
            self.append_details(result.stderr)
            if result.failed:
                raise Exception("Fabric command failed")

class CopyFileTask(FabricTask):

    def __init__(self, source, target):
        super(CopyFileTask, self).__init__()
        self.source = source
        self.target = target

    def run(self):
        self.fabric_local('cp ' + self.source + ' ' + self.target)

    def string_description(self):
        return "Copy file " + self.source + " to " + self.target

class UploadFileTask(SendorTask):

    def __init__(self, source):
        super(UploadFileTask, self).__init__()
        self.source = source

    def run(self):
        pass

    def string_description(self):
        return "Upload file " + self.source

class StashFileTask(SendorTask):

    def __init__(self, path, source, file_stash):
        super(StashFileTask, self).__init__()
        self.path = path
        self.source = source
        self.file_stash = file_stash
        self.stashed_file = None

    def run(self):
        self.stashed_file = self.file_stash.add(self.path, self.source)

    def string_description(self):
        return "Stash file " + self.source

    def get_file_func(self):

        def get_file():
            return self.stashed_file

        return get_file


class CopyStashedFileTask(FabricTask):

    def __init__(self, get_file, target):
        super(CopyStashedFileTask, self).__init__()
        self.get_file = get_file
        self.target = target

    def run(self):
        source_path = self.get_file().get_full_path()
        self.fabric_local('cp ' + source_path + ' ' + self.target)

    def string_description(self):
        return "Copy to " + self.target


class ScpStashedFileTask(FabricTask):

    def __init__(self, get_file, filename, target):
        super(ScpStashedFileTask, self).__init__()
        self.get_file = get_file
        self.filename = filename
        self.target = target

    def run(self):
        source_path = self.get_file().get_full_path()
        target_path = self.target['user'] + '@' + self.target['host'] + ":" + self.filename
        target_port = self.target['port']
        key_file = self.target['private_key_file']
        self.fabric_local('scp ' + ' -P ' + target_port + ' -i ' + key_file + ' ' + source_path + ' ' + target_path)

    def string_description(self):
        return "Distribute to " + self.target['user']

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
