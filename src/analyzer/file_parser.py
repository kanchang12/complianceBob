"""
File Parser Module
Parses and extracts code from repository files
"""

import os
import mimetypes
from typing import List, Dict, Set, Optional
from datetime import datetime
import logging
import chardet

logger = logging.getLogger(__name__)


class FileParser:
    """Handles parsing and extraction of code files"""
    
    # Language detection by file extension
    LANGUAGE_MAP = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript (React)',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript (React)',
        '.java': 'Java',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.c': 'C',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.cs': 'C#',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.kts': 'Kotlin Script',
        '.rs': 'Rust',
        '.scala': 'Scala',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.sql': 'SQL',
        '.sh': 'Shell Script',
        '.bash': 'Bash Script',
        '.zsh': 'Zsh Script',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.json': 'JSON',
        '.xml': 'XML',
        '.md': 'Markdown',
        '.txt': 'Text',
        '.env': 'Environment Config',
        '.ini': 'INI Config',
        '.toml': 'TOML Config',
        '.conf': 'Configuration',
        '.config': 'Configuration',
        '.vue': 'Vue.js',
        '.svelte': 'Svelte',
        '.r': 'R',
        '.m': 'Objective-C/MATLAB',
        '.pl': 'Perl',
        '.lua': 'Lua',
        '.dart': 'Dart',
        '.ex': 'Elixir',
        '.exs': 'Elixir Script',
        '.erl': 'Erlang',
        '.clj': 'Clojure',
        '.fs': 'F#',
        '.vb': 'Visual Basic',
        '.asm': 'Assembly',
    }
    
    # Supported file extensions for code analysis
    SUPPORTED_EXTENSIONS = set(LANGUAGE_MAP.keys())
    
    # Binary file extensions to skip
    BINARY_EXTENSIONS = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.dat',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
        '.mp3', '.wav', '.ogg', '.flac', '.aac',
        '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.pyc', '.pyo', '.class', '.o', '.obj',
        '.woff', '.woff2', '.ttf', '.eot', '.otf',
    }
    
    # Directories to ignore
    IGNORE_DIRS = {
        'node_modules', '.git', '__pycache__', 'venv', 'env',
        '.venv', 'dist', 'build', 'target', '.idea', '.vscode',
        'vendor', 'coverage', '.pytest_cache', '.mypy_cache',
        '.tox', '.eggs', '*.egg-info', '.gradle', '.mvn',
        'bower_components', 'jspm_packages', '.nuxt', '.next',
        '.cache', 'tmp', 'temp', 'logs', '.DS_Store'
    }
    
    # Maximum file size to parse (10 MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self):
        """Initialize file parser"""
        self.files_parsed = 0
        self.total_lines = 0
        self.skipped_files = 0
        self.errors = []
    
    def detect_encoding(self, file_path: str) -> str:
        """
        Detect file encoding using chardet
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected encoding (defaults to 'utf-8')
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(min(10000, os.path.getsize(file_path)))
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                # Use utf-8 if confidence is low
                if confidence < 0.7:
                    encoding = 'utf-8'
                
                return encoding or 'utf-8'
        except Exception as e:
            logger.warning(f"Error detecting encoding for {file_path}: {str(e)}")
            return 'utf-8'
    
    def is_binary_file(self, file_path: str) -> bool:
        """
        Check if file is binary
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if binary, False otherwise
        """
        # Check extension first
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.BINARY_EXTENSIONS:
            return True
        
        # Check using mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if not mime_type.startswith('text/') and mime_type != 'application/json':
                return True
        
        # Check file content (read first 8192 bytes)
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(8192)
                # Check for null bytes (common in binary files)
                if b'\x00' in chunk:
                    return True
        except Exception:
            return True
        
        return False
    
    def get_language(self, file_path: str) -> str:
        """
        Detect programming language from file extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name
        """
        ext = os.path.splitext(file_path)[1].lower()
        return self.LANGUAGE_MAP.get(ext, 'Unknown')
    
    def scan_repository(self, repo_path: str) -> List[Dict]:
        """
        Scan repository and collect all relevant code files
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            List of file information dictionaries
        """
        files_info = []
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Remove ignored directories from traversal
                dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS and not d.startswith('.')]
                
                for file in files:
                    # Skip hidden files
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    # Skip if not supported extension
                    if file_ext not in self.SUPPORTED_EXTENSIONS:
                        continue
                    
                    # Skip if binary
                    if self.is_binary_file(file_path):
                        self.skipped_files += 1
                        continue
                    
                    # Skip if too large
                    file_size = os.path.getsize(file_path)
                    if file_size > self.MAX_FILE_SIZE:
                        logger.warning(f"Skipping large file: {file_path} ({file_size} bytes)")
                        self.skipped_files += 1
                        continue
                    
                    relative_path = os.path.relpath(file_path, repo_path)
                    
                    file_info = {
                        'path': file_path,
                        'relative_path': relative_path,
                        'filename': file,
                        'extension': file_ext,
                        'language': self.get_language(file_path),
                        'size': file_size,
                        'last_modified': datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).isoformat()
                    }
                    
                    files_info.append(file_info)
            
            logger.info(f"Found {len(files_info)} code files in {repo_path}")
            logger.info(f"Skipped {self.skipped_files} files (binary/too large)")
            return files_info
        
        except Exception as e:
            logger.error(f"Error scanning repository {repo_path}: {str(e)}")
            raise
    
    def read_file_content(self, file_path: str, max_lines: Optional[int] = None) -> str:
        """
        Read content from a file with encoding detection
        
        Args:
            file_path: Path to the file
            max_lines: Optional maximum number of lines to read
            
        Returns:
            File content as string
        """
        try:
            # Detect encoding
            encoding = self.detect_encoding(file_path)
            
            # Read file
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                if max_lines:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line)
                    content = ''.join(lines)
                else:
                    content = f.read()
            
            self.files_parsed += 1
            self.total_lines += content.count('\n')
            
            return content
        
        except Exception as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            raise
    
    def parse_file(self, file_path: str, include_line_numbers: bool = False) -> Dict:
        """
        Parse a file and extract relevant information
        
        Args:
            file_path: Path to the file
            include_line_numbers: Whether to include line-by-line content
            
        Returns:
            Dictionary with file content and metadata
        """
        try:
            content = self.read_file_content(file_path)
            lines = content.split('\n')
            
            file_info = {
                'path': file_path,
                'filename': os.path.basename(file_path),
                'extension': os.path.splitext(file_path)[1],
                'language': self.get_language(file_path),
                'content': content,
                'lines': len(lines),
                'size': len(content),
                'encoding': self.detect_encoding(file_path),
                'last_modified': datetime.fromtimestamp(
                    os.path.getmtime(file_path)
                ).isoformat()
            }
            
            # Add line-by-line content if requested
            if include_line_numbers:
                file_info['lines_content'] = [
                    {'line_number': i + 1, 'content': line}
                    for i, line in enumerate(lines)
                ]
            
            return file_info
        
        except Exception as e:
            error_msg = f"Error parsing file {file_path}: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            raise
    
    def parse_files_batch(self, file_paths: List[str], include_line_numbers: bool = False) -> List[Dict]:
        """
        Parse multiple files at once
        
        Args:
            file_paths: List of file paths
            include_line_numbers: Whether to include line-by-line content
            
        Returns:
            List of parsed file information
        """
        parsed_files = []
        
        for file_path in file_paths:
            try:
                file_info = self.parse_file(file_path, include_line_numbers)
                parsed_files.append(file_info)
            except Exception as e:
                logger.warning(f"Skipping file {file_path} due to error: {str(e)}")
                continue
        
        logger.info(f"Successfully parsed {len(parsed_files)} out of {len(file_paths)} files")
        return parsed_files
    
    def get_file_statistics(self, repo_path: str) -> Dict:
        """
        Get statistics about files in the repository
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dictionary with file statistics
        """
        files_info = self.scan_repository(repo_path)
        
        stats = {
            'total_files': len(files_info),
            'total_size': sum(f['size'] for f in files_info),
            'languages': {},
            'extensions': {},
            'largest_files': [],
            'skipped_files': self.skipped_files
        }
        
        # Count files by language
        for file_info in files_info:
            lang = file_info['language']
            stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
        
        # Count files by extension
        for file_info in files_info:
            ext = file_info['extension']
            stats['extensions'][ext] = stats['extensions'].get(ext, 0) + 1
        
        # Get largest files
        sorted_files = sorted(files_info, key=lambda x: x['size'], reverse=True)
        stats['largest_files'] = sorted_files[:10]
        
        return stats
    
    def filter_files_by_extension(self, files_info: List[Dict], 
                                  extensions: Set[str]) -> List[Dict]:
        """
        Filter files by extension
        
        Args:
            files_info: List of file information dictionaries
            extensions: Set of extensions to filter by
            
        Returns:
            Filtered list of files
        """
        return [f for f in files_info if f['extension'] in extensions]
    
    def filter_files_by_language(self, files_info: List[Dict],
                                languages: Set[str]) -> List[Dict]:
        """
        Filter files by programming language
        
        Args:
            files_info: List of file information dictionaries
            languages: Set of languages to filter by
            
        Returns:
            Filtered list of files
        """
        return [f for f in files_info if f['language'] in languages]
    
    def get_stats(self) -> Dict:
        """
        Get parsing statistics
        
        Returns:
            Dictionary with parsing stats
        """
        return {
            'files_parsed': self.files_parsed,
            'total_lines': self.total_lines,
            'skipped_files': self.skipped_files,
            'errors': len(self.errors)
        }
    
    def reset_stats(self):
        """Reset parsing statistics"""
        self.files_parsed = 0
        self.total_lines = 0
        self.skipped_files = 0
        self.errors = []

# Made with Bob
