import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from github import Github
from github.Issue import Issue

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: str, repo_owner: str, repo_name: str):
        self.github = Github(token)
        self.repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        
    def get_recent_issues_by_user(self, username: str, minutes_back: int = 5) -> List[Issue]:
        """Get issues created by a specific user in the last N minutes"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_back)
            
            # Get recent issues
            issues = self.repo.get_issues(
                state='open',
                sort='created',
                direction='desc'
            )
            
            recent_issues = []
            issue_count = 0
            
            for issue in issues:
                issue_count += 1
                logger.debug(f"Checking issue #{issue.number}: {issue.title} by {issue.user.login}")
                logger.debug(f"Issue created at: {issue.created_at}, Cutoff: {cutoff_time}")
                
                # Ensure both datetimes are timezone-aware for comparison
                issue_created_at = issue.created_at
                if issue_created_at.tzinfo is None:
                    issue_created_at = issue_created_at.replace(tzinfo=timezone.utc)
                
                # Check if issue is recent and by target user
                if (issue_created_at >= cutoff_time and 
                    issue.user.login == username and
                    not issue.pull_request):  # Exclude PRs
                    recent_issues.append(issue)
                    logger.info(f"Found new issue #{issue.number}: {issue.title} by {issue.user.login}")
                elif issue_created_at < cutoff_time:
                    # Issues are sorted by creation date, so we can break early
                    logger.debug(f"Issue #{issue.number} is older than cutoff, stopping search")
                    break
                    
                # Limit to checking first 50 issues to avoid API rate limits
                if issue_count >= 50:
                    logger.info("Checked 50 issues, stopping to avoid rate limits")
                    break
            
            logger.info(f"Checked {issue_count} issues, found {len(recent_issues)} by user '{username}' in last {minutes_back} minutes")
            return recent_issues
            
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            return []
    
    def close_issue(self, issue_number: int, comment: str = None) -> bool:
        """Close an issue with optional comment"""
        try:
            issue = self.repo.get_issue(issue_number)
            
            if comment:
                issue.create_comment(comment)
            
            issue.edit(state='closed')
            logger.info(f"Closed issue #{issue_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing issue #{issue_number}: {e}")
            return False
    
    def add_comment(self, issue_number: int, comment: str) -> bool:
        """Add a comment to an issue"""
        try:
            issue = self.repo.get_issue(issue_number)
            issue.create_comment(comment)
            logger.info(f"Added comment to issue #{issue_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding comment to issue #{issue_number}: {e}")
            return False