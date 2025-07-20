SYSTEM_PROMPT = """You are a medical information assistant. Strict rules:
1. Critical Symptoms ({critical_list}) → Respond ONLY with: "EMERGENCY: [standard emergency instructions]"
2. For non-emergencies:
   - Suggest 2-3 POSSIBLE causes
   - List 1-2 recommended actions
   - Always add: "Consult a healthcare professional"
3. Never:
   - Provide diagnoses
   - Recommend specific medications
   - Suggest delaying care for serious symptoms"""

CRITICAL_SYMPTOMS = {
    "chest pain", "difficulty breathing", "severe bleeding",
    "sudden numbness", "loss of consciousness", "stroke symptoms",
    "suicidal thoughts", "severe burns", "choking"
}

# Response templates
RESPONSE_TEMPLATES = {
    "emergency": (
        "🚨 EMERGENCY: {symptom} detected\n"
        "1. Call local emergency services IMMEDIATELY\n"
        "2. Do NOT wait for further instructions\n"
        "3. Follow operator guidance\n"
        "Nearest hospital: {hospital_info}"
    ),
    "normal": (
        "Possible causes for your symptoms:\n"
        "- {cause_1}\n"
        "- {cause_2}\n\n"
        "Recommended actions:\n"
        "1. {action_1}\n"
        "2. {action_2}\n\n"
        "ℹ️ Always consult a healthcare professional for persistent symptoms."
    )
}

DISCLAIMER = "\n🔒 Privacy Note: {mode_detail}"
