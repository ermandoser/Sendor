
from flask import Flask
from flask import Blueprint, Response, redirect, url_for
import logging
import sys

logger = logging.getLogger('main')


def create_ui():

	ui_app = Blueprint('ui', __name__)

	@ui_app.route('/')
	@ui_app.route('/index.html', methods = ['GET'])
	def index():
		return "bodybodybody"

	logger.info("Created ui")

	return ui_app

def main(host, port):
	
	root = Flask(__name__)

	ui_app = create_ui()
	root.register_blueprint(url_prefix = '/ui', blueprint = ui_app)

	@root.route('/')
	@root.route('/index.html')
	def index():
		return redirect('ui')

	logger.info("Starting wsgi server")

	root.run(host = host, port = port, debug = True)


if __name__ == '__main__':
	
	if len(sys.argv) != 3:
		print "Usage: main.py <host> <port>"
	else:
		main(host = sys.argv[1], port = int(sys.argv[2]))
