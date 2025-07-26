import streamlit as st
from datetime import datetime
import json
import os
import uuid

# Medical Profile System (Backend)
# Can be used to replace loginSystem import
class MedicalProfileSystem:
    def __init__(self):
        self.profiles_file = "medical_profiles.json"
        self.profiles = self._load_profiles()
    
    def _load_profiles(self):
        if os.path.exists(self.profiles_file):
            with open(self.profiles_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_profiles(self):
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f, indent=2)
    
    def create_profile(self, user_data):
        profile_id = str(uuid.uuid4())
        
        self.profiles[profile_id] = {
            "basic_info": {
                "name": user_data.get("name"),
                "age": user_data.get("age"),
                "gender": user_data.get("gender"),
                "created_date": datetime.now().strftime("%Y-%m-%d")
            },
            "medical_details": {},
            "conversation_history": []
        }
        self._save_profiles()
        return profile_id
    
    def update_medical_details(self, profile_id, details):
        if profile_id not in self.profiles:
            return False
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.profiles[profile_id]["medical_details"]:
            self.profiles[profile_id]["medical_details"][today] = []
        
        self.profiles[profile_id]["medical_details"][today].append({
            "detail": details,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        self._save_profiles()
        return True
    
    def add_conversation(self, profile_id, role, content):
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id]["conversation_history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self._save_profiles()
        return True
    
    def get_profile(self, profile_id):
        return self.profiles.get(profile_id)

# Streamlit UI (Frontend)
# Change signup(or form) to 
def main():
    st.title("Medical Chatbot with Profile System")
    profile_system = MedicalProfileSystem()
    
    # Initialize session state
    if 'profile_id' not in st.session_state:
        st.session_state.profile_id = None
    if 'show_profile' not in st.session_state:
        st.session_state.show_profile = False
    
    # Sign Up Form
    with st.sidebar:
        st.header("Create Medical Profile")
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=1, max_value=120)
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
            conditions = st.text_area("Existing Medical Conditions")
            
            if st.form_submit_button("Create Profile"):
                if name and age and gender:
                    profile_id = profile_system.create_profile({
                        "name": name,
                        "age": age,
                        "gender": gender,
                        "conditions": conditions
                    })
                    st.session_state.profile_id = profile_id
                    st.success("Profile created successfully!")
                else:
                    st.error("Please fill all required fields")
    
    # Chat Interface
    st.header("Chat with Medical Assistant")
    
    if st.session_state.profile_id:
        # Display conversation history
        profile = profile_system.get_profile(st.session_state.profile_id)
        
        for msg in profile["conversation_history"][-5:]:  # Show last 5 messages
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        # Chat input
        if prompt := st.chat_input("Describe your symptoms..."):
            # Add user message to history
            profile_system.add_conversation(
                st.session_state.profile_id,
                "user",
                prompt
            )
            
            # Detect medical details in user input
            medical_keywords = ["pain", "hurt", "symptom", "feel", "condition", "diagnos"]
            if any(keyword in prompt.lower() for keyword in medical_keywords):
                profile_system.update_medical_details(
                    st.session_state.profile_id,
                    f"User reported: {prompt}"
                )
            
            # Generate bot response (simplified for demo)
            bot_response = f"I've noted your symptoms: {prompt}. You should monitor these and consult a doctor if they persist."
            
            # Add bot response to history
            profile_system.add_conversation(
                st.session_state.profile_id,
                "assistant",
                bot_response
            )
            
            # Display new messages
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                st.write(bot_response)
        
        # Toggle for medical profile view
        if st.button("View/Update Medical Profile"):
            st.session_state.show_profile = not st.session_state.show_profile
        
        if st.session_state.show_profile:
            display_medical_profile(profile)
    else:
        st.warning("Please create a medical profile to start chatting")

def display_medical_profile(profile):
    st.header("Medical Profile")
    
    with st.expander("Basic Information"):
        st.write(f"**Name:** {profile['basic_info']['name']}")
        st.write(f"**Age:** {profile['basic_info']['age']}")
        st.write(f"**Gender:** {profile['basic_info']['gender']}")
        st.write(f"**Profile Created:** {profile['basic_info']['created_date']}")
    
    with st.expander("Medical Details"):
        if not profile['medical_details']:
            st.write("No medical details recorded yet")
        else:
            for date, details in profile['medical_details'].items():
                st.subheader(f"Date: {date}")
                for detail in details:
                    st.write(f"- {detail['timestamp']}: {detail['detail']}")
    
    with st.expander("Full Conversation History"):
        for msg in profile['conversation_history']:
            st.write(f"**{msg['role'].title()}** ({msg['timestamp']}): {msg['content']}")

if __name__ == "__main__":
    main()
