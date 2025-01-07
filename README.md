# Git-Backed Messaging Application

A lightweight web-based messaging application that uses Git as a backend storage system. This application allows users to send and receive messages while maintaining a complete history of all communications through Git.

## Features

- Simple and intuitive web interface
- Message persistence using Git
- Real-time message updates
- SQLite database for user management
- GitHub API integration for backup and sync
- No framework dependencies

## Tech Stack

- Backend: Python (Standard Library)
- Database: SQLite3
- Frontend: HTML5, CSS3, JavaScript (Vanilla)
- Version Control: Git
- API: GitHub REST API

## Project Structure

```
reservationista/
├── .env                 # Environment variables
├── .gitignore          # Git ignore file
├── README.md           # Project documentation
├── static/             # Static files
│   ├── css/           # Stylesheets
│   └── js/            # JavaScript files
├── templates/          # HTML templates
├── database/          # SQLite database
└── server.py          # Python server
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd reservationista
   ```

2. Create a GitHub personal access token:
   - Go to GitHub Settings > Developer Settings > Personal Access Tokens
   - Generate a new token with `repo` scope
   - Copy the token

3. Create `.env` file with your GitHub credentials:
   ```
   GITHUB_TOKEN=your_personal_access_token
   GITHUB_USERNAME=your_username
   ```

4. Install Python (if not already installed)
   - Required version: Python 3.8+

5. Run the server:
   ```bash
   python server.py
   ```

6. Access the application:
   Open your web browser and navigate to `http://localhost:8000`

## Development

This project is built incrementally with minimal dependencies. Each component is designed to be simple and maintainable.

## License

MIT License - Feel free to use this project for personal or commercial purposes.
