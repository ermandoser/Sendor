import os 

from flask import Flask
from flask import Blueprint, Response, redirect, url_for, render_template, request
from werkzeug import secure_filename

from FileDistribution.SendorQueue import SendorQueue, SendorJob
from FileDistribution.FileStash import FileStash
from FileDistribution.Targets import Targets
from FileDistribution.tasks import StashFileTask, DistributeFileTask

from Logger.logger import g_logger

g_sendor_queue = None
g_file_stash = None
g_targets = None

def create_ui(upload_folder, file_stash_folder, queue_folder, config_targets):
	global g_sendor_queue
	global g_file_stash
	global g_targets

	ui_app = Blueprint('ui', __name__)
	g_sendor_queue = SendorQueue(queue_folder)
	g_file_stash = FileStash(file_stash_folder)
	g_targets = Targets(config_targets)
	
	@ui_app.route('/')
	@ui_app.route('/index.html', methods = ['GET'])
	def index():
		file_stash = sorted(g_file_stash.files.values(), cmp = lambda x, y: cmp(x.timestamp, y.timestamp))
		latest_uploaded_file = None
		if len(file_stash) != 0:
			latest_uploaded_file = file_stash[-1].to_json()
        
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
                               file_stash = [latest_uploaded_file],
                               pending_jobs = pending_jobs,
                               current_job = current_job,
                               past_jobs = past_jobs)

	@ui_app.route('/login', methods=["GET", "POST"])
	def login():
		print("LoginIn")
		form = LoginForm(request.form)
		print("Form uname: " + str(form.username.data))
		if request.method == 'POST' and form.validate():
			print("Form validate")
			# login and validate the user...
			login_user(user)
			flash("Logged in successfully.")
			return redirect(request.args.get("next") or url_for("index"))
		print("Form not valid")
		return render_template("login.html", form=form)
							
	@ui_app.route('/file_stash.html', methods = ['GET'])
	def file_stash():
        
		file_stash = sorted(g_file_stash.files.values(), cmp = lambda x, y: cmp(x.timestamp, y.timestamp))
		file_stash_contents = []
		for file in file_stash:
			file_stash_contents.append(file.to_json())
        
		return render_template('file_stash.html',
                               file_stash = file_stash_contents)
    
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
				files[id] = file.to_json()
            
			return Response(render_template('distribute	_form.html',
                                            files = files,
                                            targets = g_targets.get_targets()))
        
		elif request.method == 'POST':
            
			target_ids = request.form.getlist('target')
			id = request.form.get('file')
			stashed_file = g_file_stash.get(id)
            
			distribute_file_tasks = []
			for id in target_ids:
				distribute_file_task = DistributeFileTask(stashed_file.original_filename, id)
				distribute_file_actions = g_targets.create_distribution_actions(distribute_file_task, stashed_file.full_path_filename, stashed_file.original_filename, id)
				distribute_file_task.actions.extend(distribute_file_actions)
				distribute_file_tasks.append(distribute_file_task)
            
			job = SendorJob(distribute_file_tasks)
			g_sendor_queue.add(job)
            
			return redirect('index.html')
    
	g_logger.info("Created ui")
    
	return ui_app
