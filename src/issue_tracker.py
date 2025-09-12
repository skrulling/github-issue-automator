import os
import json
import logging
import time
from typing import Set, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class IssueTracker:
    """Track processed GitHub issues and failed attempts with backoff"""
    
    def __init__(self, storage_path: str = "data/processed_issues.json"):
        self.storage_path = Path(storage_path)
        self.processed_issues: Set[int] = set()
        self.failed_attempts: Dict[int, Dict] = {}  # issue_number -> {count, last_attempt, next_retry}
        self._ensure_storage_dir()
        self._load_processed_issues()
    
    def _ensure_storage_dir(self):
        """Ensure the storage directory exists"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_processed_issues(self):
        """Load processed issue IDs and failed attempts from storage file"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.processed_issues = set(data.get('processed_issues', []))
                    self.failed_attempts = data.get('failed_attempts', {})
                    # Convert string keys back to int
                    self.failed_attempts = {int(k): v for k, v in self.failed_attempts.items()}
                    logger.info(f"Loaded {len(self.processed_issues)} processed issues and {len(self.failed_attempts)} failed attempts")
            else:
                logger.info("No previous issue tracking file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading processed issues: {e}")
            self.processed_issues = set()
            self.failed_attempts = {}
    
    def _save_processed_issues(self):
        """Save processed issue IDs and failed attempts to storage file"""
        try:
            data = {
                'processed_issues': sorted(list(self.processed_issues)),
                'failed_attempts': {str(k): v for k, v in self.failed_attempts.items()},
                'last_updated': time.time()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.processed_issues)} processed issues and {len(self.failed_attempts)} failed attempts")
        except Exception as e:
            logger.error(f"Error saving processed issues: {e}")
    
    def is_processed(self, issue_number: int) -> bool:
        """Check if an issue has already been processed"""
        return issue_number in self.processed_issues
    
    def should_retry_issue(self, issue_number: int) -> bool:
        """Check if a failed issue should be retried based on backoff"""
        if issue_number in self.processed_issues:
            return False  # Already successfully processed
        
        if issue_number not in self.failed_attempts:
            return True  # Never attempted before
        
        failure_info = self.failed_attempts[issue_number]
        next_retry = failure_info.get('next_retry', 0)
        current_time = time.time()
        
        if current_time >= next_retry:
            return True  # Backoff period has passed
        
        return False  # Still in backoff period
    
    def mark_processed(self, issue_number: int):
        """Mark an issue as successfully processed"""
        if issue_number not in self.processed_issues:
            self.processed_issues.add(issue_number)
            # Remove from failed attempts if it was there
            if issue_number in self.failed_attempts:
                del self.failed_attempts[issue_number]
            self._save_processed_issues()
            logger.info(f"Marked issue #{issue_number} as processed")
    
    def mark_failed(self, issue_number: int):
        """Mark an issue as failed with exponential backoff"""
        current_time = time.time()
        
        if issue_number in self.failed_attempts:
            # Increment failure count
            self.failed_attempts[issue_number]['count'] += 1
            failure_count = self.failed_attempts[issue_number]['count']
        else:
            # First failure
            failure_count = 1
            self.failed_attempts[issue_number] = {'count': failure_count}
        
        # Exponential backoff: 5 min, 15 min, 45 min, 2 hours, 6 hours, then 24 hours
        backoff_minutes = min(5 * (3 ** (failure_count - 1)), 1440)  # Max 24 hours
        next_retry = current_time + (backoff_minutes * 60)
        
        self.failed_attempts[issue_number].update({
            'last_attempt': current_time,
            'next_retry': next_retry,
            'backoff_minutes': backoff_minutes
        })
        
        self._save_processed_issues()
        logger.info(f"Marked issue #{issue_number} as failed (attempt {failure_count}). Next retry in {backoff_minutes} minutes")
    
    def get_processed_count(self) -> int:
        """Get the count of processed issues"""
        return len(self.processed_issues)
    
    def cleanup_old_issues(self, keep_last: int = 1000):
        """Keep only the most recent N processed issues to prevent file from growing too large"""
        if len(self.processed_issues) > keep_last:
            # Keep the highest issue numbers (most recent)
            sorted_issues = sorted(self.processed_issues, reverse=True)
            self.processed_issues = set(sorted_issues[:keep_last])
            self._save_processed_issues()
            logger.info(f"Cleaned up old issues, now tracking {len(self.processed_issues)} issues")