#!/usr/bin/env python3
"""
Enhanced full-stack startup script for AIDD Paper Tracker
Features:
- Automatic conda environment creation and management
- Dependency installation in conda environment
- Starts both FastAPI backend and React frontend
"""
import subprocess
import os
import sys
import time
import shutil
from pathlib import Path
import platform

# Configuration
ENV_NAME = "aidd-tracker"
PYTHON_VERSION = "3.10"

def check_conda():
    """Check if conda is available"""
    print("🔍 Checking for conda...")
    
    # Try different conda commands
    conda_commands = ['conda', 'conda.exe']
    if platform.system() == "Windows":
        conda_commands.extend([
            os.path.expanduser("~/miniconda3/Scripts/conda.exe"),
            os.path.expanduser("~/anaconda3/Scripts/conda.exe"),
            "C:/ProgramData/Miniconda3/Scripts/conda.exe",
            "C:/ProgramData/Anaconda3/Scripts/conda.exe"
        ])
    
    for cmd in conda_commands:
        try:
            result = subprocess.run([cmd, '--version'], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Found conda: {result.stdout.strip()}")
                return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    print("❌ Conda not found!")
    print("📋 Please install conda first:")
    print("   • Miniconda: https://docs.conda.io/en/latest/miniconda.html")
    print("   • Anaconda: https://www.anaconda.com/products/distribution")
    return None

def get_conda_env_list(conda_cmd):
    """Get list of existing conda environments"""
    try:
        result = subprocess.run([conda_cmd, 'env', 'list'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"⚠️ Warning: Could not list conda environments: {result.stderr}")
            return ""
    except subprocess.TimeoutExpired:
        print("⚠️ Warning: Conda env list command timed out")
        return ""
    except Exception as e:
        print(f"⚠️ Warning: Error listing conda environments: {e}")
        return ""

def create_or_activate_env(conda_cmd):
    """Create conda environment if it doesn't exist"""
    print(f"🔍 Checking for conda environment: {ENV_NAME}")
    
    # Check if environment exists
    env_list = get_conda_env_list(conda_cmd)
    if ENV_NAME in env_list:
        print(f"✅ Environment '{ENV_NAME}' already exists")
        return True
    
    print(f"🆕 Creating new conda environment: {ENV_NAME}")
    print(f"📦 Python version: {PYTHON_VERSION}")
    
    try:
        # Create environment with specific Python version
        create_cmd = [conda_cmd, 'create', '-n', ENV_NAME, f'python={PYTHON_VERSION}', '-y']
        result = subprocess.run(create_cmd, timeout=300)  # 5 minutes timeout
        
        if result.returncode == 0:
            print(f"✅ Successfully created environment: {ENV_NAME}")
            return True
        else:
            print(f"❌ Failed to create conda environment")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Environment creation timed out (took more than 5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error creating environment: {e}")
        return False

def get_conda_python_path(conda_cmd):
    """Get the Python path for the conda environment"""
    try:
        if platform.system() == "Windows":
            # Try to get conda info
            result = subprocess.run([conda_cmd, 'info', '--base'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                base_path = result.stdout.strip()
                python_path = os.path.join(base_path, "envs", ENV_NAME, "python.exe")
                if os.path.exists(python_path):
                    return python_path
            
            # Fallback: try common paths
            common_paths = [
                os.path.expanduser(f"~/miniconda3/envs/{ENV_NAME}/python.exe"),
                os.path.expanduser(f"~/anaconda3/envs/{ENV_NAME}/python.exe"),
                f"C:/ProgramData/Miniconda3/envs/{ENV_NAME}/python.exe",
                f"C:/ProgramData/Anaconda3/envs/{ENV_NAME}/python.exe"
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
        else:
            # Unix-like systems
            result = subprocess.run([conda_cmd, 'info', '--base'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                base_path = result.stdout.strip()
                python_path = os.path.join(base_path, "envs", ENV_NAME, "bin", "python")
                if os.path.exists(python_path):
                    return python_path
            
            # Fallback
            common_paths = [
                os.path.expanduser(f"~/miniconda3/envs/{ENV_NAME}/bin/python"),
                os.path.expanduser(f"~/anaconda3/envs/{ENV_NAME}/bin/python"),
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
    
    except Exception as e:
        print(f"⚠️ Warning: Could not determine conda Python path: {e}")
    
    return None

def install_python_dependencies(conda_cmd, python_path):
    """Install Python dependencies in conda environment"""
    print("📦 Installing Python dependencies...")
    
    # Check if requirements.txt exists
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    try:
        # Install dependencies using pip in conda environment
        install_cmd = [python_path, "-m", "pip", "install", "-r", requirements_file]
        result = subprocess.run(install_cmd, timeout=600)  # 10 minutes timeout
        
        if result.returncode == 0:
            print("✅ Python dependencies installed successfully")
            return True
        else:
            print("❌ Failed to install Python dependencies")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Dependency installation timed out")
        return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_node_and_npm():
    """Check if Node.js and npm are available with version requirements"""
    print("🔍 Checking Node.js and npm...")
    
    # Check Node.js
    node_cmd = 'node.exe' if platform.system() == 'Windows' else 'node'
    try:
        result = subprocess.run([node_cmd, '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            node_version = result.stdout.strip()
            print(f"✅ Node.js found: {node_version}")
            
            # Check if version meets requirement (Node.js 18+)
            try:
                # Extract version number (remove 'v' prefix if present)
                version_num = node_version.lstrip('v')
                major_version = int(version_num.split('.')[0])
                
                if major_version < 18:
                    print(f"⚠️  Warning: Node.js {major_version} detected, but Node.js 18+ is recommended")
                    print("📋 Consider upgrading: https://nodejs.org/")
                    # Continue anyway, but warn user
                else:
                    print(f"✅ Node.js version {major_version} meets requirements (18+)")
                    
            except (ValueError, IndexError):
                print(f"⚠️  Warning: Could not parse Node.js version: {node_version}")
                print("📋 Please ensure you have Node.js 18+ installed")
            
        else:
            print("❌ Node.js not found")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ Node.js not found")
        print("📋 Please install Node.js 18+: https://nodejs.org/")
        return False
    
    # Check npm
    npm_cmd = 'npm.cmd' if platform.system() == 'Windows' else 'npm'
    try:
        result = subprocess.run([npm_cmd, '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ npm found: {result.stdout.strip()}")
            return True
        else:
            print("❌ npm not found")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ npm not found")
        print("📋 npm should come with Node.js installation")
        return False

def install_frontend_dependencies():
    """Install frontend dependencies"""
    print("📦 Installing frontend dependencies...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Check if dependencies already installed
    if (frontend_dir / "node_modules").exists():
        print("✅ Frontend dependencies already installed")
        return True
    
    try:
        npm_cmd = 'npm.cmd' if platform.system() == 'Windows' else 'npm'
        if platform.system() == 'Windows':
            install_cmd = ['cmd', '/c', f'{npm_cmd} install']
            result = subprocess.run(install_cmd, cwd=frontend_dir, shell=True, timeout=300)
        else:
            install_cmd = [npm_cmd, 'install']
            result = subprocess.run(install_cmd, cwd=frontend_dir, timeout=300)
        
        if result.returncode == 0:
            print("✅ Frontend dependencies installed successfully")
            return True
        else:
            print("❌ Failed to install frontend dependencies")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Frontend dependency installation timed out")
        return False
    except Exception as e:
        print(f"❌ Error installing frontend dependencies: {e}")
        return False

def start_backend(python_path):
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI backend...")
    
    backend_env = os.environ.copy()
    backend_env['PYTHONPATH'] = str(Path.cwd())
    
    try:
        return subprocess.Popen([
            python_path, "backend/run_server.py"
        ], env=backend_env)
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the React frontend development server"""
    print("🚀 Starting React frontend...")
    
    try:
        if platform.system() == 'Windows':
            npm_cmd = 'npm.cmd'
            return subprocess.Popen([
                'cmd', '/c', f'{npm_cmd} run dev'
            ], cwd='frontend', shell=True)
        else:
            return subprocess.Popen([
                'npm', 'run', 'dev'
            ], cwd='frontend')
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def print_startup_info():
    """Print startup information"""
    print("\n" + "="*60)
    print("🧬 AIDD Paper Tracker - Enhanced Startup Complete!")
    print("="*60)
    print(f"🐍 Conda Environment: {ENV_NAME}")
    print(f"🌐 Frontend: http://localhost:5173")
    print(f"🔧 Backend API: http://localhost:8000")
    print(f"📖 API Documentation: http://localhost:8000/docs")
    print("\n💡 Tips:")
    print(f"   • To activate environment manually: conda activate {ENV_NAME}")
    print(f"   • To deactivate: conda deactivate")
    print(f"   • Environment location: Use 'conda info --envs' to see path")
    print("\n⌨️  Press Ctrl+C to stop both servers")
    print("="*60)

def cleanup_processes(backend_process, frontend_process):
    """Clean up processes"""
    print("\n🛑 Stopping servers...")
    
    processes = [
        ("Backend", backend_process),
        ("Frontend", frontend_process)
    ]
    
    for name, process in processes:
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔥 {name} force killed")
            except Exception as e:
                print(f"⚠️ Error stopping {name}: {e}")

def main():
    """Main function"""
    print("🧬 AIDD Paper Tracker - Enhanced Full Stack Startup")
    print("🔧 With Conda Environment Management")
    print("=" * 60)
    
    # Check conda
    conda_cmd = check_conda()
    if not conda_cmd:
        return 1
    
    # Create or check environment
    if not create_or_activate_env(conda_cmd):
        return 1
    
    # Get Python path in conda environment
    python_path = get_conda_python_path(conda_cmd)
    if not python_path:
        print(f"❌ Could not find Python in conda environment: {ENV_NAME}")
        print("💡 Try running: conda activate {ENV_NAME} && which python")
        return 1
    
    print(f"🐍 Using Python: {python_path}")
    
    # Install Python dependencies
    if not install_python_dependencies(conda_cmd, python_path):
        return 1
    
    # Check Node.js and npm
    if not check_node_and_npm():
        return 1
    
    # Install frontend dependencies
    if not install_frontend_dependencies():
        return 1
    
    # Create necessary directories
    print("📁 Creating necessary directories...")
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    print("✅ Directories created")
    
    # Start services
    backend_process = start_backend(python_path)
    if not backend_process:
        return 1
    
    print("⏳ Waiting for backend to start...")
    time.sleep(5)  # Give backend time to start
    
    frontend_process = start_frontend()
    if not frontend_process:
        if backend_process:
            backend_process.terminate()
        return 1
    
    print_startup_info()
    
    try:
        # Monitor processes
        while True:
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break
            time.sleep(2)
    
    except KeyboardInterrupt:
        pass  # User pressed Ctrl+C
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        cleanup_processes(backend_process, frontend_process)
        print("👋 All servers stopped. Environment is still active.")
        print(f"💡 To reactivate later: conda activate {ENV_NAME}")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code else 0)