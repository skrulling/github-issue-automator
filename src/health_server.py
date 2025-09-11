import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'GitHub Issue Automator is running')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default HTTP server logging
        pass

def start_health_server():
    """Start a simple HTTP server for health checks"""
    port = int(os.environ.get('PORT', 8080))
    
    try:
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        logger.info(f"Health check server starting on port {port}")
        
        # Run server in a separate thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        return server
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")
        return None