#!/usr/bin/env python3

import os
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
import aiohttp
from dotenv import load_dotenv
from database.db import Database
from git_handler import GitHandler

class GitHubManager:
    """Manage multiple GitHub repositories"""
    
    def __init__(self):
        """Initialize GitHub manager"""
        load_dotenv()
        
        self.token = os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
            
        self.db = Database()
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
    async def add_repository(self, owner: str, name: str) -> Dict:
        """Add a new repository to track"""
        # Verify repository exists and is accessible
        async with aiohttp.ClientSession() as session:
            url = f"https://api.github.com/repos/{owner}/{name}"
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    raise ValueError(f"Repository {owner}/{name} not found or not accessible")
                
                repo_data = await response.json()
                
        # Add to database
        repo_id = self.db.add_repository(owner, name)
        
        # Initialize Git handler for this repository
        git_handler = GitHandler(owner=owner, repo_name=name)
        
        return {
            'id': repo_id,
            'owner': owner,
            'name': name,
            'url': repo_data['html_url']
        }
    
    def get_repositories(self) -> List[Dict]:
        """Get all tracked repositories"""
        return self.db.get_repositories()
    
    async def fetch_repository_messages(self, owner: str, name: str, since: Optional[datetime] = None) -> List[Dict]:
        """Fetch messages from a specific repository"""
        async with aiohttp.ClientSession() as session:
            url = f"https://api.github.com/repos/{owner}/{name}/commits"
            params = {'since': since.isoformat()} if since else {}
            
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch commits from {owner}/{name}")
                
                commits = await response.json()
                
        messages = []
        for commit in commits:
            messages.append({
                'content': commit['commit']['message'],
                'author': commit['commit']['author']['name'],
                'timestamp': commit['commit']['author']['date'],
                'url': commit['html_url'],
                'repository': f"{owner}/{name}",
                'sha': commit['sha']
            })
            
        return messages
    
    async def fetch_all_messages(self, since: Optional[datetime] = None) -> List[Dict]:
        """Fetch messages from all tracked repositories"""
        repositories = self.get_repositories()
        tasks = []
        
        for repo in repositories:
            task = self.fetch_repository_messages(repo['owner'], repo['name'], since)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_messages = []
        for repo, result in zip(repositories, results):
            if isinstance(result, Exception):
                print(f"Error fetching messages from {repo['owner']}/{repo['name']}: {str(result)}")
                continue
            all_messages.extend(result)
        
        # Sort by timestamp
        all_messages.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_messages
    
    async def save_message(self, content: str, repository_id: Optional[int] = None) -> Dict:
        """Save a message to specified repository (or first available if not specified)"""
        if repository_id is None:
            repositories = self.get_repositories()
            if not repositories:
                raise ValueError("No repositories available")
            repository_id = repositories[0]['id']
        
        # Get repository info
        repo = next((r for r in self.get_repositories() if r['id'] == repository_id), None)
        if not repo:
            raise ValueError(f"Repository with ID {repository_id} not found")
        
        # Initialize Git handler for this repository
        git_handler = GitHandler(owner=repo['owner'], repo_name=repo['name'])
        
        # Save message
        git_hash = git_handler.save_message(content)
        if not git_hash:
            raise ValueError("Failed to save message to Git repository")
        
        # Save to database
        message_id = self.db.add_message(content, repository_id, git_hash)
        
        return self.db.get_message(message_id)
    
    async def push_repository(self, owner: str, name: str) -> Dict:
        """Push local changes to GitHub repository"""
        # Get repository info
        repo = next((r for r in self.get_repositories() 
                    if r['owner'] == owner and r['name'] == name), None)
        if not repo:
            raise ValueError(f"Repository {owner}/{name} not found in tracked repositories")
            
        # Initialize Git handler
        git_handler = GitHandler(owner=owner, repo_name=name)
        
        try:
            # Push changes
            result = git_handler.push_changes()
            if not result:
                raise ValueError("Failed to push changes")
                
            return {
                'status': 'success',
                'repository': f"{owner}/{name}",
                'message': 'Successfully pushed changes to GitHub'
            }
        except Exception as e:
            raise ValueError(f"Failed to push changes: {str(e)}")

async def main():
    """Example usage"""
    github_manager = GitHubManager()
    
    # Add repositories to track
    try:
        await github_manager.add_repository('kzelle', 'reservationista')
        print("Added repository successfully")
    except ValueError as e:
        print(f"Error adding repository: {str(e)}")
    
    # Fetch messages from all repositories
    try:
        messages = await github_manager.fetch_all_messages()
        print(f"\nFound {len(messages)} messages across all repositories:")
        for msg in messages[:5]:  # Show first 5 messages
            print(f"\nRepository: {msg['repository']}")
            print(f"Message: {msg['content']}")
            print(f"Author: {msg['author']}")
            print(f"Date: {msg['timestamp']}")
            print(f"URL: {msg['url']}")
    except Exception as e:
        print(f"Error fetching messages: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
