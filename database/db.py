#!/usr/bin/env python3

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "messages.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create necessary database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create repositories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repositories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner, name)
                )
            """)
            
            # Create messages table with repository reference
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    repository_id INTEGER,
                    git_hash TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (repository_id) REFERENCES repositories(id)
                )
            """)
            
            conn.commit()

    def add_repository(self, owner: str, name: str) -> int:
        """Add a new repository to track"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO repositories (owner, name) VALUES (?, ?)",
                    (owner, name)
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute(
                    "SELECT id FROM repositories WHERE owner = ? AND name = ?",
                    (owner, name)
                )
                return cursor.fetchone()[0]

    def get_repositories(self) -> List[Dict]:
        """Get all tracked repositories"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM repositories ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def add_message(self, content: str, repository_id: int, git_hash: Optional[str] = None) -> int:
        """Add a new message"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (content, repository_id, git_hash) VALUES (?, ?, ?)",
                (content, repository_id, git_hash)
            )
            return cursor.lastrowid

    def update_git_hash(self, message_id: int, git_hash: str):
        """Update the Git hash for a message"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE messages SET git_hash = ? WHERE id = ?",
                (git_hash, message_id)
            )

    def get_message(self, message_id: int) -> Optional[Dict]:
        """Get a specific message by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, r.owner, r.name as repo_name
                FROM messages m
                LEFT JOIN repositories r ON m.repository_id = r.id
                WHERE m.id = ?
            """, (message_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_messages(self, limit: int = 100) -> List[Dict]:
        """Get all messages with repository information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    m.*,
                    r.owner,
                    r.name as repo_name
                FROM messages m
                LEFT JOIN repositories r ON m.repository_id = r.id
                ORDER BY m.timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_messages_by_repository(self, repository_id: int, limit: int = 50) -> List[Dict]:
        """Get messages for a specific repository"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    m.*,
                    r.owner,
                    r.name as repo_name
                FROM messages m
                LEFT JOIN repositories r ON m.repository_id = r.id
                WHERE m.repository_id = ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            """, (repository_id, limit))
            return [dict(row) for row in cursor.fetchall()]
