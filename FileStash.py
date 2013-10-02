
import unittest
import os.path

from fabric.api import local

class StashedFile(object):

    def __init__(self, root_path, filename, sha1sum):
        self.root_path = root_path
        self.filename = filename
        self.sha1sum = sha1sum

        if len(sha1sum) != 40:
            raise Exception(sha1sum + " is not a valid SHA1 hash value")

    def get_full_path(self):
        return os.path.join(self.root_path, self.sha1sum + '/' + self.filename)

class FileStash(object):

    def __init__(self, root_path):
        self.root_path = root_path
        self.build_index()

    def build_index(self):
        self.files = {}
        
        for root, dirs, filenames in os.walk(self.root_path):
            for filename in filenames:
                sha1sum = root[-40:]
                file = StashedFile(self.root_path, filename, sha1sum)
                self.files[sha1sum] = file

    def get(self, sha1sum):
        return self.files.get(sha1sum)

    def add(self, original_path, filename):
        original_file = os.path.join(original_path, filename)
        
        sha1sum = local('sha1sum -b ' + original_file, capture = True)[:40]
        file = self.get(sha1sum)
        if file:
            return file
        else:

            file = StashedFile(self.root_path, filename, sha1sum)
            stashed_file = file.get_full_path()

            local('mkdir ' + os.path.join(self.root_path, sha1sum))
            local('cp "' + original_file + '" "' + stashed_file + '"')
            
            self.files[sha1sum] = file
            return file

class StashedFileUnitTest(unittest.TestCase):

    def test_file(self):

        self.assertRaises(Exception, StashedFile, "root/path", "myfilename", "invalid_hash")

        file = StashedFile("root/path", "myfilename", "cf53e64d1bb75ce5a4e71324777d7ed6cc19c435")
        self.assertEquals(file.get_full_path(), "root/path/cf53e64d1bb75ce5a4e71324777d7ed6cc19c435/myfilename")

class FileStashUnitTest(unittest.TestCase):

    file1_sha1sum = 'a2abbbf0d432a8097fd7a4d421cc91881309cda2'
    file2_sha1sum = 'dca028d53b41169f839eeefe489b02e0aa7b5d27'

    def setUp(self):
        local('mkdir unittest')
        local('mkdir unittest/file_stash')
        local('mkdir unittest/file_stash/' + self.file1_sha1sum)
        local('echo "Hello World 1" > unittest/file_stash/' + self.file1_sha1sum + '/hello1.txt')
        local('mkdir unittest/file_stash/' + self.file2_sha1sum)
        local('echo "Hello World 2" > unittest/file_stash/' + self.file2_sha1sum + '/hello2.txt')

        local('echo "Hello World 3" > unittest/hello3.txt')
        local('echo "Hello World 4" > unittest/hello1.txt')

    def test(self):

        file_stash = FileStash('unittest/file_stash')
        self.assertEquals(len(file_stash.files), 2)

        file3 = file_stash.add('unittest', 'hello3.txt')
        file4 = file_stash.add('unittest', 'hello1.txt')

        self.assertNotEquals(file_stash.get(self.file1_sha1sum), None)
        self.assertNotEquals(file_stash.get(self.file2_sha1sum), None)
        self.assertNotEquals(file_stash.get(file3.sha1sum), None)
        self.assertNotEquals(file_stash.get(file4.sha1sum), None)
        self.assertEquals(file_stash.get('12345678'), None)

    def tearDown(self):
        local('rm -rf unittest')

if __name__ == '__main__':
    unittest.main()
