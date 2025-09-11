import os
import subprocess
import logging
import tempfile
import shutil
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class ClaudeExecutor:
    def __init__(self, work_dir: str = None):
        self.work_dir = work_dir or tempfile.mkdtemp(prefix='claude_automation_')
        
    def execute_issue_fix(self, repo_url: str, issue_number: int, issue_title: str, issue_body: str) -> Tuple[bool, str]:
        """
        Execute Claude Code to fix an issue:
        1. Clone repo to new branch
        2. Ask Claude to fix the issue
        3. Create PR
        """
        try:
            # Create a temporary directory for this specific issue
            issue_work_dir = os.path.join(self.work_dir, f"issue_{issue_number}")
            os.makedirs(issue_work_dir, exist_ok=True)
            
            # Clone the repository
            clone_success, clone_msg = self._clone_repo(repo_url, issue_work_dir)
            if not clone_success:
                return False, f"Failed to clone repository: {clone_msg}"
            
            # Change to repo directory
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            repo_path = os.path.join(issue_work_dir, repo_name)
            
            # Create and checkout new branch
            branch_name = f"fix-issue-{issue_number}"
            branch_success, branch_msg = self._create_branch(repo_path, branch_name)
            if not branch_success:
                return False, f"Failed to create branch: {branch_msg}"
            
            # Execute Claude Code to fix the issue
            fix_prompt = self._build_fix_prompt(issue_number, issue_title, issue_body)
            fix_success, fix_msg = self._run_claude_code(repo_path, fix_prompt)
            if not fix_success:
                return False, f"Claude Code execution failed: {fix_msg}"
            
            # Create PR
            pr_success, pr_msg = self._create_pr(repo_path, branch_name, issue_number, issue_title)
            if not pr_success:
                return False, f"Failed to create PR: {pr_msg}"
            
            return True, f"Successfully processed issue #{issue_number}. {pr_msg}"
            
        except Exception as e:
            logger.error(f"Error executing issue fix: {e}")
            return False, str(e)
        finally:
            # Cleanup
            if os.path.exists(issue_work_dir):
                shutil.rmtree(issue_work_dir, ignore_errors=True)
    
    def _clone_repo(self, repo_url: str, work_dir: str) -> Tuple[bool, str]:
        """Clone repository"""
        try:
            cmd = ['git', 'clone', repo_url]
            result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return True, "Repository cloned successfully"
            else:
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            return False, "Clone operation timed out"
        except Exception as e:
            return False, str(e)
    
    def _create_branch(self, repo_path: str, branch_name: str) -> Tuple[bool, str]:
        """Create and checkout new branch"""
        try:
            # Create and checkout branch
            cmd = ['git', 'checkout', '-b', branch_name]
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f"Created branch {branch_name}"
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, str(e)
    
    def _build_fix_prompt(self, issue_number: int, issue_title: str, issue_body: str) -> str:
        """Build prompt for Claude Code"""
        return f"""Please help fix GitHub issue #{issue_number}: {issue_title}

Issue description:
{issue_body}

Please:
1. Analyze the issue and understand what needs to be fixed
2. Implement the necessary changes
3. Make sure the code follows best practices
4. Run any tests if available
5. Commit your changes with a descriptive message

Make sure to commit all changes when you're done."""
    
    def _run_claude_code(self, repo_path: str, prompt: str) -> Tuple[bool, str]:
        """Execute Claude Code with the fix prompt"""
        try:
            # Write prompt to temporary file
            prompt_file = os.path.join(repo_path, '.claude_prompt.txt')
            with open(prompt_file, 'w') as f:
                f.write(prompt)
            
            # Run Claude Code in non-interactive mode
            cmd = ['claude', 'code', '--non-interactive', '--prompt-file', '.claude_prompt.txt']
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=1800)
            
            # Clean up prompt file
            os.remove(prompt_file)
            
            if result.returncode == 0:
                return True, "Claude Code executed successfully"
            else:
                return False, f"Claude Code failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Claude Code execution timed out"
        except Exception as e:
            return False, str(e)
    
    def _create_pr(self, repo_path: str, branch_name: str, issue_number: int, issue_title: str) -> Tuple[bool, str]:
        """Push branch and create PR"""
        try:
            # Push branch
            push_cmd = ['git', 'push', '-u', 'origin', branch_name]
            push_result = subprocess.run(push_cmd, cwd=repo_path, capture_output=True, text=True)
            
            if push_result.returncode != 0:
                return False, f"Failed to push branch: {push_result.stderr}"
            
            # Create PR using GitHub CLI
            pr_title = f"Fix: {issue_title} (#{issue_number})"
            pr_body = f"Automated fix for issue #{issue_number}\n\nCloses #{issue_number}"
            
            pr_cmd = ['gh', 'pr', 'create', '--title', pr_title, '--body', pr_body]
            pr_result = subprocess.run(pr_cmd, cwd=repo_path, capture_output=True, text=True)
            
            if pr_result.returncode == 0:
                return True, f"Created PR: {pr_result.stdout.strip()}"
            else:
                return False, f"Failed to create PR: {pr_result.stderr}"
                
        except Exception as e:
            return False, str(e)
    
    def cleanup(self):
        """Clean up work directory"""
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir, ignore_errors=True)