import streamlit as st
import time
import queue
import threading
import sys
import os
from back_end.form import Form

try:
    from back_end.chatbot_backend import GUIChatbot
    BACKEND_AVAILABLE = True
    print("✅ Backend imported successfully")
except ImportError as e:
    print(f"❌ Backend import error: {e}")
    BACKEND_AVAILABLE = False

class ChatWindow:
    def __init__(self):
        st.set_page_config(
            page_title="Medical Chatbot",
            page_icon="🏥",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        self.is_model_loaded = False
        self.response_queue = queue.Queue()
        self.is_generating = False
        
        # Initialize medical form system
        self.medicalForm = Form()
        
        # Initialize chatbot backend
        if BACKEND_AVAILABLE:
            try:
                self.chatbot = GUIChatbot(
                    mode="auto",
                    status_callback=self.update_status,
                    progress_callback=self.update_progress
                )
                print("✅ Chatbot initialized")
            except Exception as e:
                print(f"❌ Chatbot initialization error: {e}")
                self.chatbot = None
        else:
            self.chatbot = None
            
        # Initialize session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            self.add_message("Welcome to Medical Chatbot! 🏥", "system")
            if BACKEND_AVAILABLE and self.chatbot:
                self.add_message("System initializing...", "system")
            else:
                self.add_message("⚠️ Backend not available - Running in demo mode", "system")
                
        if 'status' not in st.session_state:
            st.session_state.status = "System has not been initialized, please wait..."
            
        if 'progress' not in st.session_state:
            st.session_state.progress = 0

    def add_message(self, message, sender):
        """Add message to chat history"""
        if sender == "user":
            avatar = "👤"
            prefix = "You"
        elif sender == "system":
            avatar = "🔔"
            prefix = "System"
        else:  # ai
            avatar = "🤖"
            prefix = "Medical AI"
            
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {avatar} {prefix}: {message}"
        
        st.session_state.messages.append({
            "role": sender,
            "content": message,
            "avatar": avatar,
            "full": full_message
        })

    def update_status(self, status_text):
        """Update status from backend"""
        st.session_state.status = status_text

    def update_progress(self, progress_value):
        """Update progress from backend"""
        st.session_state.progress = progress_value

    def clear_chat(self):
        """Clear chat history"""
        st.session_state.messages = []
        self.add_message("Chat cleared. �", "system")

    def reset_conversation(self):
        """Reset the conversation in backend and clear chat"""
        if self.chatbot and BACKEND_AVAILABLE:
            try:
                self.chatbot.reset_conversation()
                st.session_state.messages = []
                self.add_message("Chat conversation has been reset. You can start over! 🔄", "system")
            except Exception as e:
                self.add_message(f"❌ Error resetting conversation: {str(e)}", "system")
        else:
            self.clear_chat()
            self.add_message("Demo reset successful! 🔄", "system")

    def show_chat_history(self):
        """Show conversation history in a popup"""
        if self.chatbot and BACKEND_AVAILABLE:
            try:
                status = self.chatbot.get_status()
                history_info = f"Status: {'Initialized' if status['initialized'] else 'Uninitialized'}\n"
                history_info += f"Mode: {status['mode']}\n"
                if 'model' in status:
                    history_info += f"Model: {status['model']}\n"
                history_info += f"Number of chats: {status['conversation_turns']}\n\n"
                
                st.sidebar.text_area("Chat History Info", history_info, height=200)
            except Exception as e:
                st.sidebar.error(f"Cannot show chat history: {str(e)}")
        else:
            st.sidebar.info("No history to show")

    def show_system_info(self):
        """Show system information"""
        if self.chatbot and BACKEND_AVAILABLE:
            try:
                requirements = self.chatbot.get_system_requirements()
                
                if "error" in requirements:
                    info_content = f"❌ Error: {requirements['error']}"
                else:
                    current = requirements['current_specs']
                    recommended = requirements['recommended_specs']
                    meets = requirements['meets_requirements']
                    
                    info_content = "=== SYSTEM INFORMATION ===\n\n"
                    info_content += "Current specs:\n"
                    info_content += f"• CPU Cores: {current['cpu_cores']} ({'✅' if meets['cpu'] else '❌'} {recommended['cpu_cores']} recommended)\n"
                    info_content += f"• RAM: {current['ram_gb']}GB ({'✅' if meets['ram'] else '❌'} {recommended['ram_gb']}GB recommended)\n"
                    info_content += f"• AVX Support: {'✅' if current['has_avx'] else '❌'}\n"
                    info_content += f"• OS: {current['os_type']}\n\n"
                    
                    info_content += f"Meets requirements: {'✅ Yes' if meets['overall'] else '❌ No'}\n\n"
                    
                    info_content += "Performance improvement suggestions:\n"
                    for tip in requirements['performance_tips']:
                        info_content += f"• {tip}\n"
                
                st.sidebar.text_area("System Information", info_content, height=400)
            except Exception as e:
                st.sidebar.error(f"Cannot show system information: {str(e)}")
        else:
            system_info = f"Backend: ❌ Not available\nOllama: Not checked\nPython: {sys.version}\nOS: {os.name}"
            st.sidebar.info(system_info)

    def show_medical_form(self):
        """Show medical form popup"""
        with st.sidebar.form("medical_form"):
            st.subheader("Create Medical Form")
            
            name = st.text_input("Name:", placeholder="Enter your name")
            age = st.text_input("Age:", placeholder="Enter your age")
            
            submitted = st.form_submit_button("Submit")
            
            if submitted:
                if not name or not age:
                    st.error("Please fill in all fields")
                    return
                
                new_user = self.medicalForm.signUp(name, age)
                st.success("Saved successfully!")

    def send_message(self, user_input):
        """Handle sending a message"""
        if not user_input.strip():
            return
            
        if self.is_generating:
            self.add_message("⚠️ We're working on the previous message, please wait...", "system")
            return
            
        self.add_message(user_input, "user")
        
        # Disable send button to prevent spam
        self.is_generating = True
        
        # Use backend if available
        if self.chatbot and BACKEND_AVAILABLE:
            # Show "thinking" message
            thinking_msg = "🤔 Analyzing..."
            self.add_message(thinking_msg, "system")
            
            # Generate response asynchronously
            def response_callback(response):
                try:
                    # Remove "thinking" message by getting current content and removing last system message
                    if st.session_state.messages and st.session_state.messages[-1]["content"] == thinking_msg:
                        st.session_state.messages.pop()
                    
                    # Add AI response
                    self.add_message(response, "ai")
                    
                except Exception as e:
                    print(f"Error in response callback: {e}")
                    self.add_message(f"❌ Error showing response: {str(e)}", "system")
                
                finally:
                    # Re-enable send button
                    self.is_generating = False
            
            self.chatbot.generate_response_async(user_input, response_callback)
        else:
            # Fallback to simple response if backend not available
            def simple_response():
                try:
                    time.sleep(1)
                    if any(keyword in user_input.lower() for keyword in ["chest pain", "difficulty breathing", "heart attack"]):
                        response = "🚨 WARNING: The symptoms you described above can be serious!\n\n1. Please contact medical help immediately (115)\n2. Please do not hesitate with the help of a medical team.\n\n"
                    elif "hi" in user_input.lower() or "hello" in user_input.lower():
                        response = "Greetings, I am Medical Chatbot. I can provide you with necessary medical knowledge, but please directly consult a medical expert in urgent situations."
                    else:
                        response = f"⚠️ Backend not available.\n\nYou said: '{user_input}'\n"
                    
                    self.add_message(response, "ai")
                    
                except Exception as e:
                    self.add_message(f"❌ Response generating error: {str(e)}", "system")
                
                finally:
                    self.is_generating = False
            
            threading.Thread(target=simple_response, daemon=True).start()

    def render(self):
        """Render the Streamlit UI"""
        # Sidebar with controls
        with st.sidebar:
            st.title("Medical Chatbot Controls")
            
            if st.button("Chat History"):
                self.show_chat_history()
                
            if st.button("System Info"):
                self.show_system_info()
                
            if st.button("Reset Chat"):
                self.reset_conversation()
                
            if st.button("Clear Chat"):
                self.clear_chat()
                
            if st.button("Create Medical Form"):
                self.show_medical_form()
            
            # Status information
            st.divider()
            st.subheader("System Status")
            st.write(st.session_state.status)
            st.progress(st.session_state.progress)

        # Main chat area
        st.title("Medical Chatbot 🏥")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=message["avatar"]):
                st.write(message["content"])
        
        # User input
        if prompt := st.chat_input("How are you doing?..."):
            self.send_message(prompt)

    def run(self):
        """Run the Streamlit application"""
        try:
            print("🚀 Starting Medical Chatbot (Streamlit)...")
            self.render()
        except Exception as e:
            st.error(f"Critical error: {str(e)}")

if __name__ == "__main__":
    try:
        app = ChatWindow()
        app.run()
    except Exception as e:
        st.error(f"Application startup error: {str(e)}")