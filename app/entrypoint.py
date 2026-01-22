#!/usr/bin/env python3
"""
Entrypoint script for the iNaturalist ETL container.
Downloads data from Allas and executes the ETL process.
"""

import os
import sys
import subprocess

# Add /app to Python path to ensure imports work
sys.path.insert(0, '/app')

def ensure_writable_directories():
    """Ensure store and privatedata directories exist and are writable."""
    directories = ['/app/store', '/app/privatedata']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, mode=0o777, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            # Ensure directory is writable (chmod 777)
            os.chmod(directory, 0o777)

def main():
    """Main entrypoint function."""
    # Ensure writable directories exist
    ensure_writable_directories()
    
    # Download data from Allas
    print("Downloading data from Allas...")
    try:
        import download_from_allas
        download_from_allas.download_from_allas()
        print("Data download complete.")
    except Exception as e:
        print(f"Error downloading data from Allas: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    # Get command arguments
    if len(sys.argv) > 1:
        # Arguments provided via CMD
        cmd_args = sys.argv[1:]
        
        # If first argument is a script name (e.g., "single.py"), run that script directly
        if cmd_args[0].endswith('.py'):
            script_name = cmd_args[0]
            script_args = cmd_args[1:]
            print(f"Executing {script_name} with arguments: {' '.join(script_args)}")
            result = subprocess.run(
                [sys.executable, script_name] + script_args,
                cwd='/app',
                check=False
            )
            sys.exit(result.returncode)
        # Otherwise, treat as arguments for inat.py (cmd_args already set)
    else:
        # No arguments - use production update parameters
        cmd_args = ['production', 'auto', 'true', '5']
    
    # Execute inat.py with the arguments
    print(f"Executing inat.py with arguments: {' '.join(cmd_args)}")
    try:
        # Change to /app directory
        os.chdir('/app')
        
        # Execute inat.py
        result = subprocess.run(
            [sys.executable, 'inat.py'] + cmd_args,
            cwd='/app',
            check=False  # Don't raise on non-zero exit, we'll handle it
        )
        
        # Exit with the same code as inat.py
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"Error executing ETL process: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
