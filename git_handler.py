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
            result = subprocess.run(
                ['git'] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check
            )
            if not check:
                return result
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    returncode=result.returncode,
                    cmd=['git'] + command,
                    output=result.stdout,
                    stderr=result.stderr
                )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
            if check:
                raise
            return e

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
                add_result = self._run_git_command(['add', str(file_path)], check=False)
                if not isinstance(add_result, subprocess.CompletedProcess) or add_result.returncode != 0:
                    print(f"Failed to stage file: {add_result.stderr if hasattr(add_result, 'stderr') else 'Unknown error'}")
                    return None
                
                # Create commit
                commit_result = self._run_git_command(['commit', '-m', f"Add message {message_id}"], check=False)
                if not isinstance(commit_result, subprocess.CompletedProcess) or commit_result.returncode != 0:
                    print(f"Failed to commit: {commit_result.stderr if hasattr(commit_result, 'stderr') else 'Unknown error'}")
                    return None
                
                # Push to GitHub
                push_result = self.push_changes()
                if not push_result:
                    print(f"Failed to push: {push_result.stderr if hasattr(push_result, 'stderr') else 'Unknown error'}")
                    return None
                
                # Get commit hash
                hash_result = self._run_git_command(['rev-parse', 'HEAD'], check=False)
                if isinstance(hash_result, subprocess.CompletedProcess) and hash_result.returncode == 0:
                    return hash_result.stdout.strip()
                print(f"Failed to get commit hash: {hash_result.stderr if hasattr(hash_result, 'stderr') else 'Unknown error'}")
                return None
                
            except Exception as e:
                print(f"Git operations failed: {e}")
                return None
                
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    def push_changes(self) -> bool:
        """Push changes to GitHub"""
        try:
            # Check if there are changes to push
            status = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if not status.stdout.strip():
                # No changes to push
                return True

            # Get GitHub token from environment
            github_token = self.github_token
            if not github_token:
                raise ValueError("GitHub token not found")

            # Set remote URL with token
            remote_url = f"https://{github_token}@github.com/{self.github_username}/{self.repo_path.name}.git"
            subprocess.run(
                ['git', 'remote', 'set-url', 'origin', remote_url],
                cwd=self.repo_path,
                check=True
            )

            # Push changes
            result = subprocess.run(
                ['git', 'push', '-u', 'origin', 'main'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"Push error: {result.stderr}")
                return False

            return True

        except Exception as e:
            print(f"Error pushing changes: {str(e)}")
            return False

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
