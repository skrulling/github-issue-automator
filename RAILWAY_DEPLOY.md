# Railway Deployment Guide

## Prerequisites

1. **GitHub Account** with your issue automator code
2. **Railway Account** - Sign up at [railway.app](https://railway.app)
3. **GitHub Personal Access Token** with repo permissions
4. **Claude Code Authentication** (you'll need to handle this specially)

## Step 1: Prepare Your Repository

1. Push this code to a GitHub repository:
```bash
cd github-issue-automator
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/github-issue-automator.git
git push -u origin main
```

## Step 2: Deploy to Railway

### Option A: Using Railway CLI (Recommended)

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login to Railway:
```bash
railway login
```

3. Initialize and deploy:
```bash
railway init
railway up
```

### Option B: Using Railway Web Dashboard

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect the Dockerfile

## Step 3: Configure Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

```
GITHUB_TOKEN=ghp_your_github_personal_access_token
REPO_OWNER=target_repo_owner
REPO_NAME=target_repo_name  
TARGET_USER=username_to_watch_for_issues
POLL_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

## Step 4: Handle Claude Code Authentication

**Important**: Claude Code authentication is tricky in containerized environments. You have a few options:

### Option A: Manual Authentication (Recommended)
1. Deploy the app first (it will fail initially)
2. Use Railway's "Shell" feature to access the container
3. Run `claude auth login` in the shell
4. Restart the service

### Option B: Pre-authenticated Container
1. Authenticate Claude Code locally
2. Copy authentication files to the project
3. Modify Dockerfile to copy them in

### Option C: Environment-based Auth (if available)
Check if Claude Code supports API key or token-based authentication

## Step 5: Configure GitHub CLI

Add to your environment variables:
```
GH_TOKEN=your_github_personal_access_token
```

This will authenticate GitHub CLI automatically.

## Step 6: Monitor Deployment

1. Check logs in Railway dashboard
2. Look for successful startup messages
3. Test by creating an issue in your target repo

## Troubleshooting

### Common Issues:

1. **Claude Code not authenticated**
   - Use Railway shell to manually authenticate
   - Check Claude Code documentation for container authentication

2. **GitHub CLI authentication failed**
   - Ensure GH_TOKEN environment variable is set
   - Token needs repo permissions

3. **Python import errors**
   - Check that all dependencies are in requirements.txt
   - Verify Python path in container

4. **Git operations failing**
   - Ensure GitHub token has proper permissions
   - Check network connectivity from Railway

### Viewing Logs:
```bash
railway logs
```

### Accessing Container Shell:
1. Go to Railway dashboard
2. Select your service
3. Click "Shell" tab
4. Run commands to debug

## Production Considerations

1. **Secrets Management**: Use Railway's environment variables for all secrets
2. **Monitoring**: Set up Railway's monitoring features
3. **Scaling**: Railway auto-scales, but monitor resource usage
4. **Backup**: Keep your repository backed up
5. **Updates**: Use Railway's GitHub integration for automatic deployments

## Cost Optimization

- Railway free tier: $5 credit monthly
- Monitor usage in Railway dashboard
- Consider using Railway's sleep feature for development

## Next Steps

1. Test the deployment with a real issue
2. Monitor logs for any errors
3. Set up Railway's monitoring alerts
4. Consider adding health checks