#!/usr/bin/env python3

import os
import argparse
from typing import List, Dict, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv

class GitHubAPI:
    """Class to interact with GitHub REST API"""
    
    def __init__(self, token: Optional[str] = None, username: Optional[str] = None):
        """
        Initialize GitHub API client
        
        Args:
            token: GitHub personal access token. If None, will try to load from GITHUB_TOKEN env var
            username: GitHub username. If None, will try to load from GITHUB_USERNAME env var
        """
        # Load environment variables if needed
        if token is None or username is None:
            load_dotenv()
            
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable or pass token to constructor.")
            
        self.username = username or os.getenv('GITHUB_USERNAME')
        if not self.username:
            raise ValueError("GitHub username is required. Set GITHUB_USERNAME environment variable or pass username to constructor.")
            
        self.api_base_url = "https://api.github.com"
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def get_commits(self, repo_name: str, branch: str = 'main', per_page: int = 30, page: int = 1) -> List[Dict]:
        """
        Fetch commit messages from a repository
        
        Args:
            repo_name: Name of the repository
            branch: Branch to fetch commits from (default: main)
            per_page: Number of commits per page (default: 30)
            page: Page number for pagination (default: 1)
            
        Returns:
            List of dictionaries containing commit information:
            {
                'sha': commit hash,
                'message': commit message,
                'author': author name,
                'author_email': author email,
                'date': commit date,
                'url': commit URL
            }
        """
        url = f"{self.api_base_url}/repos/{self.username}/{repo_name}/commits"
        params = {
            'sha': branch,
            'per_page': per_page,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            commits = []
            for commit_data in response.json():
                commit = commit_data['commit']
                commits.append({
                    'sha': commit_data['sha'],
                    'message': commit['message'],
                    'author': commit['author']['name'],
                    'author_email': commit['author']['email'],
                    'date': datetime.strptime(commit['author']['date'], '%Y-%m-%dT%H:%M:%SZ'),
                    'url': commit_data['html_url']
                })
            
            return commits
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching commits: {str(e)}")
            if hasattr(e.response, 'json'):
                print(f"GitHub API response: {e.response.json()}")
            return []
    
    def get_all_commits(self, repo_name: str, branch: str = 'main', max_pages: int = 10) -> List[Dict]:
        """
        Fetch all commit messages from a repository
        
        Args:
            repo_name: Name of the repository
            branch: Branch to fetch commits from (default: main)
            max_pages: Maximum number of pages to fetch (default: 10)
            
        Returns:
            List of dictionaries containing commit information
        """
        all_commits = []
        page = 1
        
        while page <= max_pages:
            commits = self.get_commits(repo_name, branch, per_page=100, page=page)
            if not commits:
                break
                
            all_commits.extend(commits)
            if len(commits) < 100:  # Last page
                break
                
            page += 1
        
        return all_commits

def main():
    """Example usage"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fetch commit messages from a GitHub repository')
    parser.add_argument('--token', help='GitHub personal access token')
    parser.add_argument('--username', help='GitHub username')
    parser.add_argument('--repo', help='GitHub repository name', default='reservationista')
    parser.add_argument('--branch', help='Branch to fetch commits from', default='main')
    parser.add_argument('--max-pages', type=int, help='Maximum number of pages to fetch', default=10)
    args = parser.parse_args()
    
    try:
        # Initialize GitHub API client
        github = GitHubAPI(token=args.token, username=args.username)
        
        # Fetch commits
        commits = github.get_all_commits(args.repo, args.branch, args.max_pages)
        
        # Print commit messages
        print(f"\nFound {len(commits)} commits in {args.repo}:")
        for commit in commits:
            print(f"\nCommit: {commit['sha'][:8]}")
            print(f"Author: {commit['author']} <{commit['author_email']}>")
            print(f"Date: {commit['date']}")
            print(f"Message: {commit['message']}")
            print(f"URL: {commit['url']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        parser.print_help()

if __name__ == "__main__":
    main()
