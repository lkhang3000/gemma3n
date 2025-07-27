# Test integration between UI and Backend with local gemma:2b model
from ui.chat_window import ChatWindow

if __name__ == "__main__":
    print("Starting Gemma Chatbot with Local Model...")
    app = ChatWindow()
    app.run()
