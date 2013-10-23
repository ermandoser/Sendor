
import json

from flask import Flask, redirect
from Sendor.views import create_ui
from Sendor.Logger.logger import initialize_logger
from fabric.api import local

g_config = {}

def load_config(host_config_filename, targets_config_filename):
	global g_config
	with open(host_config_filename) as file:
		g_config = json.load(file)
	with open(targets_config_filename) as file:
		g_config['targets'] = json.load(file)
		
load_config('Sendor/configfiles/host_config.json', 'Sendor/configfiles/ssh_remote_targets.json')

initialize_logger(g_config['logging'])
	
host = g_config['host']
port = int(g_config['port'])
upload_folder = g_config['upload_folder']
file_stash_folder = g_config['file_stash_folder']
queue_folder = g_config['queue_folder']
config_targets = g_config['targets']
	
root = Flask(__name__)

ui_app = create_ui(upload_folder, file_stash_folder, queue_folder, config_targets)
root.register_blueprint(url_prefix = '/ui', blueprint = ui_app)

@root.route('/')
@root.route('/index.html')
def index():
	return redirect('ui')

#g_logger.info("Starting wsgi server")
