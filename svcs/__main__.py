"""Command-line interface for SVCS."""

import sys
import argparse
from pathlib import Path
from .repository import Repository

def main():
    parser = argparse.ArgumentParser(description='Simple Version Control System')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize a new repository')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Stage files')
    add_parser.add_argument('files', nargs='+', help='Files to stage')
    
    # Commit command
    commit_parser = subparsers.add_parser('commit', help='Commit staged changes')
    commit_parser.add_argument('-m', '--message', required=True, help='Commit message')
    commit_parser.add_argument('-a', '--author', help='Author name')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show repository status')
    
    # Branch commands
    branch_parser = subparsers.add_parser('branch', help='Create or list branches')
    branch_parser.add_argument('name', nargs='?', help='Name of the new branch')
    
    # Checkout command
    checkout_parser = subparsers.add_parser('checkout', help='Switch branches')
    checkout_parser.add_argument('branch', help='Branch to switch to')
    
    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Merge branches')
    merge_parser.add_argument('branch', help='Branch to merge from')
    
    # Clone command
    clone_parser = subparsers.add_parser('clone', help='Clone a repository')
    clone_parser.add_argument('source', help='Source repository path')
    clone_parser.add_argument('destination', help='Destination path')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show file contents')
    show_parser.add_argument('file', help='File path')
    show_parser.add_argument('--commit', help='Commit hash (defaults to HEAD)')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'clone':
            repo = Repository.clone(args.source, args.destination)
            print(f"Cloned repository from {args.source} to {args.destination}")
            return
            
        repo = Repository(Path.cwd())
        
        if args.command == 'init':
            repo.init()
            print("Initialized empty repository")
            
        elif args.command == 'add':
            for file_path in args.files:
                try:
                    repo.stage_file(file_path)
                    print(f"Staged: {file_path}")
                except Exception as e:
                    print(f"Error staging {file_path}: {str(e)}", file=sys.stderr)
            
        elif args.command == 'commit':
            commit_hash = repo.commit(args.message, args.author)
            print(f"Created commit {commit_hash[:8]}")
            
        elif args.command == 'status':
            if not repo.is_initialized():
                print("Not a repository", file=sys.stderr)
                sys.exit(1)
                
            status = repo.get_status()
            current_branch = repo.get_current_branch()
            print(f"On branch {current_branch}")
            
            if status['staged']:
                print("\nStaged files:")
                for file in sorted(status['staged']):
                    print(f"  {file}")
                    
            if status['modified']:
                print("\nModified files:")
                for file in sorted(status['modified']):
                    print(f"  {file}")
                    
            if status['untracked']:
                print("\nUntracked files:")
                for file in sorted(status['untracked']):
                    print(f"  {file}")
                    
            if not any(status.values()):
                print("Working directory clean")
                
        elif args.command == 'branch':
            if args.name:
                repo.create_branch(args.name)
                print(f"Created branch {args.name}")
            else:
                branches = repo.list_branches()
                current = repo.get_current_branch()
                for name, commit in branches.items():
                    prefix = '*' if name == current else ' '
                    print(f"{prefix} {name} ({commit[:8]})")
                    
        elif args.command == 'checkout':
            repo.switch_branch(args.branch)
            print(f"Switched to branch {args.branch}")
            
        elif args.command == 'merge':
            result = repo.merge_branch(args.branch)
            
            if result['conflicts']:
                print("\nMerge conflicts in:")
                for file in sorted(result['conflicts']):
                    print(f"  {file}")
                print("\nPlease resolve conflicts and commit the changes")
            else:
                if result['merged']:
                    print("\nSuccessfully merged files:")
                    for file in sorted(result['merged']):
                        print(f"  {file}")
                print(f"\nMerged branch {args.branch}")
                
        elif args.command == 'show':
            try:
                content = repo.get_file_content(args.file, args.commit)
                try:
                    # Try to decode as text
                    print(content.decode('utf-8'))
                except UnicodeDecodeError:
                    print("Binary file")
            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                sys.exit(1)
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
