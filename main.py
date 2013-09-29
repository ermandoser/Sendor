
from flask import Flask
from flask import Blueprint, Response, redirect, url_for, render_template, request
from werkzeug import secure_filename
import logging
import sys
import os

from SendorQueue import SendorQueue, SendorJob, CopyFileTask, SendorTask

from LocalMachineDistributionJob import create_local_machine_distribution_job

logger = logging.getLogger('main')

UPLOAD_FOLDER = 'test/upload'

DISTRIBUTION_TARGETS = [
	'test/targetdir1',
	'test/targetdir2',
	'test/targetdir3'
]

g_sendor_queue = None

class UploadFileTask(SendorTask):

	def __init__(self):
		super(UploadFileTask, self).__init__()

	def run(self):
		pass

	def string_description(self):
		return "Upload file"

def create_ui():

	ui_app = Blueprint('ui', __name__)

	@ui_app.route('/')
	@ui_app.route('/index.html', methods = ['GET'])
	def index():
		jobs = []
		current_job = g_sendor_queue.current_job
		if current_job:
			jobs.append(current_job)
		jobs = jobs + list(g_sendor_queue.jobs.queue)
		jobs_html = ""

		for job in jobs:
			progress = job.visualize_progress()
			jobs_html = jobs_html + progress

		return render_template('index.html', jobs_html = jobs_html)

	@ui_app.route('/upload.html', methods = ['GET', 'POST'])
	def upload():
		if request.method == 'GET':
			return Response(render_template('upload_form.html'))
		elif request.method == 'POST':

			targets = DISTRIBUTION_TARGETS
			upload_file_task = UploadFileTask()

			file = request.files['file']
			filename = secure_filename(file.filename)
			upload_file_full_path = os.path.join(UPLOAD_FOLDER, filename)
			file.save(upload_file_full_path)

			job = create_local_machine_distribution_job(filename, upload_file_full_path, upload_file_task, targets)

			g_sendor_queue.add(job)

#			return redirect('index.html')
			return "Upload done"

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
