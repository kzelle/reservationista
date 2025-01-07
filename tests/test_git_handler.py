#!/usr/bin/env python3

import unittest
import os
import shutil
import tempfile
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
from git_handler import GitHandler

class TestGitHandler(unittest.TestCase):
    """Test cases for GitHandler class"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.test_dir))

        # Mock GitHub credentials
        self.github_token = "test_token"
        self.github_username = "test_user"

        # Initialize GitHandler with test directory
        self.git_handler = GitHandler(
            repo_path=self.test_dir,
            github_token=self.github_token,
            github_username=self.github_username
        )

    def test_messages_directory_creation(self):
        """Test that messages directory is created"""
        messages_dir = Path(self.test_dir) / 'messages'
        self.assertTrue(messages_dir.exists())
        self.assertTrue(messages_dir.is_dir())

    @patch('subprocess.run')
    def test_save_message(self, mock_run):
        """Test saving a message"""
        # Mock successful git commands
        mock_run.return_value = MagicMock(
            stdout="test_commit_hash\n",
            returncode=0
        )

        # Test data
        message_content = "Test message"
        message_id = 1

        # Save message
        commit_hash = self.git_handler.save_message(message_content, message_id)

        # Verify commit hash is returned
        self.assertIsNotNone(commit_hash)
        self.assertEqual(commit_hash, "test_commit_hash")

        # Verify file was created
        message_files = list(Path(self.test_dir).glob('messages/message_1_*.json'))
        self.assertEqual(len(message_files), 1)

        # Verify file contents
        with open(message_files[0], 'r') as f:
            message_data = json.load(f)
            self.assertEqual(message_data['content'], message_content)
            self.assertEqual(message_data['id'], message_id)
            self.assertIn('timestamp', message_data)

        # Verify git commands were called
        expected_calls = [
            ['add', str(message_files[0])],
            ['commit', '-m', 'Add message 1'],
            ['push', 'origin', 'main'],
            ['rev-parse', 'HEAD']
        ]
        
        actual_calls = [call.args[0][1:] for call in mock_run.call_args_list]
        self.assertEqual(actual_calls, expected_calls)

    @patch('subprocess.run')
    def test_save_message_git_error(self, mock_run):
        """Test handling git command failure"""
        # Mock git command failure
        mock_run.side_effect = Exception("Git command failed")

        # Test data
        message_content = "Test message"
        message_id = 1

        # Attempt to save message
        commit_hash = self.git_handler.save_message(message_content, message_id)

        # Verify no commit hash is returned
        self.assertIsNone(commit_hash)

    def test_get_message_history(self):
        """Test retrieving message history"""
        # Create test message files
        message_id = 1
        messages = [
            {"id": message_id, "content": "Version 1", "timestamp": "2025-01-07T15:00:00"},
            {"id": message_id, "content": "Version 2", "timestamp": "2025-01-07T15:30:00"}
        ]

        for i, msg in enumerate(messages, 1):
            filename = f"message_{message_id}_2025-01-07T15-{i}0-00.json"
            file_path = Path(self.test_dir) / 'messages' / filename
            with open(file_path, 'w') as f:
                json.dump(msg, f)

        # Get message history
        history = self.git_handler.get_message_history(message_id)

        # Verify history
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['content'], "Version 1")
        self.assertEqual(history[1]['content'], "Version 2")

    @patch('subprocess.run')
    def test_clone_repository(self, mock_run):
        """Test repository cloning"""
        # Mock successful clone
        mock_run.return_value = MagicMock(returncode=0)

        # Test data
        repo_name = "test_repo"
        local_path = os.path.join(self.test_dir, "cloned_repo")

        # Clone repository
        handler = GitHandler.clone_repository(
            repo_name=repo_name,
            github_token=self.github_token,
            github_username=self.github_username,
            local_path=local_path
        )

        # Verify GitHandler instance is returned
        self.assertIsInstance(handler, GitHandler)

        # Verify git clone was called with correct arguments
        expected_url = f"https://{self.github_token}@github.com/{self.github_username}/{repo_name}.git"
        mock_run.assert_called_once_with(
            ['git', 'clone', expected_url, local_path],
            check=True,
            capture_output=True,
            text=True
        )

if __name__ == '__main__':
    unittest.main()
