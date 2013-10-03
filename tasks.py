
import json
import os
import shutil
import time
import unittest

import paramiko
import fabric.api
from fabric.api import local

from SendorQueue import SendorTask
from FileStash import FileStash, StashedFile

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

class SftpStashedFileTask(FabricTask):

    def __init__(self, get_file, filename, target):
        super(SftpStashedFileTask, self).__init__()
        self.get_file = get_file
        self.filename = filename
        self.target = target
        self.transferred = None

    def run(self):

        def cb(transferred, total):
            self.transferred = transferred
            self.total = total

        source_path = self.get_file().get_full_path()

        key_file = self.target['private_key_file']
        transport = paramiko.Transport((self.target['host'], int(self.target['port'])))
        transport.connect(username = self.target['user'], password = 'apa')
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(source_path, self.filename, callback=cb)

    def string_description(self):
        if self.transferred:
            ratio = int(100 * self.transferred / self.total)
            return "Distribute to " + self.target['user'] + " - " + str(ratio) + "% sent"
        else:
            return "Distribute to " + self.target['user']


class CopyFileTaskUnitTest(unittest.TestCase):

    def setUp(self):
        os.mkdir('unittest')
        local('echo abc123 > unittest/source')

    def test_copy_file_task(self):

        self.assertFalse(os.path.exists('unittest/target'))
        task = CopyFileTask('unittest/source', 'unittest/target')
        task.run()
        self.assertTrue(os.path.exists('unittest/target'))

    def tearDown(self):
        shutil.rmtree('unittest')

class SftpFileTaskUnitTest(unittest.TestCase):

    root_path = 'unittest'
    upload_root = root_path + '/upload'
    file_stash_root = root_path + '/FileStash'
    file_name = 'testfile'

    def setUp(self):
        os.mkdir(self.root_path)
        os.mkdir(self.upload_root)
        os.mkdir(self.file_stash_root)
        self.file_stash = FileStash(self.file_stash_root)

        local('echo abc123 > ' + os.path.join(self.upload_root, self.file_name))
        self.file = self.file_stash.add(self.upload_root, self.file_name)

    def test_copy_file_task(self):

        def get_file():
            return self.file_stash.get(self.file_name, self.file.sha1sum)

        targets = {}
        with open('remote_machine_targets.json') as file:
            targets = json.load(file)

        target = targets['target1']

        task = SftpStashedFileTask(get_file, self.file_name, target)
        task.run()

    def tearDown(self):
        shutil.rmtree(self.root_path)

if __name__ == '__main__':
    unittest.main()
