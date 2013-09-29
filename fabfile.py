
from fabric.api import local

def hello():
	print "Hello world!"

def ls():
	local('ls -l')

