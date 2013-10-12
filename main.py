
import json
import logging
import sys
import os

from flask import Flask
from flask import Blueprint, Response, redirect, url_for, render_template, request
from werkzeug import secure_filename

from SendorQueue import SendorQueue, SendorJob
from FileStash import FileStash
from Targets import Targets

from tasks import StashFileTask, DistributeFileTask

logger = logging.getLogger('main')

g_sendor_queue = None

g_file_stash = None
g_targets = None

g_config = {}

def create_ui(upload_folder):

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
			return Response(render_template('upload_form.html'))

		elif request.method == 'POST':

			file = request.files['file']
			filename = secure_filename(file.filename)
			upload_file_full_path = os.path.join(upload_folder, filename)
			file.save(upload_file_full_path)

			stash_file_task = StashFileTask(upload_folder, filename, g_file_stash)
			job = SendorJob([stash_file_task])

			g_sendor_queue.add(job)

			return redirect('index.html')

	@ui_app.route('/distribute.html', methods = ['GET', 'POST'])
	def distribute():
		if request.method == 'GET':
			files = {}
			for id, file in g_file_stash.files.items():
				files[id] = {
					'name' : file.filename,
				}
		
			return Response(render_template('distribute_form.html',
							files = files,
							targets = g_targets.get_targets()))

		elif request.method == 'POST':

			target_ids = request.form.getlist('target')
			file = request.form.get('file')
			stashed_file = g_file_stash.files[file] 

			distribute_file_tasks = []
			for id in target_ids:
				distribute_file_task = DistributeFileTask(stashed_file.filename, id)
				distribute_file_action = g_targets.create_distribution_action(distribute_file_task, stashed_file.get_full_path(), stashed_file.filename, id)
				distribute_file_task.actions.append(distribute_file_action)
				distribute_file_tasks.append(distribute_file_task)

			job = SendorJob(distribute_file_tasks)
			g_sendor_queue.add(job)

			return redirect('index.html')

	logger.info("Created ui")

	return ui_app

def load_config(host_config_filename, targets_config_filename):
	global g_config
	with open(host_config_filename) as file:
		g_config = json.load(file)
	with open(targets_config_filename) as file:
		g_config['targets'] = json.load(file)

def main(host_config_filename, targets_config_filename):
	global g_sendor_queue
	global g_file_stash
	global g_targets

	load_config(host_config_filename, targets_config_filename)
	
	host = g_config['host']
	port = int(g_config['port'])
	upload_folder = g_config['upload_folder']
	file_stash_folder = g_config['file_stash_folder']
	
	root = Flask(__name__)

	ui_app = create_ui(upload_folder)
	root.register_blueprint(url_prefix = '/ui', blueprint = ui_app)

	@root.route('/')
	@root.route('/index.html')
	def index():
		return redirect('ui')

	g_sendor_queue = SendorQueue()
	g_file_stash = FileStash(file_stash_folder)
	g_targets = Targets(g_config['targets'])

	logger.info("Starting wsgi server")


	root.run(host = host, port = port, debug = True)


if __name__ == '__main__':
	
	if len(sys.argv) != 3:
		print "Usage: main.py <host config> <targets config>"
	else:
		main(host_config_filename = sys.argv[1], targets_config_filename = sys.argv[2])
