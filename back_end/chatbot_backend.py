###############################
### CHATBOT BACKEND FOR GUI ###
###############################

# Standard library imports
import os
import sys
import time
import threading
import queue
from typing import List, Dict, Optional, Tuple, Callable

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
### 3. GUI CHATBOT CLASS ###
##########################

class GUIChatbot:
    def __init__(self, 
                 mode: str = "auto", 
                 server_url: Optional[str] = None,
                 status_callback: Optional[Callable[[str], None]] = None,
                 progress_callback: Optional[Callable[[float], None]] = None):
        """
        Initialize chatbot for GUI integration
        
        Args:
            mode: 'local' (Ollama), 'server' (remote), or 'auto'
            server_url: Custom Ollama server URL
            status_callback: Function to update status in GUI
            progress_callback: Function to update progress bar in GUI
        """
        self.status_callback = status_callback or (lambda x: print(f"Status: {x}"))
        self.progress_callback = progress_callback or (lambda x: None)
        
        self.mode = self._validate_mode(mode)
        self.server_url = server_url or "http://localhost:11434"
        self.conversation_history: List[Dict[str, str]] = []
        self.is_initialized = False
        
        # Initialize in background thread
        self._initialize_async()

    def _validate_mode(self, mode: str) -> str:
        """Ensure valid operation mode is selected"""
        valid_modes = ("local", "server", "auto")
        if mode.lower() not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be: {valid_modes}")
        return mode.lower()

    def _initialize_async(self) -> None:
        """Initialize system in background thread"""
        def init_worker():
            try:
                self.status_callback("Initializing system...")
                self.progress_callback(0.1)
                
                # Hardware capabilities
                self.status_callback("Checking hardware capabilities...")
                self.system_info = {
                    "cpu_cores": psutil.cpu_count(logical=False) or 1,
                    "ram_gb": psutil.virtual_memory().total / (1024 ** 3),
                    "has_avx": self._check_cpu_instructions(),
                    "os_type": platform.system()
                }
                self.progress_callback(0.3)

                # Mode configuration
                if self.mode == "auto":
                    self.status_callback("Auto-detecting optimal mode...")
                    self.mode = self._determine_optimal_mode()
                self.progress_callback(0.5)

                # Privacy notices
                self.mode_details = {
                    "local": "All processing occurs on your local device",
                    "server": "Responses are processed on a secure server"
                }

                # Initialize conversation
                self.status_callback("Setting up conversation...")
                self.conversation_history = [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT.format(
                            critical_list=", ".join(sorted(CRITICAL_SYMPTOMS))
                        )
                    }
                ]
                self.progress_callback(0.8)

                # Test connection/model
                self.status_callback("Testing connection...")
                self._test_connection()
                self.progress_callback(1.0)
                
                self.is_initialized = True
                self.status_callback(f"✅ Ready in {self.mode} mode")
                logger.info(f"GUI System initialized in {self.mode} mode")
                
            except Exception as e:
                self.status_callback(f"❌ Initialization failed: {str(e)}")
                logger.error(f"Initialization error: {str(e)}")

        init_thread = threading.Thread(target=init_worker, daemon=True)
        init_thread.start()

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

    def _test_connection(self) -> None:
        """Test if the selected mode is working"""
        test_prompt = "Hello"
        try:
            if self.mode == "local":
                ollama.generate(model="gemma3n:e2b", prompt=test_prompt, options={'num_predict': 1})
            else:
                response = requests.post(
                    f"{self.server_url}/api/generate",
                    json={"model": "gemma3n:e2b", "prompt": test_prompt, "stream": False},
                    timeout=10
                )
                response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Connection test failed: {str(e)}")

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

    def generate_response_async(self, user_input: str, callback: Callable[[str], None]) -> None:
        """Generate response asynchronously for GUI"""
        def response_worker():
            try:
                if not self.is_initialized:
                    callback("⚠️ System is still initializing. Please wait...")
                    return
                
                response = self.generate_response(user_input)
                callback(response)
                
            except Exception as e:
                logger.error(f"Async response generation failed: {str(e)}")
                callback("❌ Error generating response. Please try again.")

        response_thread = threading.Thread(target=response_worker, daemon=True)
        response_thread.start()

    def generate_response(self, user_input: str) -> str:
        """Main method to generate medical responses"""
        try:
            if not self.is_initialized:
                return "⚠️ System is still initializing. Please wait..."
            
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
            return "❌ System error. Please try again later."

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
        if self.conversation_history:
            self.conversation_history = [self.conversation_history[0]]
        logger.info("Conversation history reset")

    def get_status(self) -> Dict[str, any]:
        """Get current system status for GUI display"""
        return {
            "initialized": self.is_initialized,
            "mode": self.mode,
            "mode_detail": self.mode_details.get(self.mode, "Unknown"),
            "conversation_turns": len(self.conversation_history) - 1,  # Exclude system prompt
            "system_info": self.system_info if hasattr(self, 'system_info') else {}
        }
