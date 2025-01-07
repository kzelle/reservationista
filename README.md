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
├── .env.example         # Example environment file
├── .gitignore          # Git ignore file
├── README.md           # Project documentation
├── requirements.txt    # Python dependencies
├── static/             # Static files
│   ├── css/           # Stylesheets
│   └── js/            # JavaScript files
├── templates/          # HTML templates
├── database/          # SQLite database
├── setup.py            # Setup utility
└── server.py          # Python server
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd reservationista
   ```

2. Set up your environment:
   - First, create your environment file:
     ```bash
     cp .env.example .env
     ```
   - Create a GitHub personal access token:
     1. Go to GitHub Settings > Developer Settings > Personal Access Tokens > Tokens (classic)
     2. Click "Generate new token" and select "Generate new token (classic)"
     3. Give your token a descriptive name (e.g., "Reservationista App")
     4. Select the following scopes:
        - `repo` (Full control of private repositories)
        - `read:user` (Read access to user profile data)
     5. Click "Generate token" and copy it immediately

   - Use the setup utility to configure your environment:
     ```bash
     # List all environment variables and their current values
     python setup.py list

     # Set specific variables (e.g., GitHub token)
     python setup.py set GITHUB_TOKEN your_token_here
     python setup.py set GITHUB_USERNAME your_username

     # View a specific variable
     python setup.py get GITHUB_USERNAME

     # Check if your configuration is valid
     python setup.py check
     ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python -c "from database.db import Database; db = Database()"
   ```

5. Run the server:
   ```bash
   python server.py
   ```

6. Access the application:
   - Open your web browser and navigate to `http://localhost:8004`
   - You should see the messaging interface
   - Try adding a repository via the API:
     ```bash
     curl -X POST -H "Content-Type: application/json" \
          -d '{"owner":"your_username","name":"your_repo"}' \
          http://localhost:8004/repositories
     ```

## API Endpoints

### Repositories
- `GET /repositories` - List all tracked repositories
- `POST /repositories` - Add a new repository
  ```json
  {
    "owner": "github_username",
    "name": "repository_name"
  }
  ```

### Messages
- `GET /messages` - Get all messages from all repositories
- `GET /messages?repository_id=1` - Get messages from a specific repository
- `POST /messages` - Send a new message
  ```json
  {
    "content": "Your message here",
    "repository_id": 1  // Optional, uses first repository if not specified
  }
  ```

### Repository Management
- `GET /repositories` - List all tracked repositories
- `POST /repositories` - Add a new repository
  ```json
  {
    "owner": "github_username",
    "name": "repository_name"
  }
  ```
- `POST /push` - Push local changes to GitHub
  ```json
  {
    "owner": "github_username",
    "name": "repository_name"
  }
  ```
  Example:
  ```bash
  # Push changes to GitHub
  curl -X POST -H "Content-Type: application/json" \
       -d '{"owner":"your_username","name":"your_repo"}' \
       http://localhost:8004/push
  ```

## Development

This project is built incrementally with minimal dependencies. Each component is designed to be simple and maintainable.

## License

MIT License - Feel free to use this project for personal or commercial purposes.
