import sys
import os
import logging
import subprocess

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("medical_chatbot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting Medical Chatbot with Streamlit...")
        
        # Check if streamlit is installed
        try:
            import streamlit
            logger.info("✅ Streamlit is available")
        except ImportError:
            logger.error("❌ Streamlit not installed. Please run: pip install streamlit")
            print("❌ Error: Streamlit not installed")
            print("Please run: pip install streamlit")
            return
        
        # Run Streamlit app
        chat_window_path = os.path.join(project_root, "ui", "chat_window.py")
        
        if os.path.exists(chat_window_path):
            logger.info(f"Running Streamlit app: {chat_window_path}")
            print("🚀 Starting Streamlit server...")
            print("📱 App will open in your browser automatically")
            print("🌐 URL: http://localhost:8501")
            print("⏹️  Press Ctrl+C to stop")
            
            # Run streamlit
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", chat_window_path,
                "--server.port", "8501",
                "--server.address", "localhost",
                "--server.headless", "false"
            ])
        else:
            logger.error(f"Chat window file not found: {chat_window_path}")
            print(f"❌ File not found: {chat_window_path}")
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.critical(f"Application failed: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🏥 Medical Chatbot - Streamlit Version")
    print("=" * 50)
    main()
