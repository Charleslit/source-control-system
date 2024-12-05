"""Repository management module for SVCS."""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class Repository:
    """Manages repository operations including initialization, staging, and committing."""
    
    REPO_DIR = '.repo'
    STAGING_FILE = 'staging.json'
    COMMITS_DIR = 'commits'
    BRANCHES_FILE = 'branches.json'
    IGNORE_FILE = '.svcignore'
    
    def __init__(self, path: str):
        """Initialize repository instance.
        
        Args:
            path: Path to repository root directory
        """
        self.root_path = Path(path).resolve()
        self.repo_path = self.root_path / self.REPO_DIR
        
    def init(self) -> None:
        """Initialize a new repository."""
        if self.repo_path.exists():
            raise Exception("Repository already exists")
            
        # Create repository structure
        os.makedirs(self.repo_path)
        os.makedirs(self.repo_path / self.COMMITS_DIR)
        
        # Initialize staging area
        self._write_json(self.repo_path / self.STAGING_FILE, {})
        
        # Initialize branches with main branch
        self._write_json(self.repo_path / self.BRANCHES_FILE, {
            "main": None,  # No commits yet
            "current": "main"
        })
        
        # Create default ignore file
        ignore_file = self.root_path / self.IGNORE_FILE
        if not ignore_file.exists():
            with open(ignore_file, 'w') as f:
                f.write("# Ignored files and directories\n")
                f.write(f"{self.REPO_DIR}/\n")
                f.write("__pycache__/\n")
                f.write("*.pyc\n")
    
    def _write_json(self, path: Path, data: dict) -> None:
        """Write data to JSON file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _read_json(self, path: Path) -> dict:
        """Read data from JSON file."""
        with open(path, 'r') as f:
            return json.load(f)
            
    def _hash_file(self, file_path: Path) -> str:
        """Generate SHA-256 hash of file contents."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
            
    def is_initialized(self) -> bool:
        """Check if repository is initialized."""
        return self.repo_path.exists()
        
    def get_status(self) -> Dict[str, List[str]]:
        """Get repository status including staged and modified files."""
        if not self.is_initialized():
            raise Exception("Not a repository")
            
        staging = self._read_json(self.repo_path / self.STAGING_FILE)
        status = {
            "staged": [],
            "modified": [],
            "untracked": []
        }
        
        for file_path in self.root_path.rglob('*'):
            # Skip repository directory and ignored files
            if self._is_ignored(file_path):
                continue
                
            rel_path = str(file_path.relative_to(self.root_path))
            
            if file_path.is_file():
                if rel_path in staging:
                    current_hash = self._hash_file(file_path)
                    if current_hash != staging[rel_path]['hash']:
                        status['modified'].append(rel_path)
                    else:
                        status['staged'].append(rel_path)
                else:
                    status['untracked'].append(rel_path)
                    
        return status
        
    def _is_ignored(self, path: Path) -> bool:
        """Check if a path should be ignored based on .svcignore rules."""
        if str(path).startswith(str(self.repo_path)):
            return True
            
        ignore_file = self.root_path / self.IGNORE_FILE
        if not ignore_file.exists():
            return False
            
        with open(ignore_file, 'r') as f:
            patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
        rel_path = str(path.relative_to(self.root_path))
        return any(Path(rel_path).match(pattern) for pattern in patterns)
        
    def stage_file(self, file_path: str) -> None:
        """Stage a file for commit.
        
        Args:
            file_path: Path to the file to stage
        """
        if not self.is_initialized():
            raise Exception("Not a repository")
            
        abs_path = (self.root_path / file_path).resolve()
        if not abs_path.exists():
            raise Exception(f"File not found: {file_path}")
            
        if not abs_path.is_file():
            raise Exception(f"Not a file: {file_path}")
            
        if self._is_ignored(abs_path):
            raise Exception(f"File is ignored: {file_path}")
            
        rel_path = str(abs_path.relative_to(self.root_path))
        file_hash = self._hash_file(abs_path)
        
        staging = self._read_json(self.repo_path / self.STAGING_FILE)
        staging[rel_path] = {
            'hash': file_hash,
            'timestamp': datetime.now().isoformat()
        }
        self._write_json(self.repo_path / self.STAGING_FILE, staging)
        
    def commit(self, message: str, author: Optional[str] = None) -> str:
        """Create a new commit with staged changes.
        
        Args:
            message: Commit message
            author: Optional author name
            
        Returns:
            str: Commit hash
        """
        if not self.is_initialized():
            raise Exception("Not a repository")
            
        staging = self._read_json(self.repo_path / self.STAGING_FILE)
        if not staging:
            raise Exception("No changes staged for commit")
            
        # Get current branch
        branches = self._read_json(self.repo_path / self.BRANCHES_FILE)
        current_branch = branches['current']
        parent_commit = branches[current_branch]
        
        # Create commit object
        commit = {
            'message': message,
            'author': author or os.environ.get('USER', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'parent': parent_commit,
            'changes': staging
        }
        
        # Generate commit hash
        commit_hash = hashlib.sha256(json.dumps(commit, sort_keys=True).encode()).hexdigest()
        
        # Save commit
        commit_path = self.repo_path / self.COMMITS_DIR / f"{commit_hash}.json"
        self._write_json(commit_path, commit)
        
        # Update branch pointer
        branches[current_branch] = commit_hash
        self._write_json(self.repo_path / self.BRANCHES_FILE, branches)
        
        # Clear staging area
        self._write_json(self.repo_path / self.STAGING_FILE, {})
        
        return commit_hash
        
    def get_commit(self, commit_hash: str) -> dict:
        """Get commit information.
        
        Args:
            commit_hash: Hash of the commit to retrieve
            
        Returns:
            dict: Commit information
        """
        commit_path = self.repo_path / self.COMMITS_DIR / f"{commit_hash}.json"
        if not commit_path.exists():
            raise Exception(f"Commit not found: {commit_hash}")
            
        return self._read_json(commit_path)

    def create_branch(self, branch_name: str) -> None:
        """Create a new branch at the current commit.
        
        Args:
            branch_name: Name of the new branch
        """
        if not self.is_initialized():
            raise Exception("Not a repository")
            
        branches = self._read_json(self.repo_path / self.BRANCHES_FILE)
        if branch_name in branches:
            raise Exception(f"Branch already exists: {branch_name}")
            
        # New branch points to the same commit as current branch
        current_branch = branches['current']
        branches[branch_name] = branches[current_branch]
        self._write_json(self.repo_path / self.BRANCHES_FILE, branches)
        
    def list_branches(self) -> Dict[str, str]:
        """List all branches and their latest commits.
        
        Returns:
            Dict[str, str]: Dictionary mapping branch names to commit hashes
        """
        if not self.is_initialized():
            raise Exception("Not a repository")
            
        branches = self._read_json(self.repo_path / self.BRANCHES_FILE)
        return {k: v for k, v in branches.items() if k != 'current'}
        
    def switch_branch(self, branch_name: str) -> None:
        """Switch to a different branch.
        
        Args:
            branch_name: Name of the branch to switch to
        """
        if not self.is_initialized():
            raise Exception("Not a repository")
            
        branches = self._read_json(self.repo_path / self.BRANCHES_FILE)
        if branch_name not in branches:
            raise Exception(f"Branch not found: {branch_name}")
            
        # Check for uncommitted changes
        status = self.get_status()
        if status['modified'] or status['staged']:
            raise Exception("Cannot switch branches with uncommitted changes")
            
        branches['current'] = branch_name
        self._write_json(self.repo_path / self.BRANCHES_FILE, branches)
        
    def get_current_branch(self) -> str:
        """Get the name of the current branch.
        
        Returns:
            str: Name of the current branch
        """
        if not self.is_initialized():
            raise Exception("Not a repository")
            
        branches = self._read_json(self.repo_path / self.BRANCHES_FILE)
        return branches['current']
        
    def merge_branch(self, branch_name: str) -> Dict[str, List[str]]:
        """Merge another branch into the current branch.
        
        Args:
            branch_name: Name of the branch to merge from
            
        Returns:
            Dict[str, List[str]]: Dictionary containing lists of:
                - 'conflicts': Files with merge conflicts
                - 'merged': Successfully merged files
        """
        if not self.is_initialized():
            raise Exception("Not a repository")
            
        branches = self._read_json(self.repo_path / self.BRANCHES_FILE)
        if branch_name not in branches:
            raise Exception(f"Branch not found: {branch_name}")
            
        current_branch = branches['current']
        if branch_name == current_branch:
            raise Exception("Cannot merge a branch into itself")
            
        # Check for uncommitted changes
        status = self.get_status()
        if status['modified'] or status['staged']:
            raise Exception("Cannot merge with uncommitted changes")
            
        # Get the commits
        source_commit = self.get_commit(branches[branch_name])
        target_commit = self.get_commit(branches[current_branch])
        
        # Find common ancestor (for this simple implementation, we'll use the parent commit)
        source_history = self._get_commit_history(branches[branch_name])
        target_history = self._get_commit_history(branches[current_branch])
        common_ancestor = None
        
        for commit in source_history:
            if commit in target_history:
                common_ancestor = commit
                break
                
        if not common_ancestor:
            raise Exception("No common ancestor found")
            
        # Compare files between branches
        result = {
            'conflicts': [],
            'merged': []
        }
        
        source_files = source_commit['changes']
        target_files = target_commit['changes']
        ancestor_commit = self.get_commit(common_ancestor)
        ancestor_files = ancestor_commit['changes']
        
        # Check all files in both branches
        all_files = set(source_files.keys()) | set(target_files.keys())
        
        for file_path in all_files:
            source_change = source_files.get(file_path, {}).get('hash')
            target_change = target_files.get(file_path, {}).get('hash')
            ancestor_change = ancestor_files.get(file_path, {}).get('hash')
            
            # File changed in both branches
            if (source_change != ancestor_change and 
                target_change != ancestor_change and 
                source_change != target_change):
                result['conflicts'].append(file_path)
            else:
                result['merged'].append(file_path)
                
        return result
        
    def _get_commit_history(self, commit_hash: str) -> List[str]:
        """Get the history of commits starting from a given commit.
        
        Args:
            commit_hash: Hash of the starting commit
            
        Returns:
            List[str]: List of commit hashes in chronological order
        """
        history = []
        current = commit_hash
        
        while current:
            history.append(current)
            commit = self.get_commit(current)
            current = commit['parent']
            
        return history

    @classmethod
    def clone(cls, source_path: str, destination_path: str) -> 'Repository':
        """Clone a repository to a new location.
        
        Args:
            source_path: Path to the source repository
            destination_path: Path where to create the new repository
            
        Returns:
            Repository: New repository instance
        """
        source_repo = cls(source_path)
        if not source_repo.is_initialized():
            raise Exception(f"Not a repository: {source_path}")
            
        dest_path = Path(destination_path)
        if dest_path.exists():
            if not dest_path.is_dir() or any(dest_path.iterdir()):
                raise Exception(f"Destination {destination_path} exists and is not an empty directory")
        else:
            dest_path.mkdir(parents=True)
            
        # Create new repository
        dest_repo = cls(destination_path)
        dest_repo.init()
        
        # Copy repository data
        cls._copy_repository_data(source_repo, dest_repo)
        
        return dest_repo
        
    @staticmethod
    def _copy_repository_data(source_repo: 'Repository', dest_repo: 'Repository') -> None:
        """Copy repository data from source to destination.
        
        Args:
            source_repo: Source repository
            dest_repo: Destination repository
        """
        # Copy commits
        source_commits_dir = source_repo.repo_path / source_repo.COMMITS_DIR
        dest_commits_dir = dest_repo.repo_path / dest_repo.COMMITS_DIR
        
        for commit_file in source_commits_dir.glob('*.json'):
            with open(commit_file, 'r') as f:
                commit_data = json.load(f)
                
            # Copy commit file
            dest_commit_file = dest_commits_dir / commit_file.name
            with open(dest_commit_file, 'w') as f:
                json.dump(commit_data, f, indent=2)
                
            # Copy actual files for this commit
            for file_path, file_info in commit_data['changes'].items():
                source_file = source_repo.root_path / file_path
                if source_file.exists() and source_file.is_file():
                    dest_file = dest_repo.root_path / file_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(source_file, dest_file)
        
        # Copy branch information
        source_branches = source_repo._read_json(source_repo.repo_path / source_repo.BRANCHES_FILE)
        dest_repo._write_json(dest_repo.repo_path / dest_repo.BRANCHES_FILE, source_branches)
        
        # Copy ignore file if it exists
        source_ignore = source_repo.root_path / source_repo.IGNORE_FILE
        if source_ignore.exists():
            dest_ignore = dest_repo.root_path / dest_repo.IGNORE_FILE
            import shutil
            shutil.copy2(source_ignore, dest_ignore)
            
    def get_file_content(self, file_path: str, commit_hash: Optional[str] = None) -> bytes:
        """Get the content of a file at a specific commit.
        
        Args:
            file_path: Path to the file
            commit_hash: Optional commit hash, defaults to current branch HEAD
            
        Returns:
            bytes: File content
        """
        if not self.is_initialized():
            raise Exception("Not a repository")
            
        if commit_hash is None:
            branches = self._read_json(self.repo_path / self.BRANCHES_FILE)
            commit_hash = branches[branches['current']]
            
        commit = self.get_commit(commit_hash)
        if file_path not in commit['changes']:
            raise Exception(f"File not found in commit: {file_path}")
            
        abs_path = self.root_path / file_path
        if not abs_path.exists():
            raise Exception(f"File not found: {file_path}")
            
        with open(abs_path, 'rb') as f:
            return f.read()
