import os
import subprocess
import logging
import tempfile
import shutil
import json
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
        """Build intelligent system prompt for Claude Code with comprehensive project analysis"""
        return f"""You are an expert software engineer working on GitHub issue #{issue_number}: {issue_title}

## Issue Details
{issue_body}

## Your Mission
Fix this issue by following a systematic, intelligent approach. You have full access to all development tools and should work autonomously.

## Step 1: Project Discovery & Context Analysis
Before making any changes, thoroughly understand the project:

1. **Project Structure Analysis**:
   - Read package.json to understand the tech stack, scripts, and dependencies
   - Check README.md for project documentation and setup instructions
   - Examine .gitignore, tsconfig.json, next.config.js for configuration
   - Look for documentation in docs/ or similar folders

2. **Codebase Architecture**:
   - Explore the src/ or app/ directory structure
   - Identify routing patterns (pages/ vs app/ directory)
   - Find component patterns and naming conventions
   - Check for state management (Redux, Zustand, Context, etc.)
   - Look for styling approach (CSS modules, Tailwind, styled-components, etc.)

3. **Related Code Discovery**:
   - Use Grep to search for keywords from the issue across the codebase
   - Find similar components or features that might be affected
   - Locate test files related to the issue area
   - Check for existing error handling patterns

## Step 2: Contextual Research
4. **External Research** (when needed):
   - Use WebSearch for Next.js best practices related to the issue
   - Look up documentation for any unfamiliar libraries or APIs
   - Research similar problems and solutions in the community

## Step 3: Implementation Strategy
5. **Plan Before Coding**:
   - Identify all files that need modification
   - Consider backward compatibility and breaking changes
   - Plan for proper TypeScript types if applicable
   - Think about responsive design and accessibility implications

6. **Smart Implementation**:
   - Follow the project's existing patterns and conventions exactly
   - Match the coding style, naming conventions, and file organization
   - Use the same libraries and approaches already in the project
   - Ensure consistency with existing error handling and validation

## Step 4: Quality Assurance
7. **Comprehensive Testing**:
   - Run existing tests: npm test, npm run test:unit, yarn test, etc.
   - Run linting: npm run lint, yarn lint, etc.
   - Run type checking: npm run type-check, tsc --noEmit, etc.
   - Try building the project: npm run build, yarn build, etc.
   - Test the actual functionality you implemented

8. **Code Review Yourself**:
   - Double-check your changes for potential issues
   - Ensure no console.log or debug code remains
   - Verify proper error boundaries and edge cases
   - Check for accessibility compliance (ARIA labels, keyboard navigation, etc.)

## Step 5: Professional Delivery
9. **Clean Commit**:
   - Stage only the necessary files
   - Write a clear, descriptive commit message
   - Include the issue number in your commit: "fix: resolve issue #{issue_number} - [brief description]"

## Available Tools:
- **Bash**: Run any command (git, npm, yarn, tests, builds, etc.)
- **Read/Edit/Write/MultiEdit**: File operations
- **Glob/Grep**: Search and discovery
- **WebFetch/WebSearch**: Research and documentation lookup

## Success Criteria:
- Issue is completely resolved
- All existing tests pass
- Code follows project conventions
- No breaking changes unless explicitly required
- Proper TypeScript types (if applicable)
- Accessible and responsive (for UI changes)
- Clean, professional commit

Start by exploring the project structure and understanding the codebase before making any changes. Be methodical, thorough, and professional in your approach."""
    
    def _run_claude_code(self, repo_path: str, prompt: str) -> Tuple[bool, str]:
        """Execute Claude Code using headless SDK"""
        try:
            # Create enhanced system prompt
            system_prompt = """You are an expert software engineer specializing in Next.js, React, and TypeScript. 

Key principles:
- Always explore and understand the project structure before making changes
- Follow existing code patterns, naming conventions, and architectural decisions
- Research best practices when implementing new features
- Test thoroughly and ensure backward compatibility
- Write clean, maintainable code with proper error handling
- Consider accessibility and responsive design for UI changes

Your goal is to deliver production-quality code that seamlessly integrates with the existing project."""

            # Run Claude Code in headless mode with comprehensive permissions for Next.js development
            cmd = [
                'claude', 
                '--print', prompt,
                '--output-format', 'json',
                '--allowedTools', 'Bash', 'Read', 'Edit', 'Write', 'MultiEdit', 'Glob', 'Grep', 'WebFetch', 'WebSearch',
                '--append-system-prompt', system_prompt
            ]
            
            logger.info("Executing Claude Code in headless mode...")
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=1800)
            
            if result.returncode == 0:
                # Parse JSON response to get execution details
                try:
                    response_data = json.loads(result.stdout)
                    
                    # Log execution details
                    if 'content' in response_data:
                        logger.info(f"Claude Code response: {response_data['content'][:200]}...")
                    
                    if 'cost' in response_data:
                        logger.info(f"Execution cost: {response_data['cost']}")
                        
                    return True, "Claude Code executed successfully"
                    
                except json.JSONDecodeError:
                    # If not JSON, treat as success anyway
                    logger.info("Claude Code executed successfully (non-JSON response)")
                    return True, "Claude Code executed successfully"
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"Claude Code failed: {error_msg}")
                return False, f"Claude Code failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            logger.error("Claude Code execution timed out")
            return False, "Claude Code execution timed out"
        except Exception as e:
            logger.error(f"Error executing Claude Code: {e}")
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