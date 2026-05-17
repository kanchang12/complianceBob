"""
Start the Flask API Server
Simple script to launch the Compliance Guardian API
"""

import sys
import os
import webbrowser
import time
import subprocess
import platform
from threading import Timer

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.app import create_app
from config import API_CONFIG

def check_ollama_running():
    """Check if Ollama is already running"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        return response.status_code == 200
    except:
        return False

def check_model_available():
    """Check if gemma2:2b model is available"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            for model in models:
                if 'gemma2:2b' in model.get('name', ''):
                    return True
        return False
    except:
        return False

def pull_model():
    """Pull gemma2:2b model if not available"""
    if check_model_available():
        print("[OK] gemma2:2b model is available")
        return True
    
    print("Downloading gemma2:2b model (this may take a few minutes)...")
    try:
        result = subprocess.run(['ollama', 'pull', 'gemma2:2b'],
                              capture_output=True,
                              text=True,
                              timeout=600)  # 10 minute timeout
        if result.returncode == 0:
            print("[OK] gemma2:2b model downloaded successfully")
            return True
        else:
            print(f"[WARNING] Failed to download model: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("[WARNING] Model download timed out")
        return False
    except Exception as e:
        print(f"[WARNING] Error downloading model: {str(e)}")
        return False

def start_ollama():
    """Start Ollama service if not running"""
    if check_ollama_running():
        print("[OK] Ollama is already running")
        # Check and pull model if needed
        pull_model()
        return True
    
    print("Starting Ollama service in background...")
    try:
        system = platform.system()
        if system == "Windows":
            # On Windows, start Ollama hidden in background
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.Popen(['ollama', 'serve'],
                           startupinfo=startupinfo,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        else:
            # On Linux/Mac, start in background
            subprocess.Popen(['ollama', 'serve'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        
        # Wait for Ollama to start
        print("Waiting for Ollama to start...", end='', flush=True)
        for i in range(10):
            time.sleep(1)
            print('.', end='', flush=True)
            if check_ollama_running():
                print(" [OK] Ollama started successfully!")
                # Pull model after Ollama starts
                pull_model()
                return True
        
        print(" [WARNING] Ollama may not have started properly")
        return False
    except FileNotFoundError:
        print("[WARNING] Ollama not found. Please install Ollama from https://ollama.ai")
        print("  The API will still work but deep analysis features will be limited.")
        return False
    except Exception as e:
        print(f"[WARNING] Error starting Ollama: {str(e)}")
        return False

def open_browser():
    """Open the landing page in the default browser after a short delay"""
    time.sleep(3)  # Wait for server to start
    port = API_CONFIG.get('port', 5000)
    # Open the server URL, not a file path
    webbrowser.open(f'http://localhost:{port}/')

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Compliance Guardian API Server")
    print("=" * 60)
    
    # Start Ollama first
    start_ollama()
    print()
    
    print(f"Host: {API_CONFIG.get('host', '0.0.0.0')}")
    print(f"Port: {API_CONFIG.get('port', 5000)}")
    print(f"Debug: {API_CONFIG.get('debug', True)}")
    print(f"\nAPI Documentation: http://localhost:{API_CONFIG.get('port', 5000)}/api/docs")
    print(f"Frontend: http://localhost:{API_CONFIG.get('port', 5000)}/")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")
    
    # Open browser in a separate thread
    Timer(3.0, open_browser).start()
    
    app = create_app()
    app.run(
        host=API_CONFIG.get('host', '0.0.0.0'),
        port=API_CONFIG.get('port', 5000),
        debug=API_CONFIG.get('debug', True),
        threaded=True
    )

# Made with Bob