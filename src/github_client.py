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
        
    def get_unprocessed_issues_by_user(self, username: str, processed_issues: set) -> List[Issue]:
        """Get unprocessed open issues created by a specific user"""
        try:
            # Get open issues by the target user
            issues = self.repo.get_issues(
                state='open',
                creator=username,
                sort='created',
                direction='desc'
            )
            
            unprocessed_issues = []
            issue_count = 0
            
            for issue in issues:
                issue_count += 1
                
                # Skip pull requests
                if issue.pull_request:
                    logger.debug(f"Skipping PR #{issue.number}")
                    continue
                
                # Check if already processed
                if issue.number in processed_issues:
                    logger.debug(f"Issue #{issue.number} already processed, skipping")
                    continue
                
                # This is an unprocessed issue by the target user
                unprocessed_issues.append(issue)
                logger.info(f"Found unprocessed issue #{issue.number}: {issue.title} by {issue.user.login}")
                
                # Limit to checking first 50 issues to avoid API rate limits
                if issue_count >= 50:
                    logger.info("Checked 50 issues, stopping to avoid rate limits")
                    break
            
            logger.info(f"Checked {issue_count} issues, found {len(unprocessed_issues)} unprocessed issues by user '{username}'")
            return unprocessed_issues
            
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