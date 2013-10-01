
from flask import Flask
from flask import Blueprint, Response, redirect, url_for, render_template, request
from werkzeug import secure_filename
import logging
import sys
import os

from SendorQueue import SendorQueue, SendorJob

from tasks import CopyFileTask, UploadFileTask

import LocalMachineTargets

logger = logging.getLogger('main')

UPLOAD_FOLDER = 'test/upload'

g_sendor_queue = None

def create_ui():

	ui_app = Blueprint('ui', __name__)

	@ui_app.route('/')
	@ui_app.route('/index.html', methods = ['GET'])
	def index():
		pending_jobs = []
		for job in reversed(list(g_sendor_queue.pending_jobs.queue)):
			pending_jobs.append(job.progress())

		current_job = None
		if g_sendor_queue.current_job:
			current_job = g_sendor_queue.current_job.progress()

		past_jobs = []
		for job in reversed(list(g_sendor_queue.past_jobs.queue)):
			past_jobs.append(job.progress())

		return render_template('index.html',
				       pending_jobs = pending_jobs,
				       current_job = current_job,
				       past_jobs = past_jobs)

	@ui_app.route('/cancel.html', methods = ['GET'])
	def cancel():
		g_sendor_queue.cancel_current_job()
		return redirect('index.html')

	@ui_app.route('/upload.html', methods = ['GET', 'POST'])
	def upload():
		if request.method == 'GET':
			return Response(render_template('upload_form.html',
							targets = LocalMachineTargets.get_targets()))
		elif request.method == 'POST':

			target_ids = request.form.getlist('target')
			file = request.files['file']
			filename = secure_filename(file.filename)
			upload_file_full_path = os.path.join(UPLOAD_FOLDER, filename)
			file.save(upload_file_full_path)

			upload_file_task = UploadFileTask(filename)
			distribute_file_tasks = LocalMachineTargets.create_distribution_tasks(filename, upload_file_full_path, target_ids)
			job = SendorJob([upload_file_task] + distribute_file_tasks)

			g_sendor_queue.add(job)

			return redirect('index.html')

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

	LocalMachineTargets.load('local_machine_targets.json')

	root.run(host = host, port = port, debug = True)


if __name__ == '__main__':
	
	if len(sys.argv) != 3:
		print "Usage: main.py <host> <port>"
	else:
		main(host = sys.argv[1], port = int(sys.argv[2]))
