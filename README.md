# Simple Version Control System (SVCS)

A lightweight distributed version control system implemented in Python, inspired by Git. This project provides basic version control functionality including file staging, committing, branching, merging, and local repository cloning.

## Features

- Repository initialization
- File staging and committing
- Commit history viewing
- Branch creation and management
- Basic merge functionality with conflict detection
- File ignoring support (.svcignore)
- Local repository cloning

## Requirements

- Python 3.8+
- Dependencies listed in requirements.txt

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/svcs.git
cd svcs
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

## Usage

### Initialize a Repository
```bash
python -m svcs init
```

### Stage Files
```bash
python -m svcs add <file_path>
```

### Commit Changes
```bash
python -m svcs commit -m "Your commit message"
```

### View Status
```bash
python -m svcs status
```

### Create and Switch Branches
```bash
# Create a new branch
python -m svcs branch <branch_name>

# Switch to a branch
python -m svcs checkout <branch_name>

# List branches
python -m svcs branch
```

### Merge Branches
```bash
python -m svcs merge <branch_name>
```

### Clone Repository
```bash
python -m svcs clone <source_path> <destination_path>
```

### View File Contents
```bash
python -m svcs show <file_path>
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Version History

- v1.0.0 (2024) - Initial release
  - Basic version control functionality
  - Local repository operations
  - Branching and merging support
  - File ignore patterns
  - Repository cloning

## Acknowledgments

- Inspired by Git and its distributed version control model
- Built as an educational project to understand version control systems
