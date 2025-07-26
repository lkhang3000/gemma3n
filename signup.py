# Medical Profile System (Backend)
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
