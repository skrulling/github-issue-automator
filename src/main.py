#!/usr/bin/env python3

import time
import logging
import schedule
import subprocess
from typing import Set

from config import Config
from logger import setup_logging
from github_client import GitHubClient
from claude_executor import ClaudeExecutor
from health_server import start_health_server

# Track processed issues to avoid duplicates
processed_issues: Set[int] = set()

def process_new_issues():
    """Main function to check for and process new issues"""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize clients
        github_client = GitHubClient(
            token=Config.GITHUB_TOKEN,
            repo_owner=Config.REPO_OWNER,
            repo_name=Config.REPO_NAME
        )
        
        claude_executor = ClaudeExecutor()
        
        # Get recent issues by target user
        recent_issues = github_client.get_recent_issues_by_user(
            username=Config.TARGET_USER,
            minutes_back=Config.POLL_INTERVAL_MINUTES
        )
        
        if not recent_issues:
            logger.info("No new issues found")
            return
        
        logger.info(f"Found {len(recent_issues)} recent issues")
        
        # Process each new issue
        for issue in recent_issues:
            if issue.number in processed_issues:
                logger.info(f"Issue #{issue.number} already processed, skipping")
                continue
            
            logger.info(f"Processing issue #{issue.number}: {issue.title}")
            
            # Add comment to issue indicating we're working on it
            github_client.add_comment(
                issue.number,
                "🤖 Automated fix in progress. Claude Code is analyzing this issue..."
            )
            
            # Execute Claude Code to fix the issue
            success, message = claude_executor.execute_issue_fix(
                repo_url=Config.get_repo_url(),
                issue_number=issue.number,
                issue_title=issue.title,
                issue_body=issue.body or ""
            )
            
            if success:
                logger.info(f"Successfully processed issue #{issue.number}")
                
                # Add success comment and close issue
                github_client.add_comment(
                    issue.number,
                    f"✅ Automated fix completed! {message}"
                )
                
                github_client.close_issue(
                    issue.number,
                    "🤖 Issue automatically resolved by Claude Code automation."
                )
                
            else:
                logger.error(f"Failed to process issue #{issue.number}: {message}")
                
                # Add failure comment
                github_client.add_comment(
                    issue.number,
                    f"❌ Automated fix failed: {message}\n\nPlease review and fix manually."
                )
            
            # Mark as processed regardless of success/failure
            processed_issues.add(issue.number)
        
        # Cleanup
        claude_executor.cleanup()
        
    except Exception as e:
        logger.error(f"Error in process_new_issues: {e}")

def check_claude_authentication():
    """Check if Claude Code is authenticated, attempt login if not"""
    logger = logging.getLogger(__name__)
    
    try:
        # First check if already authenticated
        result = subprocess.run(['claude', 'auth', 'status'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("✅ Claude Code is already authenticated")
            return True
        else:
            logger.info("❌ Claude Code not authenticated, attempting login...")
            
            # Attempt interactive login (will output URL to logs)
            logger.info("🔗 Starting Claude Code authentication process...")
            logger.info("📋 Please check the logs below for the authentication URL")
            logger.info("=" * 60)
            
            # Start the login process
            login_process = subprocess.Popen(
                ['claude', 'auth', 'login'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line and log it
            for line in iter(login_process.stdout.readline, ''):
                if line.strip():
                    logger.info(f"CLAUDE AUTH: {line.strip()}")
                    
                    # Look for authentication URL
                    if "http" in line.lower() and ("claude.ai" in line.lower() or "anthropic" in line.lower()):
                        logger.info("🔥 AUTHENTICATION URL FOUND ABOVE! 🔥")
                        logger.info("👆 Copy the URL from the line above and open it in your browser")
                
            login_process.wait(timeout=300)  # Wait up to 5 minutes
            
            if login_process.returncode == 0:
                logger.info("✅ Claude Code authentication completed successfully!")
                return True
            else:
                logger.error("❌ Claude Code authentication failed")
                return False
                
    except subprocess.TimeoutExpired:
        logger.error("⏰ Claude Code authentication timed out")
        return False
    except FileNotFoundError:
        logger.error("❌ Claude Code CLI not found. Please install it first.")
        return False
    except Exception as e:
        logger.error(f"❌ Error during Claude Code authentication: {e}")
        return False

def main():
    """Main application entry point"""
    try:
        # Validate configuration
        Config.validate()
        
        # Setup logging
        logger = setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)
        logger.info("GitHub Issue Automator starting...")
        
        # Start health check server
        start_health_server()
        
        # Check Claude Code authentication
        logger.info("🔐 Checking Claude Code authentication...")
        claude_authenticated = check_claude_authentication()
        
        if not claude_authenticated:
            logger.warning("⚠️  Claude Code not authenticated. Issue processing will fail until authenticated.")
            logger.info("💡 Check the logs above for authentication URL, or restart the service after authentication")
        
        logger.info(f"Monitoring repo: {Config.REPO_OWNER}/{Config.REPO_NAME}")
        logger.info(f"Target user: {Config.TARGET_USER}")
        logger.info(f"Poll interval: {Config.POLL_INTERVAL_MINUTES} minutes")
        
        # Schedule the job
        schedule.every(Config.POLL_INTERVAL_MINUTES).minutes.do(process_new_issues)
        
        # Run initial check
        logger.info("Running initial issue check...")
        process_new_issues()
        
        # Start the scheduler
        logger.info("Starting scheduler...")
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()