"""
Medical Chatbot with gemma3n via Ollama - Streamlit Cloud Version
"""
import streamlit as st
import time
import sys
import os
import warnings
import requests
import json

# Suppress warnings
warnings.filterwarnings("ignore")

# MUST be first Streamlit command
st.set_page_config(
    page_title="Medical Chatbot with gemma3n",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Medical prompts and data
SYSTEM_PROMPT = """You are a medical information assistant using the gemma3n model. Follow these rules:

1. EMERGENCY SYMPTOMS: If patient mentions chest pain, difficulty breathing, severe bleeding, heart attack, stroke symptoms, loss of consciousness, severe burns, choking, poisoning, or allergic reaction:
   → Respond: "🚨 EMERGENCY: [symptom] detected! Call emergency services IMMEDIATELY (112 or 115). Do NOT wait for further instructions."

2. MEDICAL FORM REQUESTS: If patient mentions "form", "doctor", "contact doctor", "see doctor", "severe condition":
   → Respond: "📋 Medical Form Available In The Menu. Fill out the form and it will be sent to one of our trusted doctors."

3. GENERAL SYMPTOMS: For other health concerns:
   → Provide helpful medical information
   → Suggest 2-3 possible causes
   → Recommend consulting healthcare professionals
   → Use empathetic language

4. GREETINGS: Respond warmly and ask how you can help.

Always end with: "Please consult a healthcare professional for proper diagnosis."
Never provide specific diagnoses or medication recommendations."""

CRITICAL_SYMPTOMS = [
    "chest pain", "difficulty breathing", "severe bleeding", "heart attack", 
    "stroke symptoms", "loss of consciousness", "severe burns", "choking", 
    "poisoning", "allergic reaction", "suicidal thoughts"
]

class OllamaClient:
    """Handle Ollama communication"""
    
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model = "gemma3n"
        self.available = self._check_ollama()
    
    def _check_ollama(self):
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                # Check for gemma3n specifically
                for name in model_names:
                    if 'gemma3n' in name.lower():
                        self.model = name
                        return True
                
                # Fallback to any gemma model
                for name in model_names:
                    if 'gemma' in name.lower():
                        self.model = name
                        return True
                        
                return False
            return False
        except Exception as e:
            print(f"Ollama check failed: {e}")
            return False
    
    def generate_response(self, prompt, system_prompt=None):
        """Generate response using Ollama API"""
        if not self.available:
            return None
            
        try:
            # Prepare the full prompt with system instructions
            full_prompt = f"{system_prompt}\n\nPatient: {prompt}\nDoctor:" if system_prompt else f"Patient: {prompt}\nDoctor:"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 300,
                    "stop": ["Patient:", "Human:"]
                },
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                print(f"Ollama API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Ollama generation error: {e}")
            return None
    
    def get_model_info(self):
        """Get current model information"""
        return {
            "model": self.model,
            "available": self.available,
            "base_url": self.base_url
        }

