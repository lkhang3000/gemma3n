"""
Medical Chatbot - Streamlit App (Fixed Version)
"""
import streamlit as st
import warnings
import logging
import time
import sys
import os

# Suppress warnings
warnings.filterwarnings("ignore")
logging.getLogger("streamlit.runtime.scriptrunner.script_runner").setLevel(logging.ERROR)

# Set page config first
st.set_page_config(
    page_title="Medical Chatbot",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global flags
BACKEND_AVAILABLE = False
FORM_AVAILABLE = False

# Simple fallback chatbot for demo
class DemoChatbot:
    def __init__(self):
        self.conversation_history = []
        self.is_initialized = True
    
    def generate_response(self, user_input):
        """Generate demo response"""
        user_lower = user_input.lower()
        
        # Emergency keywords
        emergency_keywords = ["chest pain", "difficulty breathing", "heart attack", "stroke", "emergency"]
        if any(keyword in user_lower for keyword in emergency_keywords):
            return "🚨 EMERGENCY DETECTED!\n\n1. Call emergency services immediately (911/112/115)\n2. Do not wait for further instructions\n3. Follow operator guidance\n\n⚠️ This is a demo response. Please contact real emergency services!"
        
        # Greetings
        if any(word in user_lower for word in ["hi", "hello", "hey"]):
            return "Hello! I'm a medical chatbot assistant. I can provide general health information, but please consult healthcare professionals for serious conditions. How can I help you today?"
        
        # Form requests
        if any(phrase in user_lower for phrase in ["form", "doctor", "appointment"]):
            return "Medical form functionality would be available in the full version!"
            
        # General response
        return f"Thank you for your question about: '{user_input}'\n\n⚠️ This is a demo response. For real medical advice, please:\n\n1. Consult a healthcare professional\n2. Visit a medical clinic\n3. Call your local health hotline\n\nRunning in demo mode - full backend not available on Streamlit Cloud."
    
    def reset_conversation(self):
        self.conversation_history = []
        return True

# Try to import backend components
try:
    # Only import if files exist
    if os.path.exists("back_end") and os.path.exists("back_end/chatbot_backend.py"):
        from back_end.chatbot_backend import GUIChatbot
        BACKEND_AVAILABLE = True
except Exception as e:
    print(f"Backend not available: {e}")
    GUIChatbot = None

try:
    if os.path.exists("ui") and os.path.exists("ui/form_UI.py"):
        from ui.form_UI import Form
        FORM_AVAILABLE = True
except Exception as e:
    print(f"Form UI not available: {e}")
    Form = None

class SimpleChatApp:
    def __init__(self):
        # Initialize session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            self.add_message("Welcome to Medical Chatbot! 🏥", "assistant")
            if BACKEND_AVAILABLE:
                self.add_message("Full system loaded!", "assistant")
            else:
                self.add_message("Running in demo mode - Limited functionality", "assistant")
        
        if 'chatbot' not in st.session_state:
            if BACKEND_AVAILABLE:
                try:
                    st.session_state.chatbot = GUIChatbot(mode="local")
                except Exception as e:
                    print(f"Failed to initialize full chatbot: {e}")
                    st.session_state.chatbot = DemoChatbot()
            else:
                st.session_state.chatbot = DemoChatbot()
    
    def add_message(self, content, role):
        """Add message to chat history"""
        st.session_state.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.strftime("%H:%M:%S")
        })
    
    def clear_chat(self):
        """Clear chat history"""
        st.session_state.messages = []
        self.add_message("Chat cleared! 🧹", "assistant")
        st.rerun()
    
    def reset_conversation(self):
        """Reset conversation"""
        if hasattr(st.session_state.chatbot, 'reset_conversation'):
            st.session_state.chatbot.reset_conversation()
        st.session_state.messages = []
        self.add_message("Conversation reset! 🔄", "assistant")
        st.rerun()
    
    def render_sidebar(self):
        """Render sidebar"""
        with st.sidebar:
            st.title("🏥 Medical Chatbot")
            
            # Status
            st.subheader("Status")
            if BACKEND_AVAILABLE:
                st.success("🟢 Full System Active")
            else:
                st.warning("🟡 Demo Mode")
            
            st.divider()
            
            # Controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reset", use_container_width=True):
                    self.reset_conversation()
            with col2:
                if st.button("🧹 Clear", use_container_width=True):
                    self.clear_chat()
            
            # Information
            with st.expander("System Info", expanded=False):
                st.write(f"Backend: {'✅ Available' if BACKEND_AVAILABLE else '❌ Demo Only'}")
                st.write(f"Form: {'✅ Available' if FORM_AVAILABLE else '❌ Demo Only'}")
                st.write(f"Messages: {len(st.session_state.messages)}")
            
            # Demo form
            with st.expander("Medical Form (Demo)", expanded=False):
                with st.form("demo_form"):
                    name = st.text_input("Name:")
                    age = st.text_input("Age:")
                    symptoms = st.text_area("Symptoms:")
                    
                    if st.form_submit_button("Submit"):
                        if name and age:
                            st.success("Demo form submitted!")
                            self.add_message(f"Medical form submitted for {name} (Demo)", "assistant")
                        else:
                            st.error("Please fill required fields")
    
    def render_chat(self):
        """Render main chat"""
        st.title("Medical Assistant Chat")
        
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                st.caption(f"Time: {message['timestamp']}")
        
        # Chat input
        if prompt := st.chat_input("How can I help you today?"):
            # Add user message
            self.add_message(prompt, "user")
            
            # Generate response
            try:
                with st.spinner("Thinking..."):
                    response = st.session_state.chatbot.generate_response(prompt)
                    self.add_message(response, "assistant")
                    st.rerun()
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.add_message(error_msg, "assistant")
                st.rerun()
    
    def run(self):
        """Main app runner"""
        try:
            self.render_sidebar()
            self.render_chat()
        except Exception as e:
            st.error(f"App error: {str(e)}")
            st.write("Please refresh the page")

def main():
    """Main function"""
    try:
        app = SimpleChatApp()
        app.run()
    except Exception as e:
        st.error(f"Failed to start: {str(e)}")
        st.write("**Debug Info:**")
        st.write(f"Current directory: {os.getcwd()}")
        st.write(f"Python path: {sys.path[:3]}...")
        
        # Show file structure
        st.write("**File structure:**")
        for root, dirs, files in os.walk("."):
            if root.count(os.sep) < 3:  # Limit depth
                level = root.replace(".", "").count(os.sep)
                indent = "  " * level
                st.write(f"{indent}{os.path.basename(root)}/")
                subindent = "  " * (level + 1)
                for file in files[:5]:  # Limit files shown
                    st.write(f"{subindent}{file}")

if __name__ == "__main__":
    main()