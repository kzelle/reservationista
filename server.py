#!/usr/bin/env python3

import json
import os
import asyncio
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from database.db import Database
from github_manager import GitHubManager

load_dotenv()

# Constants
PORT = 8004
HOST = "localhost"

# Initialize managers
db = Database()
github_manager = GitHubManager()

class MessageHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_static_file('static/index.html', 'text/html')
        elif parsed_path.path == '/messages':
            self.handle_get_messages()
        elif parsed_path.path == '/repositories':
            self.handle_get_repositories()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/messages':
            self.handle_post_message()
        elif self.path == '/repositories':
            self.handle_post_repository()
        elif self.path == '/push':
            self.handle_push_repository()
        else:
            self.send_error(404, "Not Found")
    
    def serve_static_file(self, filepath: str, content_type: str):
        """Serve a static file"""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, "File not found")
        except Exception as e:
            self.send_error(500, f"Error serving file: {str(e)}")
    
    def handle_get_messages(self):
        """Handle GET /messages request"""
        try:
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            
            # Get repository_id from query parameters
            repository_id = None
            if 'repository_id' in params:
                repository_id = int(params['repository_id'][0])
            
            if repository_id:
                messages = db.get_messages_by_repository(repository_id)
            else:
                messages = db.get_all_messages()
                
            self.send_json_response(200, messages)
        except Exception as e:
            self.send_error(500, f"Error retrieving messages: {str(e)}")
    
    def handle_get_repositories(self):
        """Handle GET /repositories request"""
        try:
            repositories = github_manager.get_repositories()
            self.send_json_response(200, repositories)
        except Exception as e:
            self.send_error(500, f"Error retrieving repositories: {str(e)}")
    
    async def handle_post_repository(self):
        """Handle POST /repositories request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            repo_data = json.loads(post_data.decode('utf-8'))
            
            if 'owner' not in repo_data or 'name' not in repo_data:
                self.send_error(400, "Repository owner and name are required")
                return
            
            # Add repository
            repository = await github_manager.add_repository(
                repo_data['owner'],
                repo_data['name']
            )
            
            self.send_json_response(201, repository)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON format")
        except ValueError as e:
            self.send_error(400, str(e))
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    async def handle_post_message(self):
        """Handle POST /messages request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            message_data = json.loads(post_data.decode('utf-8'))
            
            # Validate message content
            if 'content' not in message_data:
                self.send_error(400, "Message content is required")
                return
                
            content = message_data['content'].strip()
            if not content:
                self.send_error(400, "Message content cannot be empty")
                return
                
            if len(content) > 1000:
                self.send_error(400, "Message content too long (maximum 1000 characters)")
                return
            
            # Get optional repository_id
            repository_id = message_data.get('repository_id')
            
            # Save message
            message = await github_manager.save_message(content, repository_id)
            self.send_json_response(201, message)
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON format")
        except ValueError as e:
            self.send_error(400, str(e))
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    async def handle_push_repository(self):
        """Handle POST /push request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            repo_data = json.loads(post_data.decode('utf-8'))
            
            if 'owner' not in repo_data or 'name' not in repo_data:
                self.send_error(400, "Repository owner and name are required")
                return
            
            # Push repository
            result = await github_manager.push_repository(
                repo_data['owner'],
                repo_data['name']
            )
            
            self.send_json_response(200, result)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON format")
        except ValueError as e:
            self.send_error(400, str(e))
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def send_json_response(self, status: int, data: any):
        """Send a JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

class AsyncHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def service_actions(self):
        """Run any pending coroutines"""
        self.loop.stop()
        self.loop.run_forever()

def run_server():
    """Run the HTTP server"""
    server_address = (HOST, PORT)
    with AsyncHTTPServer(server_address, MessageHandler) as httpd:
        print(f"Server running at http://{HOST}:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
