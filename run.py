#!/usr/bin/env python3
"""
Full-stack startup script for AIDD Paper Tracker
Starts both FastAPI backend and React frontend
"""
import subprocess
import os
import sys
import time
from pathlib import Path

def check_requirements():
    """Check if required dependencies are installed"""
    print("🔍 Checking requirements...")
    
    # Check Python dependencies
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI dependencies found")
    except ImportError:
        print("❌ FastAPI dependencies missing. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])
    
    # Check if Node.js is available
    node_cmd = 'node.exe' if sys.platform == 'win32' else 'node'
    try:
        result = subprocess.run([node_cmd, '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js found: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found. Please install Node.js")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found. Please install Node.js")
        return False
    
    # Check if frontend dependencies are installed
    frontend_dir = Path("frontend")
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        try:
            if sys.platform == 'win32':
                subprocess.run(['cmd', '/c', 'npm install'], cwd=frontend_dir, check=True, shell=True)
            else:
                subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
            print("✅ Frontend dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install frontend dependencies: {e}")
            return False
        except FileNotFoundError:
            print("❌ npm not found. Please install Node.js and npm")
            return False
    else:
        print("✅ Frontend dependencies found")
    
    return True

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI backend...")
    backend_env = os.environ.copy()
    backend_env['PYTHONPATH'] = str(Path.cwd())
    
    return subprocess.Popen([
        sys.executable, "backend/run_server.py"
    ], env=backend_env)

def start_frontend():
    """Start the React frontend development server"""
    print("🚀 Starting React frontend...")
    if sys.platform == 'win32':
        return subprocess.Popen([
            'cmd', '/c', 'npm run dev'
        ], cwd='frontend', shell=True)
    else:
        return subprocess.Popen([
            'npm', 'run', 'dev'
        ], cwd='frontend')

def main():
    print("🧬 AIDD Paper Tracker - Full Stack Startup")
    print("=" * 50)
    
    if not check_requirements():
        print("❌ Requirements check failed")
        return
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend
        backend_process = start_backend()
        time.sleep(3)  # Give backend time to start
        
        # Start frontend
        frontend_process = start_frontend()
        
        print("\n✅ Both servers started successfully!")
        print("🌐 Frontend: http://localhost:5173")
        print("🔧 Backend API: http://localhost:8000")
        print("📖 API Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop both servers")
        
        # Wait for processes
        while True:
            if backend_process.poll() is not None:
                print("❌ Backend process stopped")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped")
                break
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up processes
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        
        print("👋 All servers stopped")

if __name__ == "__main__":
    main()