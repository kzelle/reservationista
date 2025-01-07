#!/usr/bin/env python3

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional

# Database configuration
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'messages.db')

class Database:
    """Database handler for the messaging application"""
    
    def __init__(self):
        """Initialize database connection and create tables if they don't exist"""
        self.conn = None
        self.cursor = None
        self.initialize()

    def initialize(self):
        """Create the database connection and initialize tables"""
        try:
            self.conn = sqlite3.connect(DB_FILE)
            self.cursor = self.conn.cursor()
            
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create messages table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    git_hash TEXT,
                    UNIQUE(git_hash)
                )
            """)
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            raise

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()

    def add_message(self, content: str, git_hash: Optional[str] = None) -> int:
        """
        Add a new message to the database
        
        Args:
            content: The message content
            git_hash: Optional Git commit hash associated with the message
            
        Returns:
            The ID of the newly inserted message
        """
        try:
            timestamp = datetime.now().isoformat()
            self.cursor.execute("""
                INSERT INTO messages (content, timestamp, git_hash)
                VALUES (?, ?, ?)
            """, (content, timestamp, git_hash))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error adding message: {e}")
            self.conn.rollback()
            raise

    def get_message(self, message_id: int) -> Optional[Dict]:
        """
        Retrieve a specific message by ID
        
        Args:
            message_id: The ID of the message to retrieve
            
        Returns:
            Dictionary containing message data or None if not found
        """
        try:
            self.cursor.execute("""
                SELECT id, content, timestamp, git_hash
                FROM messages
                WHERE id = ?
            """, (message_id,))
            
            row = self.cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'content': row[1],
                    'timestamp': row[2],
                    'git_hash': row[3]
                }
            return None
        except sqlite3.Error as e:
            print(f"Error retrieving message: {e}")
            raise

    def get_all_messages(self) -> List[Dict]:
        """
        Retrieve all messages from the database
        
        Returns:
            List of dictionaries containing message data
        """
        try:
            self.cursor.execute("""
                SELECT id, content, timestamp, git_hash
                FROM messages
                ORDER BY timestamp DESC
            """)
            
            return [{
                'id': row[0],
                'content': row[1],
                'timestamp': row[2],
                'git_hash': row[3]
            } for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error retrieving messages: {e}")
            raise

    def update_git_hash(self, message_id: int, git_hash: str) -> bool:
        """
        Update the Git hash for a message
        
        Args:
            message_id: The ID of the message to update
            git_hash: The Git commit hash to associate with the message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute("""
                UPDATE messages
                SET git_hash = ?
                WHERE id = ?
            """, (git_hash, message_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating git hash: {e}")
            self.conn.rollback()
            return False

# Create an instance of the database
db = Database()