class MedicalChatbot:
    """Medical chatbot using gemma3n via Ollama"""
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.conversation_history = []
        self.model_info = self.ollama.get_model_info()
    
    def generate_response(self, user_input):
        """Generate response using gemma3n or fallback"""
        user_input_lower = user_input.lower()
        
        # Emergency check first (always use rule-based for safety)
        for symptom in CRITICAL_SYMPTOMS:
            if symptom in user_input_lower:
                return f"🚨 EMERGENCY: {symptom} detected!\n\n1. Call emergency services IMMEDIATELY (112 or 115)\n2. Do NOT wait for further instructions\n3. Follow operator guidance\n\nThis is a medical emergency - seek help now!"
        
        # Try gemma3n via Ollama first
        if self.ollama.available:
            try:
                response = self.ollama.generate_response(user_input, SYSTEM_PROMPT)
                if response:
                    # Add conversation to history
                    self.conversation_history.append({"user": user_input, "assistant": response})
                    return f"{response}\n\n🤖 *Response generated by {self.model_info['model']} via Ollama*"
            except Exception as e:
                print(f"Ollama response error: {e}")
        
        # Fallback to rule-based responses
        return self._fallback_response(user_input)
    
    def _fallback_response(self, user_input):
        """Rule-based fallback responses"""
        user_input_lower = user_input.lower()
        
        # Form requests
        if any(word in user_input_lower for word in ["form", "doctor", "contact", "appointment"]):
            return "📋 Medical Form Available In The Menu. Fill out the form and it will be sent to one of our trusted doctors."
        
        # Greetings
        if any(word in user_input_lower for word in ["hi", "hello", "hey", "good morning", "good afternoon"]):
            return "Hello! I'm a medical information assistant powered by gemma3n. How can I help you today? Please describe any symptoms or health concerns you have."
        
        # Common symptoms with medical advice
        if "headache" in user_input_lower:
            return """For headaches, consider these approaches:

**Immediate relief:**
- Rest in a quiet, dark room
- Apply cold or warm compress
- Stay hydrated
- Gentle neck/shoulder massage

**When to see a doctor:**
- Sudden, severe headaches
- Headaches with fever, stiff neck, or vision changes
- Persistent or worsening headaches

Please consult a healthcare professional for proper diagnosis.

⚠️ *Fallback response - Ollama/gemma3n not available*"""

        elif "fever" in user_input_lower:
            return """For fever management:

**Home care:**
- Rest and drink plenty of fluids
- Use fever reducers as directed
- Monitor temperature regularly
- Light, comfortable clothing

**Seek medical attention if:**
- Fever above 103°F (39.4°C)
- Fever with severe symptoms
- Fever in young children or elderly
- Persistent fever over 3 days

Please consult a healthcare professional for proper diagnosis.

⚠️ *Fallback response - Ollama/gemma3n not available*"""

        elif "cough" in user_input_lower:
            return """For cough relief:

**Home remedies:**
- Stay hydrated with warm liquids
- Use a humidifier
- Honey (for children over 1 year)
- Avoid irritants and smoke

**See a doctor if:**
- Cough produces blood
- Persistent cough over 2 weeks
- Cough with high fever
- Difficulty breathing

Please consult a healthcare professional for proper diagnosis.

⚠️ *Fallback response - Ollama/gemma3n not available*"""

        # Default response
        return f"""Thank you for your question about: "{user_input}"

For medical concerns, I recommend:
1. **Consulting with a healthcare professional** for proper evaluation
2. **Using the medical form** in the sidebar if you need to contact a doctor
3. **Calling emergency services (112/115)** if this is urgent

Please consult a healthcare professional for proper diagnosis and treatment.

⚠️ *Fallback response - Ollama/gemma3n not available. Install Ollama locally and pull gemma3n model for AI responses.*"""
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
    
    def get_status(self):
        """Get chatbot status"""
        return {
            "ollama_available": self.ollama.available,
            "model": self.model_info['model'],
            "conversation_turns": len(self.conversation_history),
            "mode": "AI (gemma3n)" if self.ollama.available else "Fallback"
        }

