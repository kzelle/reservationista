#!/usr/bin/env python3

import http.server
import socketserver
import json
import os
from urllib.parse import parse_qs, urlparse
from http import HTTPStatus

# Constants
PORT = 8000
HOST = "localhost"

class MessageHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for processing messages in our Git-backed messaging application"""

    def _send_response(self, status_code, content_type, response_data):
        """Helper method to send HTTP responses"""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')  # Enable CORS for development
        self.end_headers()
        
        if response_data:
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def do_GET(self):
        """Handle GET requests
        
        Routes:
        / - Serve the main page
        /messages - Get all messages
        /messages/{id} - Get a specific message
        """
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/':
            # Serve the main page
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        
        elif path == '/messages':
            # TODO: Implement message retrieval from SQLite/Git
            messages = [
                {"id": 1, "content": "Test message", "timestamp": "2025-01-07T15:33:08-05:00"}
            ]
            self._send_response(HTTPStatus.OK, 'application/json', messages)
            
        else:
            self._send_response(
                HTTPStatus.NOT_FOUND,
                'application/json',
                {"error": "Route not found"}
            )

    def do_POST(self):
        """Handle POST requests
        
        Routes:
        /messages - Create a new message
        """
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/messages':
            # Get the length of the POST data
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read and parse the POST data
            post_data = self.rfile.read(content_length)
            try:
                message_data = json.loads(post_data.decode('utf-8'))
                
                # TODO: Implement message storage in SQLite/Git
                response_data = {
                    "status": "success",
                    "message": "Message received",
                    "data": message_data
                }
                self._send_response(HTTPStatus.CREATED, 'application/json', response_data)
                
            except json.JSONDecodeError:
                self._send_response(
                    HTTPStatus.BAD_REQUEST,
                    'application/json',
                    {"error": "Invalid JSON data"}
                )
        else:
            self._send_response(
                HTTPStatus.NOT_FOUND,
                'application/json',
                {"error": "Route not found"}
            )

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server():
    """Start the HTTP server"""
    with socketserver.TCPServer((HOST, PORT), MessageHandler) as httpd:
        print(f"Server started at http://{HOST}:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.server_close()

if __name__ == "__main__":
    # Ensure we serve files from the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_server()
