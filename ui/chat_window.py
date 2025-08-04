import warnings
import logging
import streamlit as st
import time
import threading
import sys
import os

# Suppress warnings
warnings.filterwarnings("ignore")
logging.getLogger("streamlit.runtime.scriptrunner.script_runner").setLevel(logging.ERROR)

# Global flags
BACKEND_AVAILABLE = False
FORM_AVAILABLE = False

# Try to import backend and form
try:
    from form_UI import Form
    FORM_AVAILABLE = True
except ImportError as e:
    print(f"Form UI not available: {e}")
    Form = None

try:
    from back_end.chatbot_backend import GUIChatbot
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"Backend not available: {e}")
    GUIChatbot = None

class ChatWindow:
    def __init__(self):
        # Set page config first
        if 'page_configured' not in st.session_state:
            st.set_page_config(
                page_title="Medical Chatbot",
                layout="wide",
                initial_sidebar_state="expanded"
            )
            st.session_state.page_configured = True
        
        # Initialize components
        self.chatbot = None
        self.medicalForm = None
        
        # Try to initialize backend
        if BACKEND_AVAILABLE:
            try:
                self.chatbot = GUIChatbot(
                    mode="local",
                    status_callback=self.update_status,
                    progress_callback=self.update_progress
                )
            except Exception as e:
                print(f"Chatbot initialization failed: {e}")
                self.chatbot = None
        
        # Try to initialize form
        if FORM_AVAILABLE and Form:
            try:
                self.medicalForm = Form()
            except Exception as e:
                print(f"Form initialization failed: {e}")
                self.medicalForm = None
        
        # Initialize session state
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize all session state variables"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            self.add_message("Welcome to Medical Chatbot! 🏥", "system")
            if self.chatbot:
                self.add_message("System ready! You can start chatting.", "system")
            else:
                self.add_message("Running in demo mode - Backend not available", "system")
                
        if 'status' not in st.session_state:
            st.session_state.status = "System ready" if self.chatbot else "Demo mode"
            
        if 'progress' not in st.session_state:
            st.session_state.progress = 1.0 if self.chatbot else 0.5

        if 'is_generating' not in st.session_state:
            st.session_state.is_generating = False

    def add_message(self, message, sender):
        """Add message to chat history"""
        avatars = {
            "user": "👤",
            "system": "🔔", 
            "ai": "🤖"
        }
        
        avatar = avatars.get(sender, "💬")
        timestamp = time.strftime("%H:%M:%S")
        
        st.session_state.messages.append({
            "role": sender,
            "content": message,
            "avatar": avatar,
            "timestamp": timestamp
        })

    def update_status(self, status_text):
        """Update status from backend"""
        try:
            st.session_state.status = status_text
        except:
            pass

    def update_progress(self, progress_value):
        """Update progress from backend"""
        try:
            st.session_state.progress = progress_value
        except:
            pass

    def clear_chat(self):
        """Clear chat history"""
        st.session_state.messages = []
        self.add_message("Chat cleared! 🧹", "system")
        st.rerun()

    def reset_conversation(self):
        """Reset the conversation"""
        if self.chatbot and hasattr(self.chatbot, 'reset_conversation'):
            try:
                self.chatbot.reset_conversation()
                st.session_state.messages = []
                self.add_message("Conversation reset! You can start over. 🔄", "system")
            except Exception as e:
                self.add_message(f"Reset error: {str(e)}", "system")
        else:
            st.session_state.messages = []
            self.add_message("Demo conversation reset! 🔄", "system")
        st.rerun()

    def show_system_info(self):
        """Show system information in sidebar"""
        with st.sidebar.expander("System Information", expanded=False):
            if self.chatbot and hasattr(self.chatbot, 'get_system_requirements'):
                try:
                    requirements = self.chatbot.get_system_requirements()
                    if "error" not in requirements:
                        current = requirements.get('current_specs', {})
                        st.write(f"CPU Cores: {current.get('cpu_cores', 'Unknown')}")
                        st.write(f"RAM: {current.get('ram_gb', 'Unknown')}GB")
                        st.write(f"OS: {current.get('os_type', 'Unknown')}")
                    else:
                        st.write("System info not available")
                except:
                    st.write("Cannot retrieve system info")
            else:
                st.write("Backend: ❌ Not available")
                st.write(f"Form: {'✅' if self.medicalForm else '❌'}")

    def show_medical_form(self):
        """Show medical form in sidebar"""
        with st.sidebar.expander("Medical Form", expanded=False):
            if self.medicalForm:
                with st.form("medical_form"):
                    st.write("Fill out this form to contact a doctor:")
                    name = st.text_input("Name:")
                    age = st.text_input("Age:")
                    symptoms = st.text_area("Symptoms:")
                    
                    if st.form_submit_button("Submit Form"):
                        if name and age:
                            try:
                                # Assuming signUp method exists
                                result = self.medicalForm.signUp(name, age)
                                st.success("Form submitted successfully! ✅")
                                self.add_message(f"Medical form submitted for {name}", "system")
                            except Exception as e:
                                st.error(f"Form submission error: {str(e)}")
                        else:
                            st.error("Please fill in required fields")
            else:
                st.write("Medical form not available in demo mode")

    def generate_demo_response(self, user_input):
        """Generate demo response when backend is not available"""
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
            return "Medical form is available in the sidebar! Please fill it out to contact our medical team."
            
        # General medical questions
        return f"Thank you for your question: '{user_input}'\n\n⚠️ This is a demo response. For real medical advice, please:\n\n1. Consult a healthcare professional\n2. Visit a medical clinic\n3. Call your local health hotline\n\nI'm running in demo mode as the backend is not available."

    def send_message(self, user_input):
        """Handle sending a message"""
        if not user_input.strip():
            return
            
        if st.session_state.is_generating:
            st.warning("Please wait for the current response to complete...")
            return
            
        # Add user message
        self.add_message(user_input, "user")
        
        # Set generating flag
        st.session_state.is_generating = True
        
        if self.chatbot and BACKEND_AVAILABLE:
            # Use real backend
            def response_callback(response):
                try:
                    self.add_message(response, "ai")
                    st.session_state.is_generating = False
                    st.rerun()
                except Exception as e:
                    self.add_message(f"Response error: {str(e)}", "system")
                    st.session_state.is_generating = False
                    st.rerun()
            
            def generate_response():
                try:
                    if hasattr(self.chatbot, 'generate_response_async'):
                        self.chatbot.generate_response_async(user_input, response_callback)
                    else:
                        response = self.chatbot.generate_response(user_input)
                        response_callback(response)
                except Exception as e:
                    response_callback(f"Backend error: {str(e)}")
            
            threading.Thread(target=generate_response, daemon=True).start()
            
        else:
            # Use demo response
            def demo_response():
                time.sleep(1)  # Simulate thinking
                response = self.generate_demo_response(user_input)
                self.add_message(response, "ai")
                st.session_state.is_generating = False
                st.rerun()
            
            threading.Thread(target=demo_response, daemon=True).start()

    def render_sidebar(self):
        """Render sidebar controls"""
        with st.sidebar:
            st.title("🏥 Medical Chatbot")
            
            # Status
            st.subheader("Status")
            status_color = "🟢" if self.chatbot else "🟡"
            st.write(f"{status_color} {st.session_state.status}")
            
            if st.session_state.progress > 0:
                st.progress(st.session_state.progress)
            
            st.divider()
            
            # Controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reset", use_container_width=True):
                    self.reset_conversation()
                    
            with col2:
                if st.button("🧹 Clear", use_container_width=True):
                    self.clear_chat()
            
            # Information sections
            self.show_system_info()
            self.show_medical_form()
            
            # Chat statistics
            st.divider()
            st.write(f"💬 Messages: {len(st.session_state.messages)}")
            st.write(f"🤖 Backend: {'✅' if self.chatbot else '❌'}")

    def render_chat(self):
        """Render main chat interface"""
        st.title("Medical Chatbot Assistant 🏥")
        
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=message["avatar"]):
                st.write(message["content"])
                if "timestamp" in message:
                    st.caption(f"Time: {message['timestamp']}")
        
        # Input area
        if st.session_state.is_generating:
            st.chat_input("Generating response, please wait...", disabled=True)
        else:
            if prompt := st.chat_input("How can I help you today?"):
                self.send_message(prompt)

    def run(self):
        """Main app runner"""
        try:
            self.render_sidebar()
            self.render_chat()
        except Exception as e:
            st.error(f"Application error: {str(e)}")
            st.write("Please refresh the page or contact support.")

try:
    app = ChatWindow()
    app.run()
except Exception as e:
    st.error(f"Failed to start application: {str(e)}")
    st.write("Please check your configuration and try again.")

