
from flask import Flask
from flask import Blueprint, Response, redirect, url_for, render_template, request
from werkzeug import secure_filename
import logging
import sys
import os

from SendorQueue import SendorQueue, SendorJob, CopyFileTask

logger = logging.getLogger('main')

UPLOAD_FOLDER = 'test/upload'

DISTRIBUTION_TARGETS = [
	'test/targetdir1',
	'test/targetdir2',
	'test/targetdir3'
]

g_sendor_queue = None

def create_distribution_job(filename):

	global g_sendor_queue
	
	tasks = []
	for target in DISTRIBUTION_TARGETS:
		tasks.append(CopyFileTask(UPLOAD_FOLDER + '/' + filename, target + '/' + filename))

	job = SendorJob(tasks)

	g_sendor_queue.add(job)

def create_ui():

	ui_app = Blueprint('ui', __name__)

	@ui_app.route('/')
	@ui_app.route('/index.html', methods = ['GET'])
	def index():
		return "bodybodybody"

	@ui_app.route('/upload.html', methods = ['GET', 'POST'])
	def upload():
		if request.method == 'GET':
			return Response(render_template('upload_form.html'))
		elif request.method == 'POST':
			file = request.files['file']
			filename = secure_filename(file.filename)
			file.save(os.path.join(UPLOAD_FOLDER, filename))
			create_distribution_job(filename)
			return "Upload complete"

	logger.info("Created ui")

	return ui_app

def main(host, port):
	global g_sendor_queue
	
	root = Flask(__name__)

	ui_app = create_ui()
	root.register_blueprint(url_prefix = '/ui', blueprint = ui_app)

	@root.route('/')
	@root.route('/index.html')
	def index():
		return redirect('ui')

	g_sendor_queue = SendorQueue()

	logger.info("Starting wsgi server")

	root.run(host = host, port = port, debug = True)


if __name__ == '__main__':
	
	if len(sys.argv) != 3:
		print "Usage: main.py <host> <port>"
	else:
		main(host = sys.argv[1], port = int(sys.argv[2]))
