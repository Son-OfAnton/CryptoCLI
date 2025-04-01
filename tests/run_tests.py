#!/usr/bin/env python3
"""
Test runner script for CryptoCLI
"""
import pytest
import sys
import os

if __name__ == "__main__":
    # Compute the project root as the parent of the current file's directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    print(f"Project root set to: {project_root}")

    pytest_args = [
        "tests",                   # directory containing tests
        "-v",                      # verbose output
        "--cov=CryptoCLI",         # measure coverage for CryptoCLI package
        "--cov-report=term",       # report coverage in terminal
        "--cov-report=html:coverage_html",  # generate HTML report
    ]
    
    result = pytest.main(pytest_args)
    sys.exit(result)