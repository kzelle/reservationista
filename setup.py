#!/usr/bin/env python3

import os
import sys
import argparse
from typing import Optional, Dict
from dotenv import load_dotenv

# Required environment variables and their descriptions
ENV_VARS = {
    'GITHUB_TOKEN': 'GitHub Personal Access Token (required for repository operations)',
    'GITHUB_USERNAME': 'Your GitHub username',
    'GITHUB_REPO_NAME': 'Default repository name (optional)',
    'PORT': 'Server port (default: 8004)',
    'HOST': 'Server host (default: localhost)'
}

def load_env() -> Dict[str, str]:
    """Load current environment variables"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        # Create from example if it exists
        example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.example')
        if os.path.exists(example_path):
            with open(example_path, 'r') as src, open(env_path, 'w') as dst:
                dst.write(src.read())
    
    load_dotenv()
    return {key: os.getenv(key, '') for key in ENV_VARS.keys()}

def save_env(env_vars: Dict[str, str]):
    """Save environment variables to .env file"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    # Read existing file to preserve comments and formatting
    existing_lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            existing_lines = f.readlines()
    
    # Update or add variables while preserving comments
    updated_vars = set()
    for i, line in enumerate(existing_lines):
        if line.strip() and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key in env_vars:
                existing_lines[i] = f"{key}={env_vars[key]}\n"
                updated_vars.add(key)
    
    # Add any new variables
    for key, value in env_vars.items():
        if key not in updated_vars:
            existing_lines.append(f"{key}={value}\n")
    
    # Write back to file
    with open(env_path, 'w') as f:
        f.writelines(existing_lines)

def check_github_token(token: str) -> bool:
    """Validate GitHub token format"""
    return bool(token and len(token) >= 40 and not token.startswith('your_'))

def get_current_value(var_name: str) -> str:
    """Get current value of an environment variable"""
    current_vars = load_env()
    return current_vars.get(var_name, '')

def main():
    parser = argparse.ArgumentParser(description='Setup and manage environment variables')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all environment variables')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get value of specific environment variable')
    get_parser.add_argument('var_name', choices=ENV_VARS.keys(), help='Variable name')
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set value of specific environment variable')
    set_parser.add_argument('var_name', choices=ENV_VARS.keys(), help='Variable name')
    set_parser.add_argument('value', help='New value')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check environment configuration')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        current_vars = load_env()
        print("\nCurrent Environment Variables:")
        print("-----------------------------")
        for key in ENV_VARS:
            value = current_vars.get(key, '')
            desc = ENV_VARS[key]
            if key == 'GITHUB_TOKEN' and value:
                # Mask token for security
                value = f"{value[:4]}...{value[-4:]}"
            print(f"{key}:")
            print(f"  Value: {value}")
            print(f"  Description: {desc}")
            print()
    
    elif args.command == 'get':
        value = get_current_value(args.var_name)
        if args.var_name == 'GITHUB_TOKEN' and value:
            # Mask token for security
            value = f"{value[:4]}...{value[-4:]}"
        print(f"{args.var_name}={value}")
    
    elif args.command == 'set':
        current_vars = load_env()
        current_vars[args.var_name] = args.value
        save_env(current_vars)
        print(f"Updated {args.var_name}")
    
    elif args.command == 'check':
        current_vars = load_env()
        issues = []
        
        # Check required variables
        if not check_github_token(current_vars.get('GITHUB_TOKEN', '')):
            issues.append("GITHUB_TOKEN is missing or invalid")
        
        if not current_vars.get('GITHUB_USERNAME', ''):
            issues.append("GITHUB_USERNAME is not set")
        
        # Check optional variables with defaults
        if not current_vars.get('PORT', ''):
            print("Note: PORT not set, will use default (8004)")
        
        if not current_vars.get('HOST', ''):
            print("Note: HOST not set, will use default (localhost)")
        
        if issues:
            print("\nConfiguration Issues Found:")
            for issue in issues:
                print(f"- {issue}")
            sys.exit(1)
        else:
            print("\nConfiguration looks good! ✅")
            sys.exit(0)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
