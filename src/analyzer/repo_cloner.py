"""
Repository Cloner Module
Handles cloning GitHub repositories for analysis
"""

import git
import os
import shutil
import re
from typing import Optional, Dict
from urllib.parse import urlparse, urlunparse
import logging

logger = logging.getLogger(__name__)


class GitHubURLError(Exception):
    """Exception raised for invalid GitHub URLs"""
    pass


class GitAuthenticationError(Exception):
    """Exception raised for Git authentication failures"""
    pass


class RepoCloner:
    """Handles GitHub repository cloning operations"""
    
    # GitHub URL patterns
    GITHUB_HTTPS_PATTERN = re.compile(
        r'^https?://github\.com/[\w\-\.]+/[\w\-\.]+/?(?:\.git)?$'
    )
    GITHUB_SSH_PATTERN = re.compile(
        r'^git@github\.com:[\w\-\.]+/[\w\-\.]+\.git$'
    )
    
    def __init__(self, clone_dir: str = "data/repos"):
        """
        Initialize repository cloner
        
        Args:
            clone_dir: Directory to clone repositories into
        """
        self.clone_dir = clone_dir
        os.makedirs(clone_dir, exist_ok=True)
    
    def validate_github_url(self, url: str) -> bool:
        """
        Validate if the URL is a valid GitHub repository URL
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            GitHubURLError: If URL is invalid
        """
        if not url or not isinstance(url, str):
            raise GitHubURLError("URL must be a non-empty string")
        
        url = url.strip()
        
        # Check HTTPS pattern
        if self.GITHUB_HTTPS_PATTERN.match(url):
            return True
        
        # Check SSH pattern
        if self.GITHUB_SSH_PATTERN.match(url):
            return True
        
        raise GitHubURLError(
            f"Invalid GitHub URL: {url}. "
            "Expected format: https://github.com/owner/repo or git@github.com:owner/repo.git"
        )
    
    def normalize_github_url(self, url: str, token: Optional[str] = None) -> str:
        """
        Normalize GitHub URL and add authentication if token provided
        
        Args:
            url: GitHub repository URL
            token: Optional GitHub personal access token
            
        Returns:
            Normalized URL with authentication if token provided
        """
        url = url.strip().rstrip('/')
        
        # Convert SSH to HTTPS if needed
        if url.startswith('git@github.com:'):
            url = url.replace('git@github.com:', 'https://github.com/')
        
        # Ensure .git suffix
        if not url.endswith('.git'):
            url += '.git'
        
        # Add token authentication if provided
        if token:
            parsed = urlparse(url)
            # Insert token into URL: https://token@github.com/...
            netloc = f"{token}@{parsed.netloc}"
            url = urlunparse((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
        
        return url
    
    def extract_repo_name(self, url: str) -> str:
        """
        Extract repository name from GitHub URL
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Repository name
        """
        # Remove .git suffix
        url = url.rstrip('/').replace('.git', '')
        
        # Extract last part of path
        if 'github.com/' in url:
            parts = url.split('github.com/')[-1].split('/')
            if len(parts) >= 2:
                return f"{parts[0]}_{parts[1]}"
        
        # Fallback: use last part
        return url.split('/')[-1]
    
    def clone_repository(
        self, 
        repo_url: str, 
        token: Optional[str] = None,
        repo_name: Optional[str] = None,
        depth: Optional[int] = None
    ) -> str:
        """
        Clone a GitHub repository with authentication support
        
        Args:
            repo_url: URL of the GitHub repository
            token: Optional GitHub personal access token for private repos
            repo_name: Optional custom name for the cloned directory
            depth: Optional shallow clone depth (None for full clone)
            
        Returns:
            Path to the cloned repository
            
        Raises:
            GitHubURLError: If URL is invalid
            GitAuthenticationError: If authentication fails
            Exception: For other cloning errors
        """
        try:
            # Validate URL
            self.validate_github_url(repo_url)
            
            # Normalize URL with authentication
            clone_url = self.normalize_github_url(repo_url, token)
            
            # Extract repo name from URL if not provided
            if not repo_name:
                repo_name = self.extract_repo_name(repo_url)
            
            # Create full path for clone
            clone_path = os.path.join(self.clone_dir, repo_name)
            
            # Remove existing directory if it exists
            if os.path.exists(clone_path):
                logger.warning(f"Directory {clone_path} already exists. Removing...")
                self.cleanup_repository(clone_path)
            
            # Prepare clone options
            clone_kwargs = {}
            if depth:
                clone_kwargs['depth'] = depth
            
            # Clone the repository
            logger.info(f"Cloning repository to {clone_path}")
            git.Repo.clone_from(clone_url, clone_path, **clone_kwargs)
            logger.info(f"Successfully cloned repository to {clone_path}")
            
            return clone_path
        
        except git.exc.GitCommandError as e:
            error_msg = str(e).lower()
            if 'authentication' in error_msg or 'permission denied' in error_msg or '403' in error_msg:
                raise GitAuthenticationError(
                    f"Authentication failed for {repo_url}. "
                    "Please check your token or repository access permissions."
                ) from e
            elif 'not found' in error_msg or '404' in error_msg:
                raise GitHubURLError(
                    f"Repository not found: {repo_url}. "
                    "Please check the URL or your access permissions."
                ) from e
            elif 'network' in error_msg or 'connection' in error_msg:
                raise ConnectionError(
                    f"Network error while cloning {repo_url}. "
                    "Please check your internet connection."
                ) from e
            else:
                logger.error(f"Git command error cloning repository {repo_url}: {str(e)}")
                raise
        
        except GitHubURLError:
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error cloning repository {repo_url}: {str(e)}")
            raise
    
    def get_repo_info(self, repo_path: str) -> Dict:
        """
        Get information about a cloned repository
        
        Args:
            repo_path: Path to the cloned repository
            
        Returns:
            Dictionary with repository information
        """
        try:
            repo = git.Repo(repo_path)
            
            info = {
                'path': repo_path,
                'active_branch': repo.active_branch.name,
                'remote_url': repo.remotes.origin.url if repo.remotes else None,
                'last_commit': {
                    'hash': repo.head.commit.hexsha,
                    'author': str(repo.head.commit.author),
                    'date': repo.head.commit.committed_datetime.isoformat(),
                    'message': repo.head.commit.message.strip()
                },
                'total_commits': len(list(repo.iter_commits())),
                'branches': [branch.name for branch in repo.branches]
            }
            
            return info
        
        except Exception as e:
            logger.error(f"Error getting repo info for {repo_path}: {str(e)}")
            raise
    
    def cleanup_repository(self, repo_path: str):
        """
        Remove a cloned repository
        
        Args:
            repo_path: Path to the repository to remove
        """
        try:
            if os.path.exists(repo_path):
                # Handle Windows file permission issues
                def handle_remove_readonly(func, path, exc):
                    """Error handler for Windows readonly files"""
                    os.chmod(path, 0o777)
                    func(path)
                
                shutil.rmtree(repo_path, onerror=handle_remove_readonly)
                logger.info(f"Removed repository at {repo_path}")
            else:
                logger.warning(f"Repository path does not exist: {repo_path}")
        except Exception as e:
            logger.error(f"Error removing repository {repo_path}: {str(e)}")
            raise
    
    def cleanup_all(self):
        """Remove all cloned repositories"""
        try:
            if os.path.exists(self.clone_dir):
                # Handle Windows file permission issues
                def handle_remove_readonly(func, path, exc):
                    """Error handler for Windows readonly files"""
                    os.chmod(path, 0o777)
                    func(path)
                
                shutil.rmtree(self.clone_dir, onerror=handle_remove_readonly)
                os.makedirs(self.clone_dir, exist_ok=True)
                logger.info("Cleaned up all cloned repositories")
        except Exception as e:
            logger.error(f"Error cleaning up repositories: {str(e)}")
            raise
    
    def is_repository_cloned(self, repo_name: str) -> bool:
        """
        Check if a repository is already cloned
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            True if repository exists, False otherwise
        """
        repo_path = os.path.join(self.clone_dir, repo_name)
        return os.path.exists(repo_path) and os.path.isdir(repo_path)
    
    def get_cloned_repositories(self) -> list:
        """
        Get list of all cloned repositories
        
        Returns:
            List of repository names
        """
        try:
            if not os.path.exists(self.clone_dir):
                return []
            
            return [
                d for d in os.listdir(self.clone_dir)
                if os.path.isdir(os.path.join(self.clone_dir, d))
            ]
        except Exception as e:
            logger.error(f"Error listing cloned repositories: {str(e)}")
            return []

# Made with Bob
