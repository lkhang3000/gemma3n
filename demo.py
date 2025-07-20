###############################
### 1. BACKEND INFRASTRUCTURE ###
###############################

# Standard library imports
import os
import sys
import time
from typing import List, Dict, Optional, Tuple

# Third-party imports
import ollama
import requests
import psutil
import platform
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("medical_chatbot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

##############################
### 2. PROMPT ENGINEERING ###
##############################

# Medical safety constraints
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

##########################
### 3. CORE CHATBOT CLASS ###
##########################

class MedicalChatbot:
    def __init__(self, mode: str = "auto", server_url: Optional[str] = None):
        """
        Initialize chatbot with hardware-aware configuration
        
        Args:
            mode: 'local' (Ollama), 'server' (remote), or 'auto'
            server_url: Custom Ollama server URL
        """
        self.mode = self._validate_mode(mode)
        self.server_url = server_url or "http://localhost:11434"
        self.conversation_history: List[Dict[str, str]] = []
        self._initialize_system()
        self._warn_if_unsupported_hardware()

    def _validate_mode(self, mode: str) -> str:
        """Ensure valid operation mode is selected"""
        valid_modes = ("local", "server", "auto")
        if mode.lower() not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be: {valid_modes}")
        return mode.lower()

    def _initialize_system(self) -> None:
        """Initialize system with hardware detection"""
        # Hardware capabilities
        self.system_info = {
            "cpu_cores": psutil.cpu_count(logical=False) or 1,
            "ram_gb": psutil.virtual_memory().total / (1024 ** 3),
            "has_avx": self._check_cpu_instructions(),
            "os_type": platform.system()
        }

        # Mode configuration
        if self.mode == "auto":
            self.mode = self._determine_optimal_mode()

        # Privacy notices
        self.mode_details = {
            "local": "All processing occurs on your local device",
            "server": "Responses are processed on a secure server"
        }

        # Initialize conversation
        self.conversation_history = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(
                    critical_list=", ".join(sorted(CRITICAL_SYMPTOMS))
            }
        ]

        logger.info(f"System initialized in {self.mode} mode")

    def _check_cpu_instructions(self) -> bool:
        """Verify CPU supports required instructions (AVX)"""
        try:
            import cpuinfo
            cpu_flags = cpuinfo.get_cpu_info().get('flags', [])
            return 'avx' in cpu_flags
        except Exception as e:
            logger.warning(f"CPU check failed: {str(e)}")
            return True  # Assume supported if check fails

    def _determine_optimal_mode(self) -> str:
        """Automatically select best operation mode"""
        min_local_requirements = (
            self.system_info["cpu_cores"] >= 4
            and self.system_info["ram_gb"] >= 8
            and self.system_info["has_avx"]
        )
        return "local" if min_local_requirements else "server"

    def _warn_if_unsupported_hardware(self) -> None:
        """Notify user about potential performance issues"""
        if self.mode == "local":
            warnings = []
            if self.system_info["cpu_cores"] < 4:
                warnings.append(f"Limited CPU cores ({self.system_info['cpu_cores']}/4 recommended)")
            if self.system_info["ram_gb"] < 8:
                warnings.append(f"Limited RAM ({self.system_info['ram_gb']:.1f}GB/8GB recommended)")
            if not self.system_info["has_avx"]:
                warnings.append("Missing AVX CPU instructions (required for optimal performance)")

            if warnings:
                warning_msg = "⚠️ Offline Mode Performance Warning:\n" + "\n".join(f"- {w}" for w in warnings)
                print(warning_msg)
                if input("Continue with offline mode? (y/n): ").lower() != 'y':
                    self.mode = "server"
                    print("Switched to server mode")
                    logger.info("User opted to switch to server mode due to hardware limitations")

    def _add_to_conversation(self, role: str, content: str) -> None:
        """Manage conversation history with rolling window"""
        self.conversation_history.append({"role": role, "content": content})
        
        # Maintain 6-turn memory (3 user + 3 assistant) plus system prompt
        if len(self.conversation_history) > 7:  # system + 6 turns
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-6:]

    def _format_for_llm(self) -> str:
        """Engineer the final prompt sent to the LLM"""
        conversation = [
            f"{'Patient' if msg['role'] == 'user' else 'Doctor'}: {msg['content']}"
            for msg in self.conversation_history[1:]  # Skip system prompt
        ]
        return "\n".join(conversation) + "\nDoctor:"  # Force response style

    def _detect_emergency(self, text: str) -> Tuple[bool, Optional[str]]:
        """Pre-LLM critical symptom detection"""
        text_lower = text.lower()
        for symptom in CRITICAL_SYMPTOMS:
            if symptom in text_lower:
                return True, symptom
        return False, None

    def _process_local(self, prompt: str) -> str:
        """Handle local Ollama processing"""
        try:
            start_time = time.time()
            response = ollama.generate(
                model="gemma3n:e2b",
                prompt=prompt,
                options={
                    'num_thread': max(2, self.system_info["cpu_cores"]),
                    'temperature': 0.3,
                    'top_p': 0.9
                },
                stream=False
            )
            latency = time.time() - start_time
            logger.info(f"Local processing completed in {latency:.2f}s")
            return response['response']
        except Exception as e:
            logger.error(f"Local processing failed: {str(e)}")
            raise RuntimeError("Local model unavailable")

    def _process_remote(self, prompt: str) -> str:
        """Handle remote server processing"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.server_url}/api/generate",
                json={
                    "model": "gemma3n:e2b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=15
            )
            response.raise_for_status()
            latency = time.time() - start_time
            logger.info(f"Server response in {latency:.2f}s")
            return response.json().get('response', '')
        except requests.exceptions.RequestException as e:
            logger.error(f"Server connection failed: {str(e)}")
            raise RuntimeError("Server unavailable")
        except Exception as e:
            logger.error(f"Unexpected server error: {str(e)}")
            raise RuntimeError("Server processing error")

    def generate_response(self, user_input: str) -> str:
        """Main method to generate medical responses"""
        try:
            # Add user input to history
            self._add_to_conversation("user", user_input)

            # Emergency detection (pre-LLM)
            is_emergency, symptom = self._detect_emergency(user_input)
            if is_emergency:
                emergency_msg = RESPONSE_TEMPLATES["emergency"].format(
                    symptom=symptom,
                    hospital_info="[Location services not implemented]"
                )
                self._add_to_conversation("assistant", emergency_msg)
                return f"{emergency_msg}\n{DISCLAIMER.format(mode_detail=self.mode_details[self.mode])}"

            # Format LLM prompt
            llm_prompt = self._format_for_llm()

            # Process based on selected mode
            try:
                if self.mode == "local":
                    llm_response = self._process_local(llm_prompt)
                else:
                    llm_response = self._process_remote(llm_prompt)
            except RuntimeError as e:
                if self.mode == "local":
                    logger.info("Attempting fallback to server mode")
                    self.mode = "server"
                    llm_response = self._process_remote(llm_prompt)
                else:
                    raise

            # Post-processing
            clean_response = self._postprocess_response(llm_response)
            self._add_to_conversation("assistant", clean_response)
            return f"{clean_response}\n{DISCLAIMER.format(mode_detail=self.mode_details[self.mode])}"

        except Exception as e:
            logger.critical(f"Response generation failed: {str(e)}")
            return "System error. Please try again later."

    def _postprocess_response(self, response: str) -> str:
        """Ensure medical safety in LLM outputs"""
        # Remove any diagnostic language
        forbidden_phrases = [
            "you have", "you're diagnosed", "take this medicine",
            "you should buy", "definitely", "certainly"
        ]
        for phrase in forbidden_phrases:
            if phrase in response.lower():
                response = response.replace(phrase, "[medical advice redacted]")

        # Ensure disclaimer exists
        if "consult a healthcare professional" not in response.lower():
            response += "\n\nℹ️ Remember to consult a healthcare professional."

        return response

    def reset_conversation(self) -> None:
        """Clear conversation history while retaining system settings"""
        self.conversation_history = [self.conversation_history[0]]
        logger.info("Conversation history reset")

##########################
### 4. MAIN INTERFACE ###
##########################

def display_welcome() -> None:
    """Show welcome message and system info"""
    print("""
    Medical Safety Assistant (Gemma3n:e2b)
    -------------------------------------
    Features:
    - Emergency symptom detection
    - 100% offline capability
    - Privacy-focused design
    """)

def get_user_preferences() -> Tuple[str, Optional[str]]:
    """Collect user configuration"""
    print("\nConfiguration Options:")
    print("1. Local mode (Best privacy, needs 4+ CPU cores & 8GB+ RAM)")
    print("2. Server mode (Works on any device)")
    print("3. Auto-detect (Recommended)")
    
    mode_choice = input("Select mode [1/2/3]: ").strip()
    mode_map = {"1": "local", "2": "server", "3": "auto"}
    mode = mode_map.get(mode_choice, "auto")
    
    server_url = None
    if mode == "server":
        if input("Use custom Ollama server? (y/n): ").lower() == 'y':
            server_url = input("Server URL (e.g., http://10.0.0.5:11434): ").strip()
    
    return mode, server_url

def main():
    """Primary execution loop"""
    display_welcome()
    mode, server_url = get_user_preferences()
    
    try:
        bot = MedicalChatbot(mode=mode, server_url=server_url)
        print(f"\nRunning in {bot.mode} mode | {bot.mode_details[bot.mode]}\n")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                    
                if user_input.lower() in ('quit', 'exit'):
                    break
                elif user_input.lower() == 'reset':
                    bot.reset_conversation()
                    print("Conversation history cleared")
                    continue
                    
                print("\nAssistant:", bot.generate_response(user_input))
                
            except KeyboardInterrupt:
                print("\nSession ended.")
                break
                
    except Exception as e:
        print(f"\nFatal initialization error: {str(e)}")
        print("Please check:")
        print("- Ollama is installed and running (for local mode)")
        print("- Network connection (for server mode)")
        sys.exit(1)

if __name__ == "__main__":
    main()
