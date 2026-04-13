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
            # Create with permissive mode so arbitrary UIDs (OpenShift) can write.
            # Note: actual permissions may also be affected by umask.
            os.makedirs(directory, mode=0o777, exist_ok=True)
            print(f"Created directory: {directory}")
        # Do not chmod at runtime: the container runs as non-root in OpenShift.
        # Permissions are set during image build (see Dockerfile).

def main():
    """Main entrypoint function."""
    # Log version (git SHA + build date) so OpenShift logs show which image is running
    git_sha = os.environ.get('APP_GIT_SHA', 'unknown')
    build_date = os.environ.get('APP_BUILD_DATE', 'unknown')
    print(f"iNaturalist ETL version: {git_sha} (built {build_date})")

    # Ensure writable directories exist
    ensure_writable_directories()
    
    # Get command arguments
    if len(sys.argv) > 1:
        # Arguments provided via CMD
        cmd_args = sys.argv[1:]
    else:
        # No arguments - use production update parameters
        cmd_args = ['production', 'auto', 'true', '5']

    # If first argument is a script name (e.g., "single.py"), run that script after download.
    is_script_run = len(cmd_args) > 0 and cmd_args[0].endswith('.py')
    script_name = cmd_args[0] if is_script_run else None
    script_args = cmd_args[1:] if is_script_run else []

    # In manual mode, do not fetch data-ALLAS.json. inat.py uses local data-MANUAL.json.
    is_manual_mode = len(cmd_args) > 1 and cmd_args[1] == 'manual'

    # Download data from Allas
    print("Downloading data from Allas...")
    try:
        import download_from_allas
        download_from_allas.download_from_allas(skip_state_file=is_manual_mode)
        print("Data download complete.")
    except Exception as e:
        print(f"Error downloading data from Allas: {str(e)}", file=sys.stderr)
        sys.exit(1)

    if is_script_run:
        print(f"Executing {script_name} with arguments: {' '.join(script_args)}")
        result = subprocess.run(
            [sys.executable, script_name] + script_args,
            cwd='/app',
            check=False
        )
        sys.exit(result.returncode)

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
