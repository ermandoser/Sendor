
import json
import os
import unittest

from tasks import ScpStashedFileTask

targets = []

def load(config_filename):
    with open(config_filename) as file:
        global targets
        targets = json.load(file)

def create_distribution_tasks(get_file, filename, ids):
    tasks = []
    for id in ids:
        if not id in targets:
            raise Exception("id " + id + " does not exist in targets")
        else:
            target = targets[id]
            destination_file = filename
            task = ScpStashedFileTask(get_file, destination_file, target)
            tasks.append(task)

    return tasks


def get_targets():
    return targets


class test(unittest.TestCase):
    def setUp(self):
        load('remote_machine_targets.json')

    def test(self):
        
        class StashedFile(object):
            def get_full_path(self):
                return 'sourcedir/sourcefile'

        def get_file():
            return StashedFile()

        create_distribution_tasks(get_file, 'sourcefile', ['target2', 'target3'])

if __name__ == '__main__':
    unittest.main()
