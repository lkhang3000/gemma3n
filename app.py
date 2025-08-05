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
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit>=1.28.0"])
    
    # Install psutil if needed
    try:
        import psutil
    except ImportError:
        print("Installing psutil...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil>=5.9.0"])
    
    # Install requests if needed
    try:
        import requests
    except ImportError:
        print("Installing requests...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests>=2.31.0"])
    
    # Run the app
    chat_file = "ui/chat_window.py"
    if os.path.exists(chat_file):
        print("🚀 Starting at http://localhost:8501")
        subprocess.run([sys.executable, "-m", "streamlit", "run", chat_file])
    else:
        print("❌ chat_window.py not found")

if __name__ == "__main__":
    main()

"""
Entry point for Streamlit Cloud deployment
"""

import streamlit as st
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Import the chat window
    from ui.chat_window import ChatWindow
    
    # Run the app
    app = ChatWindow()
    app.run()
    
except ImportError as e:
    st.title("🏥 Medical Chatbot")
    st.error("❌ Import Error!")
    st.write(f"Error: {e}")
    
    st.write("**File structure check:**")
    
    # Show current structure
    for root, dirs, files in os.walk("."):
        level = root.replace(".", "").count(os.sep)
        indent = " " * 2 * level
        st.write(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            st.write(f"{subindent}{file}")
    
    st.write("**Expected structure:**")
    st.code("""
gemma3n/
├── app.py (hoặc main.py)
├── requirements.txt
├── ui/
│   ├── chat_window.py
│   └── form_UI.py
└── back_end/
    ├── __init__.py
    └── chatbot_backend.py
    """)

except Exception as e:
    st.title("🏥 Medical Chatbot")
    st.error(f"❌ Startup Error: {e}")
    st.write("Please check the logs for more details")