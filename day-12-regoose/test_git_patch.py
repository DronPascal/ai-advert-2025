#!/usr/bin/env python3
"""Test script for git patch mode."""

import os
import sys
import subprocess
from pathlib import Path

def test_git_patch_mode():
    """Test git patch mode functionality."""

    # Set environment variable
    os.environ['REGOOSE_USE_GIT_PATCH'] = 'true'

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Run regoose with git patch mode
    cmd = [
        './venv/bin/regoose',
        'improve',
        '--goal', 'Add type hints to the greet function',
        '--directory', 'test_demo',
        '--debug'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        print("=== GIT PATCH MODE TEST RESULTS ===")
        print(f"Exit code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Test timed out")
        return False
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

if __name__ == '__main__':
    success = test_git_patch_mode()
    sys.exit(0 if success else 1)
