#Check UI(just have a quick look at it)
#Check the Chatbot logic( to see if there any problem with the form)
#1. Does the form updated the user's medical information correctly. 
#2. Does the chatbot has the ability to detect which one should be added
#Check if the sign up recognize user by their name+age+gender(because there are more than one judges will see our code so I can't make the sign up to just be used by 1 user)
#Some recommendation: We can have a line that say "This information will help the chatbot to create the medical profile, save conversation to history,..., For the best experience, please sign up"
#Merge medicalchatbot into GUIchatbot(I can't do this because some frontends are using backend logic, so while you editing the GUIchatbot, you can change these code base on your editing)
import streamlit as st
from datetime import datetime
from typing import List, Dict
import ollama

# --- User Profile ---
class UserProfile:
    def __init__(self, name: str, age: int, gender: str):
        self.name = name
        self.age = age
        self.gender = gender
        self.details_by_date: Dict[str, List[str]] = {}

    def update_detail(self, new_detail: str):
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.details_by_date:
            self.details_by_date[today] = []
        self.details_by_date[today].append(new_detail)

    def get_summary(self) -> str:
        lines = [
            f"👤 Name: {self.name}",
            f"🎂 Age: {self.age}",
            f"⚧ Gender: {self.gender}",
            "📝 Health Notes:"
        ]
        for date, entries in sorted(self.details_by_date.items()):
            lines.append(f"📅 {date}:")
            for d in entries:
                lines.append(f"  - {d}")
        return "\n".join(lines)

# --- ChatBot Logic ---
#class MedicalChatBot:
  #  def __init__(self, system_prompt: str):
 #       self.conversation_history = [{"role": "system", "content": system_prompt}]
#
    #def _add_to_history(self, role: str, content: str):
   #     self.conversation_history.append({"role": role, "content": content})
  #      if len(self.conversation_history) > 7:
 #           self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-6:]
#
    #def generate_response(self, user_input: str) -> str:
        #self._add_to_history("user", user_input)
       # prompt = self._format_prompt()
      #  try:
         #   response = ollama.generate(
        #        model="gemma3n:e2b",
       #         prompt=prompt,
      #          options={"temperature": 0.3}
     #       )["response"]
    #    except Exception as e:
   #         response = f"❌ Error generating response: {e}"
  #      self._add_to_history("assistant", response)
 #       return response
#
    #def _format_prompt(self) -> str:
    #    return "\n".join(
   #         f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
  #          for m in self.conversation_history[1:]
 #       ) + "\nAssistant:"
#MMay delete this part when merging to GUIchatbot
    def is_medical_input(self, message: str) -> bool:
        classify_prompt = (
            f"Does the following message contain medical information "
            f"that should be saved to a medical profile?\n"
            f"Only answer 'yes' or 'no'.\n\n"
            f"Message: \"{message}\""
        )
        try:
            response = ollama.generate(
                model="gemma3n:e2b",
                prompt=classify_prompt,
                options={"temperature": 0.2}
            )["response"].strip().lower()
            return response.startswith("yes")
        except Exception as e:
            st.error(f"❌ Classification error: {e}")
            return False

# --- System Setup ---
#st.set_page_config("Medical Chatbot", page_icon="🧬")
#st.title("🩺 Medical Chatbot with Auto Health Profile (Gemma)")

#SYSTEM_PROMPT = (
#  you are a medical assistant. Follow strict safety rules:\n"
 #  "   If present, reply only with: '🚨 EMERGENCY: Call local emergency services.'\n"
  #  "2. Otherwise:\n"
   # "   - Suggest possible causes (2-3)\n"
    #"   - Recommend actions (1-2)\n"
    #"   - Always say: 'Consult a healthcare professional.'\n"
    #"3. Never give a diagnosis or medication name."
#)
#Can be deleted if overlap with the lastest code

# --- Session State ---
if "chatbot" not in st.session_state:
    st.session_state.chatbot = MedicalChatBot(SYSTEM_PROMPT)
if "users" not in st.session_state:
    st.session_state.users: Dict[str, UserProfile] = {}
if "active_user" not in st.session_state:
    st.session_state.active_user = ""
if "show_profile" not in st.session_state:
    st.session_state.show_profile = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sign Up Without Email ---
with st.expander("📝 Sign Up"):
    with st.form("signup"):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=0, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        submitted = st.form_submit_button("Register or Log In")

        if submitted:
            if not name:
                st.warning("Name is required.")
            else:
                # Create a unique ID from basic info
                user_key = f"{name.lower()}_{age}_{gender.lower()}"
                if user_key not in st.session_state.users:
                    st.session_state.users[user_key] = UserProfile(name, age, gender)
                st.session_state.active_user = user_key
                st.success(f"User {name} is now active.")

# --- Chat UI ---
st.subheader("💬 Chat")
if not st.session_state.active_user:
    st.info("Please sign up or log in first.")
else:
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("Your message:")
    with col2:
        if st.button("📋 Show Profile"):
            st.session_state.show_profile = True

    if user_input:
        user_key = st.session_state.active_user
        profile = st.session_state.users[user_key]
        bot = st.session_state.chatbot

        reply = bot.generate_response(user_input)

        st.session_state.messages.append(("🧑", user_input))
        st.session_state.messages.append(("🤖", reply))

        if bot.is_medical_input(user_input):
            profile.update_detail(user_input)

# --- Display Chat Messages ---
for speaker, msg in st.session_state.messages:
    st.markdown(f"**{speaker}**: {msg}")

# --- View Profile On Demand ---
if st.session_state.show_profile:
    user_key = st.session_state.active_user
    profile = st.session_state.users[user_key]
    st.subheader("📋 Medical Profile")
    st.text_area("Health Summary", profile.get_summary(), height=300)
