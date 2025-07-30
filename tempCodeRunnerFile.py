import sys
import os
import logging

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
        logger.info("Starting Medical Chatbot with modular architecture...")
        
        from ui.chat_window import ChatWindow
        
        app = ChatWindow()
        app.run()
        
    except Exception as e:
        logger.critical(f"Application failed: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🏥 Medical Chatbot - Modular Version")
    main()
