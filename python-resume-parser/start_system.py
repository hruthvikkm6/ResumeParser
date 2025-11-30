#!/usr/bin/env python3
"""
Startup script for Resume Parser & ATS Scoring System
Starts both backend and dashboard in development mode
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

class Colors:
    """Terminal colors for output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(message, color=Colors.END):
    """Print colored message"""
    print(f"{color}{message}{Colors.END}")

def check_dependencies():
    """Check if all dependencies are installed"""
    print_colored("🔍 Checking dependencies...", Colors.BLUE)
    
    # Check backend dependencies
    backend_requirements = Path("backend/requirements.txt")
    if not backend_requirements.exists():
        print_colored("❌ Backend requirements.txt not found", Colors.RED)
        return False
    
    # Check dashboard dependencies
    dashboard_requirements = Path("dashboard/requirements.txt")
    if not dashboard_requirements.exists():
        print_colored("❌ Dashboard requirements.txt not found", Colors.RED)
        return False
    
    print_colored("✅ Dependency files found", Colors.GREEN)
    return True

def start_backend():
    """Start the FastAPI backend"""
    print_colored("🚀 Starting FastAPI backend...", Colors.BLUE)
    
    # Change to backend directory and start uvicorn
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print_colored("❌ Backend directory not found", Colors.RED)
        return None
    
    try:
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONPATH'] = str(backend_dir.absolute())
        
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], cwd=backend_dir, env=env)
        
        return process
        
    except Exception as e:
        print_colored(f"❌ Failed to start backend: {e}", Colors.RED)
        return None

def start_dashboard():
    """Start the Streamlit dashboard"""
    print_colored("🎨 Starting Streamlit dashboard...", Colors.BLUE)
    
    dashboard_dir = Path("dashboard")
    if not dashboard_dir.exists():
        print_colored("❌ Dashboard directory not found", Colors.RED)
        return None
    
    try:
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONPATH'] = str(dashboard_dir.absolute())
        env['BACKEND_URL'] = 'http://localhost:8000'
        
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", 
            "run", "app.py", 
            "--server.port=8501",
            "--server.address=0.0.0.0"
        ], cwd=dashboard_dir, env=env)
        
        return process
        
    except Exception as e:
        print_colored(f"❌ Failed to start dashboard: {e}", Colors.RED)
        return None

def wait_for_backend():
    """Wait for backend to be ready"""
    import requests
    
    print_colored("⏳ Waiting for backend to start...", Colors.YELLOW)
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print_colored("✅ Backend is ready!", Colors.GREEN)
                return True
        except:
            pass
        
        time.sleep(1)
        print(".", end="", flush=True)
    
    print_colored("\n❌ Backend failed to start within 30 seconds", Colors.RED)
    return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "backend/uploads",
        "data/resumes",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print_colored("\n🛑 Shutting down system...", Colors.YELLOW)
    
    # Terminate processes
    for process in active_processes:
        if process and process.poll() is None:
            process.terminate()
    
    # Wait for processes to terminate
    time.sleep(2)
    
    # Force kill if necessary
    for process in active_processes:
        if process and process.poll() is None:
            process.kill()
    
    print_colored("👋 System shutdown complete", Colors.GREEN)
    sys.exit(0)

# Global list to track processes
active_processes = []

def main():
    """Main startup function"""
    print_colored("🚀 Resume Parser & ATS Scoring System", Colors.BOLD + Colors.BLUE)
    print_colored("=" * 50, Colors.BLUE)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check dependencies
    if not check_dependencies():
        print_colored("Please run setup first: python scripts/setup.py", Colors.YELLOW)
        return False
    
    # Create directories
    create_directories()
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return False
    
    active_processes.append(backend_process)
    
    # Wait for backend to be ready
    if not wait_for_backend():
        backend_process.terminate()
        return False
    
    # Start dashboard
    dashboard_process = start_dashboard()
    if not dashboard_process:
        backend_process.terminate()
        return False
    
    active_processes.append(dashboard_process)
    
    # Print access information
    print_colored("\n🎉 System started successfully!", Colors.GREEN + Colors.BOLD)
    print_colored("-" * 40, Colors.GREEN)
    print_colored("📡 Backend API: http://localhost:8000", Colors.GREEN)
    print_colored("📚 API Docs: http://localhost:8000/docs", Colors.GREEN)
    print_colored("🎨 Dashboard: http://localhost:8501", Colors.GREEN)
    print_colored("-" * 40, Colors.GREEN)
    print_colored("Press Ctrl+C to stop the system", Colors.YELLOW)
    
    # Keep processes running
    try:
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print_colored("❌ Backend process stopped unexpectedly", Colors.RED)
                break
            
            if dashboard_process.poll() is not None:
                print_colored("❌ Dashboard process stopped unexpectedly", Colors.RED)
                break
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)