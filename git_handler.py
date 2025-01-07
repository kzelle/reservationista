#!/usr/bin/env python3

import os
import subprocess
import json
from datetime import datetime
from typing import Optional, Dict, List
import requests
from pathlib import Path

class GitHandler:
    """Handles Git operations for message storage"""
    
    def __init__(self, repo_path: str, github_token: str, github_username: str):
        """
        Initialize GitHandler
        
        Args:
            repo_path: Path to local git repository
            github_token: GitHub personal access token
            github_username: GitHub username
        """
        self.repo_path = Path(repo_path)
        self.messages_dir = self.repo_path / 'messages'
        self.github_token = github_token
        self.github_username = github_username
        
        # Create repository directory if it doesn't exist
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.messages_dir.mkdir(exist_ok=True)
        
        # GitHub API configuration
        self.github_api_url = "https://api.github.com"
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def _run_git_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        Run a git command and return the result
        
        Args:
            command: Git command and arguments
            check: Whether to raise an exception on command failure
        """
        try:
            return subprocess.run(
                ['git'] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check
            )
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
            if check:
                raise
            return e.returncode

    def save_message(self, message_content: str, message_id: int) -> Optional[str]:
        """
        Save a message to a file and push it to GitHub
        
        Args:
            message_content: Content of the message
            message_id: Database ID of the message
            
        Returns:
            Git commit hash if successful, None otherwise
        """
        try:
            # Create message file
            timestamp = datetime.now().isoformat()
            message_data = {
                'id': message_id,
                'content': message_content,
                'timestamp': timestamp
            }
            
            # Create filename with timestamp and ID
            filename = f"message_{message_id}_{timestamp.replace(':', '-')}.json"
            file_path = self.messages_dir / filename
            
            # Write message to file
            with open(file_path, 'w') as f:
                json.dump(message_data, f, indent=2)
            
            try:
                # Stage the file
                self._run_git_command(['add', str(file_path)], check=False)
                
                # Create commit
                self._run_git_command(['commit', '-m', f"Add message {message_id}"], check=False)
                
                # Push to GitHub
                self._run_git_command(['push', 'origin', 'main'], check=False)
                
                # Get commit hash
                result = self._run_git_command(['rev-parse', 'HEAD'], check=False)
                if isinstance(result, subprocess.CompletedProcess) and result.returncode == 0:
                    return result.stdout.strip()
                return None
                
            except Exception as e:
                print(f"Git operations failed: {e}")
                return None
                
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    def get_message_history(self, message_id: int) -> List[Dict]:
        """
        Get the history of a message from Git
        
        Args:
            message_id: ID of the message
            
        Returns:
            List of dictionaries containing message versions
        """
        try:
            # Find all files for this message
            pattern = f"message_{message_id}_*.json"
            files = list(self.messages_dir.glob(pattern))
            
            history = []
            for file_path in files:
                with open(file_path, 'r') as f:
                    message_data = json.load(f)
                    history.append(message_data)
            
            # Sort by timestamp
            return sorted(history, key=lambda x: x['timestamp'])
            
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error retrieving message history: {e}")
            return []

    @classmethod
    def clone_repository(cls, repo_name: str, github_token: str, 
                        github_username: str, local_path: str) -> 'GitHandler':
        """
        Clone a GitHub repository and return a GitHandler instance
        
        Args:
            repo_name: Name of the repository
            github_token: GitHub personal access token
            github_username: GitHub username
            local_path: Local path to clone the repository to
            
        Returns:
            GitHandler instance
        """
        repo_url = f"https://{github_token}@github.com/{github_username}/{repo_name}.git"
        
        try:
            # Create the directory if it doesn't exist
            os.makedirs(local_path, exist_ok=True)
            
            # Clone the repository
            subprocess.run(
                ['git', 'clone', repo_url, local_path],
                check=True,
                capture_output=True,
                text=True
            )
            
            return cls(local_path, github_token, github_username)
            
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")
            raise
