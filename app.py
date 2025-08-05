"""
Medical Chatbot with gemma3n via Ollama - Fixed Version
"""
import streamlit as st
import requests
import warnings
import time

# Suppress warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Medical Chatbot with gemma3n",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model = "gemma3n"
        self.available = self._check_ollama()

    def _check_ollama(self):
        """Check if Ollama is running and gemma3n model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model.get("name", "") for model in models]
                
                # Check for exact gemma3n match or similar
                for name in model_names:
                    if "gemma3n" in name.lower() or "gemma" in name.lower():
                        self.model = name  # Use the actual model name found
                        return True
                return False
            return False
        except Exception as e:
            print(f"Ollama check failed: {e}")
            return False

    def generate_response(self, user_input, system_prompt):
        """Generate response using Ollama chat API"""
        if not self.available:
            return None
            
        try:
            # Prepare messages for chat API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 300
                },
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "").strip()
            else:
                print(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Ollama generation error: {e}")
            return None


class MedicalChatbot:
    def __init__(self):
        self.ollama = OllamaClient()
        self.history = []

    def generate_response(self, user_input):
        """Generate response using gemma3n or fallback"""
        user_input_lower = user_input.lower()
        
        # Emergency check first (always use rule-based for safety)
        for symptom in CRITICAL_SYMPTOMS:
            if symptom in user_input_lower:
                emergency_response = f"🚨 EMERGENCY: {symptom} detected!\n\n1. Call emergency services IMMEDIATELY (112 or 115)\n2. Do NOT wait for further instructions\n3. Follow operator guidance\n\nThis is a medical emergency - seek help now!"
                self.history.append({"user": user_input, "assistant": emergency_response})
                return emergency_response
        
        # Try Ollama/gemma3n first
        if self.ollama.available:
            try:
                response = self.ollama.generate_response(user_input, SYSTEM_PROMPT)
                if response:
                    full_response = f"{response}\n\n🤖 *Powered by {self.ollama.model} via Ollama*"
                    self.history.append({"user": user_input, "assistant": full_response})
                    return full_response
            except Exception as e:
                print(f"Ollama response error: {e}")
        
        # Fallback to rule-based responses
        fallback_response = self._fallback_response(user_input)
        self.history.append({"user": user_input, "assistant": fallback_response})
        return fallback_response

    def _fallback_response(self, user_input):
        """Rule-based fallback responses"""
        user_input_lower = user_input.lower()
        
        # Form requests
        if any(word in user_input_lower for word in ["form", "doctor", "contact", "appointment"]):
            return "📋 Medical Form Available In The Menu. Fill out the form and it will be sent to one of our trusted doctors."
        
        # Greetings
        if any(word in user_input_lower for word in ["hi", "hello", "hey", "good morning", "good afternoon"]):
            return "Hello! I'm a medical information assistant. How can I help you today? Please describe any symptoms or health concerns you have."
        
        # Common symptoms
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

    def reset_history(self):
        """Reset conversation history"""
        self.history = []

    def get_status(self):
        """Get chatbot status"""
        return {
            "ollama_available": self.ollama.available,
            "model": self.ollama.model if self.ollama.available else "None",
            "conversation_turns": len(self.history),
            "mode": f"AI ({self.ollama.model})" if self.ollama.available else "Fallback"
        }


def render_sidebar(bot):
    """Render sidebar with controls and medical form"""
    with st.sidebar:
        st.title("🏥 Medical Chatbot")
        
        # System Status
        status = bot.get_status()
        st.subheader("🔧 System Status")
        
        if status['ollama_available']:
            st.success(f"✅ {status['model']} Ready")
        else:
            st.warning("⚠️ Fallback Mode")
        
        st.write(f"**Mode:** {status['mode']}")
        st.write(f"**Model:** {status['model']}")
        st.write(f"**Conversations:** {status['conversation_turns']}")
        
        st.divider()
        
        # Controls
        st.subheader("🎛️ Controls")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Reset", use_container_width=True):
                bot.reset_history()
                st.session_state.chat_history = []
                st.rerun()
        
        with col2:
            if st.button("🧹 Clear", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        
        st.divider()
        
        # Medical Form
        st.subheader("📋 Medical Form")
        with st.form("medical_form"):
            st.write("**Patient Information**")
            name = st.text_input("Full Name*:")
            age = st.number_input("Age*:", min_value=0, max_value=120, value=25)
            
            st.write("**Medical Information**")
            symptoms = st.text_area("Describe your symptoms:", height=100)
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
                    st.session_state.chat_history.append({"role": "assistant", "content": form_summary})
                    st.rerun()
                else:
                    st.error("Please fill in all required fields (*)")
        
        st.divider()
        
        # Setup Instructions
        if not status['ollama_available']:
            with st.expander("🔧 Setup Ollama + gemma3n", expanded=False):
                st.write("**To enable AI responses:**")
                st.code("""
# 1. Install Ollama
# Visit: https://ollama.ai

# 2. Pull gemma3n model
ollama pull gemma3n

# 3. Start Ollama service
ollama serve

# 4. Restart this app
                """)


def main():
    """Main application function"""
    # Initialize chatbot
    bot = MedicalChatbot()

    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        status = bot.get_status()
        if status['ollama_available']:
            welcome_msg = f"🏥 Welcome to Medical Chatbot!\n✅ Connected to {status['model']} via Ollama\n🤖 AI-powered medical assistance ready!"
        else:
            welcome_msg = "🏥 Welcome to Medical Chatbot!\n⚠️ Running in demo mode (Ollama not available)\n💡 Install Ollama + gemma3n for full AI capabilities"
        
        st.session_state.chat_history.append({"role": "assistant", "content": welcome_msg})

    # Render sidebar
    render_sidebar(bot)

    # Main chat interface
    st.title("🤖 Medical Assistant Chat")
    
    # Show system status
    status = bot.get_status()
    if status['ollama_available']:
        st.success(f"🟢 AI Mode: {status['model']} via Ollama")
    else:
        st.warning("🟡 Demo Mode: Install Ollama + gemma3n for AI responses")

    # Display chat messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("How can I help you today?"):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Generating response..."):
                try:
                    response = bot.generate_response(prompt)
                    st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"❌ Error generating response: {str(e)}\n\nPlease try again or contact healthcare services if urgent."
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
        
        st.rerun()


if __name__ == "__main__":
    main()
