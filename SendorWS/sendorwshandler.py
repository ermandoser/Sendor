import tornado.websocket

clients = []

class WSHandler(tornado.websocket.WebSocketHandler):	
	global clients
		
	def open(self):
		print 'new connection'
		clients.append(self)
		
	def on_message(self, message):
		print 'message received %s' % message
			
	def on_close(self):
		print 'connection closed'
		clients.remove(self)
		
def notify_clients(task_state):
	print("Notifying: " + task_state)
	for client in clients:
		client.write_message("task_state")