class ChatWindow:
    def __init__(self):
        # Initialize chatbot
        self.chatbot = MedicalChatbot()
        
        # Initialize session state
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state variables"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            
            # Welcome message based on system status
            status = self.chatbot.get_status()
            if status['ollama_available']:
                welcome_msg = f"🏥 Welcome to Medical Chatbot!\n✅ Connected to {status['model']} via Ollama\n🤖 AI-powered responses ready!"
            else:
                welcome_msg = "🏥 Welcome to Medical Chatbot!\n⚠️ Running in demo mode (Ollama not available)\n💡 Install Ollama + gemma3n for full AI capabilities"
            
            self.add_message(welcome_msg, "assistant")

    def add_message(self, content, role):
        """Add message to chat history"""
        st.session_state.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.strftime("%H:%M:%S")
        })

    def render_sidebar(self):
        """Render sidebar with controls and system info"""
        with st.sidebar:
            st.title("🏥 Medical Chatbot")
            
            # System Status
            status = self.chatbot.get_status()
            st.subheader("🔧 System Status")
            
            if status['ollama_available']:
                st.success(f"✅ {status['model']} Ready")
                st.write(f"**Mode:** AI-Powered")
            else:
                st.warning("⚠️ Demo Mode")
                st.write(f"**Mode:** Rule-based fallback")
            
            st.write(f"**Conversations:** {status['conversation_turns']}")
            
            st.divider()
            
            # Controls
            st.subheader("🎛️ Controls")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Reset", use_container_width=True):
                    self.reset_conversation()
            
            with col2:
                if st.button("🧹 Clear", use_container_width=True):
                    self.clear_chat()
            
            st.divider()
            
            # Medical Form
            st.subheader("📋 Medical Form")
            self._render_medical_form()
            
            st.divider()
            
            # Setup Instructions
            if not status['ollama_available']:
                with st.expander("🔧 Setup gemma3n", expanded=False):
                    st.write("**To enable AI responses:**")
                    st.code("""
# Install Ollama
# Visit: https://ollama.ai

# Pull gemma3n model
ollama pull gemma3n

# Start Ollama service
ollama serve
                    """)
                    st.write("Then restart this app!")

    def _render_medical_form(self):
        """Render medical form"""
        with st.form("medical_form"):
            st.write("**Patient Information**")
            name = st.text_input("Full Name*:")
            age = st.number_input("Age*:", min_value=0, max_value=120, value=25)
            gender = st.selectbox("Gender:", ["Male", "Female", "Other", "Prefer not to say"])
            
            st.write("**Medical Information**")
            symptoms = st.text_area("Describe your symptoms:", height=100)
            duration = st.selectbox("How long have you had these symptoms?", 
                                  ["Less than 1 day", "1-3 days", "1 week", "More than 1 week"])
            severity = st.selectbox("Pain/Discomfort level (1-10):", 
                                  ["1-2 (Mild)", "3-4 (Moderate)", "5-6 (Noticeable)", 
                                   "7-8 (Severe)", "9-10 (Extreme)"])
            urgency = st.selectbox("How urgent is this?", 
                                 ["Non-urgent", "Somewhat urgent", "Very urgent", "Emergency"])
            
            if st.form_submit_button("📋 Submit Form", use_container_width=True):
                if name and age and symptoms:
                    if urgency == "Emergency":
                        st.error("🚨 EMERGENCY: Please call emergency services (112/115) immediately!")
                    elif urgency == "Very urgent":
                        st.warning("⚠️ URGENT: Please contact healthcare provider immediately!")
                    else:
                        st.success("✅ Form submitted successfully!")
                    
                    # Add form submission to chat
                    form_summary = f"Medical form submitted:\n**Patient:** {name}, {age} years old\n**Symptoms:** {symptoms}\n**Urgency:** {urgency}"
                    self.add_message(form_summary, "assistant")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields (*)")

    def clear_chat(self):
        """Clear chat history"""
        st.session_state.messages = []
        self.add_message("Chat cleared! 🧹", "assistant")
        st.rerun()

    def reset_conversation(self):
        """Reset conversation"""
        self.chatbot.reset_conversation()
        st.session_state.messages = []
        status = self.chatbot.get_status()
        if status['ollama_available']:
            welcome_msg = f"🔄 Conversation reset!\n✅ {status['model']} ready to help"
        else:
            welcome_msg = "🔄 Conversation reset!\n⚠️ Demo mode active"
        self.add_message(welcome_msg, "assistant")
        st.rerun()

    def render_chat(self):
        """Render main chat interface"""
        st.title("🤖 Medical Assistant Chat")
        
        # Show system status
        status = self.chatbot.get_status()
        if status['ollama_available']:
            st.success(f"🟢 AI Mode: {status['model']} via Ollama")
        else:
            st.warning("🟡 Demo Mode: Install Ollama + gemma3n for AI responses")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "timestamp" in message:
                    st.caption(f"⏰ {message['timestamp']}")
        
        # Chat input
        if prompt := st.chat_input("How can I help you today?"):
            # Add user message
            self.add_message(prompt, "user")
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate and display response
            with st.chat_message("assistant"):
                with st.spinner("🤖 Generating response..."):
                    try:
                        response = self.chatbot.generate_response(prompt)
                        st.write(response)
                        self.add_message(response, "assistant")
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}\n\nPlease try again or contact support."
                        st.error(error_msg)
                        self.add_message(error_msg, "assistant")
            
            st.rerun()

    def run(self):
        """Main app runner"""
        try:
            self.render_sidebar()
            self.render_chat()
        except Exception as e:
            st.error(f"❌ Application error: {str(e)}")
            st.write("Please refresh the page.")

def main():
    """Main function"""
    try:
        app = ChatWindow()
        app.run()
    except Exception as e:
        st.error(f"❌ Failed to start Medical Chatbot: {str(e)}")
        
        # Debug information
        st.write("**Debug Information:**")
        st.write(f"Current directory: {os.getcwd()}")
        st.write(f"Python version: {sys.version}")
        
        # Show how to set up properly
        st.subheader("🔧 Setup Instructions")
        st.write("**For full AI functionality:**")
        st.code("""
# 1. Install Ollama locally
# Download from: https://ollama.ai

# 2. Pull gemma3n model
ollama pull gemma3n

# 3. Start Ollama service
ollama serve

# 4. Run this Streamlit app
streamlit run app.py
        """)

if __name__ == "__main__":
    main()