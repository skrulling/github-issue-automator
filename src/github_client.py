import os
import logging
from datetime import datetime, timedelta
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
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes_back)
            
            # Get recent issues
            issues = self.repo.get_issues(
                state='open',
                sort='created',
                direction='desc'
            )
            
            recent_issues = []
            for issue in issues:
                # Check if issue is recent and by target user
                if (issue.created_at >= cutoff_time and 
                    issue.user.login == username and
                    not issue.pull_request):  # Exclude PRs
                    recent_issues.append(issue)
                    logger.info(f"Found new issue #{issue.number}: {issue.title} by {issue.user.login}")
                elif issue.created_at < cutoff_time:
                    # Issues are sorted by creation date, so we can break early
                    break
                    
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