"""
Repository Analyzer Module
Main orchestrator for GitHub repository analysis
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Set
from datetime import datetime
import logging

from .repo_cloner import RepoCloner, GitHubURLError, GitAuthenticationError
from .file_parser import FileParser

logger = logging.getLogger(__name__)


class RepositoryAnalyzer:
    """
    Main analyzer that orchestrates repository cloning and file parsing
    """
    
    def __init__(self, clone_dir: str = "data/repos", cache_dir: str = "data/cache"):
        """
        Initialize repository analyzer
        
        Args:
            clone_dir: Directory to clone repositories into
            cache_dir: Directory to store analysis cache
        """
        self.repo_cloner = RepoCloner(clone_dir)
        self.file_parser = FileParser()
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self.analysis_results = {}
    
    def _get_cache_key(self, repo_url: str) -> str:
        """
        Generate cache key for a repository
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Cache key (hash of URL)
        """
        return hashlib.md5(repo_url.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """
        Get cache file path
        
        Args:
            cache_key: Cache key
            
        Returns:
            Path to cache file
        """
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _load_from_cache(self, repo_url: str, repo_path: str) -> Optional[Dict]:
        """
        Load analysis results from cache if available and valid
        
        Args:
            repo_url: Repository URL
            repo_path: Path to cloned repository
            
        Returns:
            Cached results or None if cache invalid/missing
        """
        try:
            cache_key = self._get_cache_key(repo_url)
            cache_path = self._get_cache_path(cache_key)
            
            if not os.path.exists(cache_path):
                return None
            
            # Load cache
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Verify cache is still valid (check last commit hash)
            repo_info = self.repo_cloner.get_repo_info(repo_path)
            if cached_data.get('repository', {}).get('last_commit', {}).get('hash') == \
               repo_info['last_commit']['hash']:
                logger.info(f"Using cached analysis for {repo_url}")
                return cached_data
            
            logger.info(f"Cache outdated for {repo_url}, re-analyzing")
            return None
        
        except Exception as e:
            logger.warning(f"Error loading cache: {str(e)}")
            return None
    
    def _save_to_cache(self, repo_url: str, results: Dict):
        """
        Save analysis results to cache
        
        Args:
            repo_url: Repository URL
            results: Analysis results
        """
        try:
            cache_key = self._get_cache_key(repo_url)
            cache_path = self._get_cache_path(cache_key)
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Saved analysis to cache: {cache_path}")
        
        except Exception as e:
            logger.warning(f"Error saving to cache: {str(e)}")
    
    def analyze_repository(
        self,
        github_url: str,
        token: Optional[str] = None,
        include_content: bool = True,
        include_line_numbers: bool = False,
        filter_languages: Optional[Set[str]] = None,
        use_cache: bool = True,
        shallow_clone: bool = False
    ) -> Dict:
        """
        Analyze a GitHub repository
        
        Args:
            github_url: GitHub repository URL
            token: Optional GitHub personal access token for private repos
            include_content: Whether to include file contents in results
            include_line_numbers: Whether to include line-by-line content
            filter_languages: Optional set of languages to filter by
            use_cache: Whether to use cached results if available
            shallow_clone: Whether to do shallow clone (faster, less history)
            
        Returns:
            Dictionary with complete analysis results
            
        Raises:
            GitHubURLError: If URL is invalid
            GitAuthenticationError: If authentication fails
            Exception: For other errors
        """
        start_time = datetime.now()
        logger.info(f"Starting analysis of repository: {github_url}")
        
        try:
            # Step 1: Clone repository
            logger.info("Step 1: Cloning repository...")
            depth = 1 if shallow_clone else None
            repo_path = self.repo_cloner.clone_repository(
                github_url,
                token=token,
                depth=depth
            )
            
            # Check cache if enabled
            if use_cache:
                cached_results = self._load_from_cache(github_url, repo_path)
                if cached_results:
                    return cached_results
            
            # Step 2: Get repository information
            logger.info("Step 2: Extracting repository metadata...")
            repo_info = self.repo_cloner.get_repo_info(repo_path)
            
            # Step 3: Scan repository for files
            logger.info("Step 3: Scanning repository files...")
            files_info = self.file_parser.scan_repository(repo_path)
            
            # Filter by language if specified
            if filter_languages:
                files_info = self.file_parser.filter_files_by_language(
                    files_info,
                    filter_languages
                )
                logger.info(f"Filtered to {len(files_info)} files matching languages: {filter_languages}")
            
            # Step 4: Get file statistics
            logger.info("Step 4: Calculating statistics...")
            stats = self.file_parser.get_file_statistics(repo_path)
            
            # Step 5: Parse files if content requested
            parsed_files = []
            if include_content:
                logger.info("Step 5: Parsing file contents...")
                file_paths = [f['path'] for f in files_info]
                parsed_files = self.file_parser.parse_files_batch(
                    file_paths,
                    include_line_numbers=include_line_numbers
                )
            
            # Build file tree structure
            logger.info("Step 6: Building file tree...")
            file_tree = self._build_file_tree(files_info, repo_path)
            
            # Compile results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results = {
                'analysis_metadata': {
                    'analyzed_at': end_time.isoformat(),
                    'duration_seconds': duration,
                    'github_url': github_url,
                    'shallow_clone': shallow_clone,
                    'cache_used': False
                },
                'repository': repo_info,
                'statistics': stats,
                'file_tree': file_tree,
                'files': files_info,
                'parsed_files': parsed_files if include_content else [],
                'parser_stats': self.file_parser.get_stats()
            }
            
            # Save to cache
            if use_cache:
                self._save_to_cache(github_url, results)
            
            # Store in memory
            self.analysis_results[github_url] = results
            
            logger.info(f"Analysis complete in {duration:.2f} seconds")
            logger.info(f"Found {len(files_info)} files, parsed {len(parsed_files)} files")
            
            return results
        
        except (GitHubURLError, GitAuthenticationError) as e:
            logger.error(f"Repository access error: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            raise
    
    def _build_file_tree(self, files_info: List[Dict], repo_path: str) -> Dict:
        """
        Build hierarchical file tree structure
        
        Args:
            files_info: List of file information
            repo_path: Repository root path
            
        Returns:
            Nested dictionary representing file tree
        """
        tree = {}
        
        for file_info in files_info:
            rel_path = file_info['relative_path']
            parts = rel_path.split(os.sep)
            
            current = tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # Leaf node (file)
                    current[part] = {
                        'type': 'file',
                        'language': file_info['language'],
                        'size': file_info['size'],
                        'extension': file_info['extension']
                    }
                else:
                    # Directory node
                    if part not in current:
                        current[part] = {'type': 'directory', 'children': {}}
                    current = current[part].get('children', current[part])
        
        return tree
    
    def get_analysis_summary(self, github_url: str) -> Optional[Dict]:
        """
        Get summary of analysis results
        
        Args:
            github_url: Repository URL
            
        Returns:
            Summary dictionary or None if not analyzed
        """
        if github_url not in self.analysis_results:
            return None
        
        results = self.analysis_results[github_url]
        
        return {
            'repository': results['repository']['remote_url'],
            'analyzed_at': results['analysis_metadata']['analyzed_at'],
            'duration': results['analysis_metadata']['duration_seconds'],
            'total_files': results['statistics']['total_files'],
            'total_size': results['statistics']['total_size'],
            'languages': results['statistics']['languages'],
            'files_parsed': results['parser_stats']['files_parsed'],
            'total_lines': results['parser_stats']['total_lines']
        }
    
    def cleanup_repository(self, github_url: str):
        """
        Clean up cloned repository
        
        Args:
            github_url: Repository URL
        """
        try:
            repo_name = self.repo_cloner.extract_repo_name(github_url)
            repo_path = os.path.join(self.repo_cloner.clone_dir, repo_name)
            self.repo_cloner.cleanup_repository(repo_path)
            
            # Remove from memory
            if github_url in self.analysis_results:
                del self.analysis_results[github_url]
            
            logger.info(f"Cleaned up repository: {github_url}")
        
        except Exception as e:
            logger.error(f"Error cleaning up repository: {str(e)}")
            raise
    
    def cleanup_all(self):
        """Clean up all cloned repositories and reset state"""
        try:
            self.repo_cloner.cleanup_all()
            self.analysis_results = {}
            self.file_parser.reset_stats()
            logger.info("Cleaned up all repositories")
        
        except Exception as e:
            logger.error(f"Error cleaning up all repositories: {str(e)}")
            raise
    
    def clear_cache(self):
        """Clear all cached analysis results"""
        try:
            if os.path.exists(self.cache_dir):
                import shutil
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
                logger.info("Cleared analysis cache")
        
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            raise
    
    def export_results(self, github_url: str, output_path: str):
        """
        Export analysis results to JSON file
        
        Args:
            github_url: Repository URL
            output_path: Path to output file
        """
        try:
            if github_url not in self.analysis_results:
                raise ValueError(f"No analysis results found for {github_url}")
            
            results = self.analysis_results[github_url]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Exported results to {output_path}")
        
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")
            raise

# Made with Bob