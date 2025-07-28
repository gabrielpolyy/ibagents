#!/usr/bin/env python3
"""
Test runner for IB Client scanner tests
"""
import subprocess
import sys
import os

def run_scanner_tests():
    """Run the scanner tests using pytest"""
    # Change to the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(project_root)
    
    # Run pytest with specific test file
    cmd = [
        sys.executable, "-m", "pytest", 
        "test/test_scanner.py",
        "-v",  # verbose output
        "--tb=short",  # short traceback format
        "-s"  # don't capture output
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("All tests passed!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with return code: {e.returncode}")
        return e.returncode

def run_specific_test(test_name):
    """Run a specific test"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(project_root)
    
    cmd = [
        sys.executable, "-m", "pytest", 
        f"test/test_scanner.py::{test_name}",
        "-v", "-s"
    ]
    
    print(f"Running specific test: {test_name}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"Test {test_name} passed!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Test {test_name} failed with return code: {e.returncode}")
        return e.returncode

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        run_specific_test(test_name)
    else:
        # Run all scanner tests
        run_scanner_tests() 