import os
import sys
import subprocess
import signal

def main():
    print("[Python Runner] Starting Node.js backend...")
    
    # Locate project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # Check node modules
    node_modules_path = os.path.join(project_dir, 'node_modules')
    if not os.path.exists(node_modules_path):
        print("[Python Runner] node_modules not found. Installing dependencies...")
        npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
        try:
            subprocess.run([npm_cmd, 'install'], check=True, cwd=project_dir)
            print("[Python Runner] Dependencies installed successfully!")
        except Exception as e:
            print(f"[Python Runner Error] Failed to run npm install: {e}")
            print("[Python Runner Error] Please ensure Node.js and npm are installed and on your PATH.")
            sys.exit(1)

    # Start node server.js
    node_cmd = ['node', 'server.js']
    print(f"[Python Runner] Running: {' '.join(node_cmd)}")
    
    try:
        # Start subprocess
        process = subprocess.Popen(
            node_cmd,
            cwd=project_dir,
            stdout=sys.stdout,
            stderr=sys.stderr,
            stdin=sys.stdin
        )
        
        # Define clean shutdown
        def signal_handler(sig, frame):
            print("\n[Python Runner] Shutting down Node.js server...")
            process.terminate()
            process.wait()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Wait for the process to finish
        process.wait()
    except KeyboardInterrupt:
        print("\n[Python Runner] Shutting down Node.js server...")
        try:
            process.terminate()
            process.wait()
        except:
            pass
    except Exception as e:
        print(f"[Python Runner Error] Failed to run Node.js server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
