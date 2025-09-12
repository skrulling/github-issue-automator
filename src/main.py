#!/usr/bin/env python3

import time
import logging
import schedule
import subprocess

from config import Config
from logger import setup_logging
from github_client import GitHubClient
from claude_executor import ClaudeExecutor
from health_server import start_health_server
from issue_tracker import IssueTracker

# Initialize issue tracker
issue_tracker = IssueTracker()

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
        
        # Get unprocessed issues by target user
        unprocessed_issues = github_client.get_unprocessed_issues_by_user(
            username=Config.TARGET_USER,
            processed_issues=issue_tracker.processed_issues
        )
        
        if not unprocessed_issues:
            logger.info(f"No unprocessed issues found by user '{Config.TARGET_USER}'")
            return
        
        logger.info(f"Found {len(unprocessed_issues)} unprocessed issues")
        
        # Process each unprocessed issue
        for issue in unprocessed_issues:
            logger.info(f"Processing issue #{issue.number}: {issue.title}")
            
            # Try to add comment to issue indicating we're working on it (optional)
            try:
                github_client.add_comment(
                    issue.number,
                    "🤖 Automated fix in progress. Claude Code is analyzing this issue..."
                )
            except Exception as e:
                logger.warning(f"Could not add start comment to issue #{issue.number}: {e}")
                logger.info("Continuing with issue processing despite comment failure")
            
            # Execute Claude Code to fix the issue
            success, message = claude_executor.execute_issue_fix(
                repo_url=Config.get_repo_url(),
                issue_number=issue.number,
                issue_title=issue.title,
                issue_body=issue.body or ""
            )
            
            if success:
                logger.info(f"Successfully processed issue #{issue.number}")
                
                # Try to add success comment and close issue (optional)
                try:
                    github_client.add_comment(
                        issue.number,
                        f"✅ Automated fix completed! {message}"
                    )
                except Exception as e:
                    logger.warning(f"Could not add success comment to issue #{issue.number}: {e}")
                
                try:
                    github_client.close_issue(
                        issue.number,
                        "🤖 Issue automatically resolved by Claude Code automation."
                    )
                except Exception as e:
                    logger.warning(f"Could not close issue #{issue.number}: {e}")
                    logger.info("Issue was processed successfully but remains open due to permissions")
                
            else:
                logger.error(f"Failed to process issue #{issue.number}: {message}")
                
                # Try to add failure comment (optional)
                try:
                    github_client.add_comment(
                        issue.number,
                        f"❌ Automated fix failed: {message}\n\nPlease review and fix manually."
                    )
                except Exception as e:
                    logger.warning(f"Could not add failure comment to issue #{issue.number}: {e}")
            
            # Mark as processed regardless of success/failure
            issue_tracker.mark_processed(issue.number)
        
        # Cleanup
        claude_executor.cleanup()
        
    except Exception as e:
        logger.error(f"Error in process_new_issues: {e}")

def check_claude_authentication():
    """Check if Claude Code is authenticated using headless mode"""
    logger = logging.getLogger(__name__)
    
    try:
        # Test authentication by running a simple headless command
        result = subprocess.run([
            'claude', '--print', 'Hello, this is an authentication test.',
            '--output-format', 'json'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("✅ Claude Code is authenticated and working in headless mode")
            return True
        else:
            # Check if it's an authentication error
            error_output = result.stderr.lower()
            if 'auth' in error_output or 'login' in error_output or 'unauthenticated' in error_output:
                logger.info("❌ Claude Code not authenticated, providing authentication instructions...")
                
                # Provide clear authentication instructions
                logger.info("=" * 60)
                logger.info("🔐 CLAUDE CODE AUTHENTICATION REQUIRED")
                logger.info("=" * 60)
                logger.info("To authenticate Claude Code in Railway:")
                logger.info("")
                logger.info("1. 🚀 Use Railway CLI to access shell:")
                logger.info("   railway shell")
                logger.info("")
                logger.info("2. 🔑 Run authentication in the shell:")
                logger.info("   claude")
                logger.info("   /login")
                logger.info("")
                logger.info("3. 📋 Copy the authentication URL and open in browser")
                logger.info("4. 🔄 Restart this Railway service after authentication")
                logger.info("")
                logger.info("💡 Alternative: Check Railway dashboard for 'Shell' or 'Console' tab")
                logger.info("=" * 60)
                
                return False
            else:
                logger.error(f"❌ Claude Code error (not authentication): {result.stderr}")
                return False
                
    except subprocess.TimeoutExpired:
        logger.error("⏰ Claude Code authentication check timed out")
        return False
    except FileNotFoundError:
        logger.error("❌ Claude Code CLI not found. Please install it first.")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking Claude Code authentication: {e}")
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
        logger.info(f"Currently tracking {issue_tracker.get_processed_count()} processed issues")
        
        # Schedule the job
        schedule.every(Config.POLL_INTERVAL_MINUTES).minutes.do(process_new_issues)
        
        # Schedule daily cleanup of old processed issues
        schedule.every().day.at("02:00").do(lambda: issue_tracker.cleanup_old_issues())
        
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