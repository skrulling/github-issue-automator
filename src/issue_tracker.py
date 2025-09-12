import os
import json
import logging
from typing import Set, List
from pathlib import Path

logger = logging.getLogger(__name__)

class IssueTracker:
    """Track processed GitHub issues to avoid duplicates"""
    
    def __init__(self, storage_path: str = "data/processed_issues.json"):
        self.storage_path = Path(storage_path)
        self.processed_issues: Set[int] = set()
        self._ensure_storage_dir()
        self._load_processed_issues()
    
    def _ensure_storage_dir(self):
        """Ensure the storage directory exists"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_processed_issues(self):
        """Load processed issue IDs from storage file"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.processed_issues = set(data.get('processed_issues', []))
                    logger.info(f"Loaded {len(self.processed_issues)} previously processed issues")
            else:
                logger.info("No previous issue tracking file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading processed issues: {e}")
            self.processed_issues = set()
    
    def _save_processed_issues(self):
        """Save processed issue IDs to storage file"""
        try:
            data = {
                'processed_issues': sorted(list(self.processed_issues)),
                'last_updated': str(Path().resolve())
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.processed_issues)} processed issues to {self.storage_path}")
        except Exception as e:
            logger.error(f"Error saving processed issues: {e}")
    
    def is_processed(self, issue_number: int) -> bool:
        """Check if an issue has already been processed"""
        return issue_number in self.processed_issues
    
    def mark_processed(self, issue_number: int):
        """Mark an issue as processed"""
        if issue_number not in self.processed_issues:
            self.processed_issues.add(issue_number)
            self._save_processed_issues()
            logger.info(f"Marked issue #{issue_number} as processed")
    
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