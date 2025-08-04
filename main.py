"""
Medical Chatbot - Simple Launcher
"""

import os
import sys
import subprocess

def main():
    print("🏥 Medical Chatbot")
    print("Starting...")
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Install streamlit if needed
    try:
        import streamlit
    except ImportError:
        print("Installing streamlit...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit"])
    
    # Run the app
    chat_file = "ui/chat_window.py"
    if os.path.exists(chat_file):
        print("🚀 Starting at http://localhost:8501")
        subprocess.run([sys.executable, "-m", "streamlit", "run", chat_file])
    else:
        print("❌ chat_window.py not found")

if __name__ == "__main__":
    main()