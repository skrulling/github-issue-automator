# GitHub Issue Automator

Automatically detect new GitHub issues from a specific user and use Claude Code to fix them.

## Features

- Monitors a GitHub repository for new issues from a specific user
- Automatically creates a new branch for each issue
- Uses Claude Code in non-interactive mode to analyze and fix the issue
- Creates a pull request with the fix
- Closes the original issue when complete
- Comprehensive logging and error handling

## Setup

### Prerequisites

- Python 3.11+
- GitHub personal access token with repo permissions
- Claude Code CLI installed and authenticated
- GitHub CLI (gh) installed and authenticated

### Installation

1. Clone this project:
```bash
git clone <this-repo>
cd github-issue-automator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Required environment variables:
```
GITHUB_TOKEN=your_github_personal_access_token
REPO_OWNER=target_repo_owner
REPO_NAME=target_repo_name
TARGET_USER=username_to_watch_for_issues
POLL_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

### GitHub Token Setup

Create a GitHub personal access token with these permissions:
- `repo` (full repository access)
- `read:user` (read user information)

### Claude Code Setup

Make sure Claude Code is installed and authenticated:
```bash
# Install Claude Code (follow official installation instructions)
# Authenticate with your Claude account
claude auth login
```

### GitHub CLI Setup

Install and authenticate GitHub CLI:
```bash
# Install gh (follow official installation instructions)
# Authenticate
gh auth login
```

## Usage

### Local Development

```bash
python src/main.py
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## How It Works

1. **Polling**: The app polls the specified GitHub repository every N minutes
2. **Issue Detection**: Looks for new issues created by the target user
3. **Processing**: For each new issue:
   - Clones the repository to a temporary directory
   - Creates a new branch named `fix-issue-{number}`
   - Runs Claude Code with a detailed prompt about the issue
   - Claude Code analyzes the issue and implements a fix
   - Pushes the branch and creates a pull request
   - Closes the original issue with a success comment
4. **Error Handling**: If any step fails, adds a comment to the issue explaining the failure

## Deployment Options

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Fly.io
```bash
# Install flyctl
# Create fly.toml configuration
flyctl deploy
```

### DigitalOcean App Platform
- Upload this code to a Git repository
- Connect the repository to DigitalOcean App Platform
- Configure environment variables in the dashboard
- Deploy

## Configuration

### Polling Interval
Adjust `POLL_INTERVAL_MINUTES` to change how often the app checks for new issues.

### Logging
- Logs are written to both console and `logs/automator.log`
- Adjust `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR)

## Limitations

- Requires Claude Code to be authenticated and available
- GitHub CLI must be authenticated for PR creation
- Internet connection required for GitHub API and Claude Code
- Processing time depends on issue complexity

## Security Notes

- Keep your GitHub token secure
- Don't commit `.env` file to version control
- Consider using secrets management in production
- Review generated code before merging PRs

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure all tools are properly authenticated
2. **Permission Errors**: Check GitHub token permissions
3. **Claude Code Timeout**: Increase timeout in `claude_executor.py` if needed
4. **Branch Conflicts**: The app creates unique branch names to avoid conflicts

### Logs

Check `logs/automator.log` for detailed execution logs and error messages.