import os
import subprocess
import logging
import shutil
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

class RepositoryManager:
    """Manage persistent repository for issue processing"""
    
    def __init__(self, repo_url: str, github_token: str, repo_dir: str = "/app/repo"):
        self.repo_url = repo_url
        self.github_token = github_token
        self.repo_dir = Path(repo_dir)
        self.current_branch = None
        
        # Convert HTTPS URL to use token authentication
        self.auth_repo_url = self._get_authenticated_url(repo_url, github_token)
    
    def _get_authenticated_url(self, repo_url: str, token: str) -> str:
        """Convert GitHub URL to use token authentication"""
        if repo_url.startswith('https://github.com/'):
            # Convert https://github.com/owner/repo.git to https://token@github.com/owner/repo.git
            return repo_url.replace('https://github.com/', f'https://{token}@github.com/')
        return repo_url
        
    def initialize_repo(self) -> Tuple[bool, str]:
        """Clone repository if not exists, or validate existing repo"""
        try:
            if self.repo_dir.exists():
                # Check if it's a valid git repo
                result = subprocess.run(
                    ['git', 'rev-parse', '--git-dir'],
                    cwd=self.repo_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"Using existing repository at {self.repo_dir}")
                    return self._update_repo()
                else:
                    logger.warning(f"Invalid git repo at {self.repo_dir}, removing and cloning fresh")
                    shutil.rmtree(self.repo_dir)
            
            # Clone fresh repository using authenticated URL
            logger.info(f"Cloning repository {self.repo_url} to {self.repo_dir}")
            self.repo_dir.parent.mkdir(parents=True, exist_ok=True)
            
            result = subprocess.run(
                ['git', 'clone', self.auth_repo_url, str(self.repo_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("Repository cloned successfully")
                
                # Set remote URL to use authenticated URL for pushes
                subprocess.run(
                    ['git', 'remote', 'set-url', 'origin', self.auth_repo_url],
                    cwd=self.repo_dir,
                    capture_output=True
                )
                
                return True, "Repository initialized"
            else:
                logger.error(f"Failed to clone repository: {result.stderr}")
                return False, f"Clone failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Repository clone timed out"
        except Exception as e:
            logger.error(f"Error initializing repository: {e}")
            return False, str(e)
    
    def _update_repo(self) -> Tuple[bool, str]:
        """Fetch latest changes from remote"""
        try:
            # Ensure remote URL uses authentication
            subprocess.run(
                ['git', 'remote', 'set-url', 'origin', self.auth_repo_url],
                cwd=self.repo_dir,
                capture_output=True
            )
            
            # Ensure we're on main branch
            subprocess.run(['git', 'checkout', 'main'], cwd=self.repo_dir, check=True, capture_output=True)
            
            # Fetch latest changes
            result = subprocess.run(
                ['git', 'fetch', 'origin'],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("Repository updated from remote")
                return True, "Repository updated"
            else:
                logger.warning(f"Failed to fetch from remote: {result.stderr}")
                return True, "Using existing repository (fetch failed)"
                
        except Exception as e:
            logger.error(f"Error updating repository: {e}")
            return True, f"Using existing repository (update failed: {e})"
    
    def prepare_for_issue(self, issue_number: int) -> Tuple[bool, str]:
        """Prepare repository for working on a specific issue"""
        try:
            branch_name = f"fix-issue-{issue_number}"
            
            # Ensure we're in the repo directory
            if not self.repo_dir.exists():
                return False, "Repository not initialized"
            
            # Clean up any existing work
            subprocess.run(['git', 'reset', '--hard'], cwd=self.repo_dir, capture_output=True)
            subprocess.run(['git', 'clean', '-fd'], cwd=self.repo_dir, capture_output=True)
            
            # Switch to main branch
            result = subprocess.run(
                ['git', 'checkout', 'main'],
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return False, f"Failed to checkout main: {result.stderr}"
            
            # Pull latest changes
            result = subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to pull latest changes: {result.stderr}")
                # Continue anyway - maybe we're offline or have local changes
            
            # Delete branch if it exists
            subprocess.run(
                ['git', 'branch', '-D', branch_name],
                cwd=self.repo_dir,
                capture_output=True
            )
            
            # Create and checkout new branch
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.current_branch = branch_name
                logger.info(f"Created and switched to branch: {branch_name}")
                return True, f"Branch {branch_name} ready"
            else:
                return False, f"Failed to create branch: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error preparing repository for issue #{issue_number}: {e}")
            return False, str(e)
    
    def cleanup_after_issue(self, success: bool) -> Tuple[bool, str]:
        """Clean up repository after processing an issue"""
        try:
            if not self.repo_dir.exists():
                return True, "Repository not found"
            
            # Switch back to main
            result = subprocess.run(
                ['git', 'checkout', 'main'],
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            
            # If we had a current branch and the issue failed, delete the branch
            if self.current_branch and not success:
                subprocess.run(
                    ['git', 'branch', '-D', self.current_branch],
                    cwd=self.repo_dir,
                    capture_output=True
                )
                logger.info(f"Deleted failed branch: {self.current_branch}")
            
            # Clean up any uncommitted changes
            subprocess.run(['git', 'reset', '--hard'], cwd=self.repo_dir, capture_output=True)
            subprocess.run(['git', 'clean', '-fd'], cwd=self.repo_dir, capture_output=True)
            
            self.current_branch = None
            return True, "Repository cleaned up"
            
        except Exception as e:
            logger.error(f"Error cleaning up repository: {e}")
            return False, str(e)
    
    def get_repo_directory(self) -> str:
        """Get the repository directory path"""
        return str(self.repo_dir)
    
    def is_initialized(self) -> bool:
        """Check if repository is properly initialized"""
        try:
            if not self.repo_dir.exists():
                return False
            
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_dir,
                capture_output=True
            )
            
            return result.returncode == 0
        except:
            return False