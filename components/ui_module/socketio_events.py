# components/ui_module/socketio_events.py
from app import socketio
from datetime import datetime

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def send_update(data):
    socketio.emit('update', data)

def send_alert(message):
    socketio.emit('alert', {'message': message})

def send_data_status(status, last_update):
    socketio.emit('data_status', {
        'status': status,
        'last_update': last_update
    })
    
def send_data_update(status):
    socketio.emit('data_update', {
        'status': status,
        'timestamp': datetime.now().isoformat()
    })