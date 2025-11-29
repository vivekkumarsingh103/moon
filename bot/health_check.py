from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Disable default logging
        pass

def start_health_server():
    """Start a simple health check server"""
    server = HTTPServer(('0.0.0.0', 8000), HealthHandler)
    logging.info("🩺 Health check server running on port 8000")
    server.serve_forever()

if __name__ == '__main__':
    start_health_server()
