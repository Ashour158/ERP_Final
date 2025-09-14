#!/usr/bin/env python3
"""
Syntax validation for app.py without requiring Flask to be installed
"""

import ast
import sys

def validate_python_file(filename):
    """Validate Python file syntax"""
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        # Parse the AST to check for syntax errors
        ast.parse(content)
        print(f"✓ {filename} has valid Python syntax")
        return True
    except SyntaxError as e:
        print(f"✗ {filename} has syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ {filename} validation failed: {e}")
        return False

def main():
    """Validate all Python files"""
    files_to_check = [
        'app.py',
        'config.py', 
        'wsgi.py',
        'init_db.py',
        'validate.py'
    ]
    
    print("Python Syntax Validation")
    print("=" * 30)
    
    all_valid = True
    for filename in files_to_check:
        if not validate_python_file(filename):
            all_valid = False
    
    if all_valid:
        print("\n🎉 All Python files have valid syntax!")
        return 0
    else:
        print("\n⚠️  Some files have syntax errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())