#!/usr/bin/env python3

import time
import logging
import schedule
from typing import Set

from config import Config
from logger import setup_logging
from github_client import GitHubClient
from claude_executor import ClaudeExecutor

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

def main():
    """Main application entry point"""
    try:
        # Validate configuration
        Config.validate()
        
        # Setup logging
        logger = setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)
        logger.info("GitHub Issue Automator starting...")
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