
import os
import os.path
import shutil
import unittest

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
        if not os.path.exists(root_path):
            raise Exception("Stash directory " + root_path + " does not exist")
        self.root_path = root_path
        self.build_index()

    def build_index(self):
        """ Create an index for all the files in the stash directory tree """
        self.files = {}
        
        for root, dirs, filenames in os.walk(self.root_path):
            for filename in filenames:
                sha1sum = root[-40:]
                self.add_to_index(filename, sha1sum)

    def add_to_index(self, filename, sha1sum):
        """ Add a new file to the index
            The file should not yet exist in the index
            The file should be present in the stash directory tree
            """
        file = StashedFile(self.root_path, filename, sha1sum)
        self.files[sha1sum + ' ' + filename] = file
        return file

    def remove_from_index(self, filename, sha1sum):
        """ Remove a file from the index
            The file should exist in the index
            The file will not be removed from the stash directory tree
            """
        del self.files[sha1sum + ' ' + filename]

    def get(self, filename, sha1sum):
        """ Locate the index entry for a file, or return None if it does not exist """
        return self.files.get(sha1sum + ' ' + filename)

    def add(self, original_path, filename):
        """ Add a file to the stash
            If the file already exists in the stash, this operation returns the stashed file
            Otherwise, the file will be copied into the stash directory tree, and added to the index, and the stashed file is returned
            """
        original_file = os.path.join(original_path, filename)
        
        sha1sum = local('sha1sum -b ' + original_file, capture = True)[:40]
        file = self.get(filename, sha1sum)
        if file:
            return file
        else:

            file = self.add_to_index(filename, sha1sum)
            stashed_file = file.get_full_path()

            if not os.path.exists(os.path.join(self.root_path, sha1sum)):
                os.mkdir(os.path.join(self.root_path, sha1sum))

            shutil.copy2(original_file, stashed_file)
            return file

    def remove(self, filename, sha1sum):
        """ Remove a file from the stash
            The file should exist in the index and stash directory tree
            The file will be removed from the index and stash directory tree
            """

        file = self.get(filename, sha1sum)
        stashed_file = file.get_full_path()
        self.remove_from_index(filename, sha1sum)
        os.remove(stashed_file)

    def nuke(self):
        """ Erase all files from stash """
        shutil.rmtree(self.root_path)
        os.mkdir(self.root_path)
        self.build_index()

class StashedFileUnitTest(unittest.TestCase):

    def test_file(self):

        self.assertRaises(Exception, StashedFile, "root/path", "myfilename", "invalid_hash")

        file = StashedFile("root/path", "myfilename", "cf53e64d1bb75ce5a4e71324777d7ed6cc19c435")
        self.assertEquals(file.get_full_path(), "root/path/cf53e64d1bb75ce5a4e71324777d7ed6cc19c435/myfilename")

class FileStashUnitTest(unittest.TestCase):

    file1_name = 'hello1.txt'
    file1_sha1sum = 'a2abbbf0d432a8097fd7a4d421cc91881309cda2'
    file2_name = 'hello2.txt'
    file2_sha1sum = 'dca028d53b41169f839eeefe489b02e0aa7b5d27'
    file3_name = 'hello3.txt'
    file3_sha1sum = 'ca44a076d1ac49f10ebb55949a9a16805af69bcd'
    file4_name = 'hello1.txt'
    file4_sha1sum = '77b8b233f03f1720c0642f6e1ce395fbfe0322ed'
    file5_name = 'hello5.txt'
    file5_sha1sum = 'ca44a076d1ac49f10ebb55949a9a16805af69bcd'

    def setUp(self):

        # Construct a file-stash
        os.mkdir('unittest')
        os.mkdir('unittest/file_stash')

    def test(self):

        # Add two files to the stash
        file_stash_init = FileStash('unittest/file_stash')
        local('echo "Hello World 1" > unittest/' + self.file1_name)
        local('echo "Hello World 2" > unittest/' + self.file2_name)
        file_stash_init.add('unittest', self.file1_name)
        file_stash_init.add('unittest', self.file2_name)
        os.remove('unittest/' + self.file1_name)
        os.remove('unittest/' + self.file2_name)

        # Create three temporary files outside of the stash
        local('echo "Hello World 3" > unittest/' + self.file3_name)
        local('echo "Hello World 4" > unittest/' + self.file4_name)
        local('echo "Hello World 3" > unittest/' + self.file5_name)

        file_stash = FileStash('unittest/file_stash')
        # file1 and file2 should already exist in the file stash
        self.assertEquals(len(file_stash.files), 2)

        # Files not in the stash should not yield any hits
        self.assertEquals(file_stash.get('12345678', '12345678'), None)

        # file4 has the same filename as file1
        # file3 and file5 have different names but identical content

        file_stash.add('unittest', self.file3_name)
        file_stash.add('unittest', self.file4_name)
        file_stash.add('unittest', self.file5_name)

        # Validate that all files have been added to the stash
        self.assertNotEquals(file_stash.get(self.file1_name, self.file1_sha1sum), None)
        self.assertNotEquals(file_stash.get(self.file2_name, self.file2_sha1sum), None)
        self.assertNotEquals(file_stash.get(self.file3_name, self.file3_sha1sum), None)
        self.assertNotEquals(file_stash.get(self.file4_name, self.file4_sha1sum), None)
        self.assertNotEquals(file_stash.get(self.file5_name, self.file5_sha1sum), None)

        # There should be 5 files in the stash both before and after re-indexing
        self.assertEquals(len(file_stash.files), 5)
        file_stash.build_index()
        self.assertEquals(len(file_stash.files), 5)

        # Remove two files with identical content
        file_stash.remove(self.file3_name, self.file3_sha1sum)
        self.assertEquals(file_stash.get(self.file3_name, self.file3_sha1sum), None)
        self.assertNotEquals(file_stash.get(self.file5_name, self.file5_sha1sum), None)
        file_stash.remove(self.file5_name, self.file5_sha1sum)
        self.assertEquals(file_stash.get(self.file3_name, self.file3_sha1sum), None)
        self.assertEquals(file_stash.get(self.file5_name, self.file5_sha1sum), None)

        # Remove one file which has identical name to another file 
        file_stash.remove(self.file4_name, self.file4_sha1sum)
        self.assertEquals(file_stash.get(self.file4_name, self.file4_sha1sum), None)
        self.assertNotEquals(file_stash.get(self.file1_name, self.file1_sha1sum), None)

        # At this point, only the first two files should remain in the stash
        file_stash.build_index()
        self.assertEquals(len(file_stash.files), 2)
        self.assertNotEquals(file_stash.get(self.file1_name, self.file1_sha1sum), None)
        self.assertNotEquals(file_stash.get(self.file2_name, self.file2_sha1sum), None)

        # Remove all files from stash
        file_stash.nuke()
        self.assertEquals(len(file_stash.files), 0)

    def tearDown(self):
        shutil.rmtree('unittest')

if __name__ == '__main__':
    unittest.main()
