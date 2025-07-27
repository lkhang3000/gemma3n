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
### PROMPTS AND CONSTANTS ###
##############################

SYSTEM_PROMPT = """You are a medical information assistant. Follow these rules IN ORDER:

1. FIRST CHECK - ONLY for EXACT emergency symptoms ({critical_list}):
   → If patient mentions ANY of these EXACT words, respond with: "EMERGENCY!!: [symptom] detected\n1. Call local emergency services IMMEDIATELY (112 or 115 in Vietnam)\n2. Do NOT wait for further instructions\n3. Follow operator guidance\nNearest hospital: Contact local hospital or emergency services"

2. SECOND CHECK - For medical form requests:
   → If patient mentions ANY of these phrases: "create form", "medical form", "create a form", "want form", "need form", "fill form", "contact doctor", "see doctor", "severe condition", "serious condition"
   → Respond with: "Medical Form Available In The Menu. Fill out the form and it will be sent to one of our most trustworthy doctors."

3. THIRD CHECK - For general negative feeling:
   → If patients describe they have any signs of sickness (light or severe), use one of: {reassure_sentences}
   → Then ask: "Do you have any other symptoms I should know about?"

4. DEFAULT: For normal medical questions or unrecognized input:
   → Suggest 2-3 POSSIBLE causes
   → List 1-2 recommended actions
   → Always add: "Consult a healthcare professional"

5. For greetings: Greet politely and ask how you can help

IMPORTANT: "feeling unwell" is NOT an emergency. Only treat as emergency if they mention EXACT words like "chest pain", "difficulty breathing", etc.

Never provide diagnoses or recommend specific medications."""

REASSURE_SENTENCES = {
    "Sorry to hear that", "Everything's gonna be alright", "I understand what you're going through",
}

CRITICAL_SYMPTOMS = {
    "chest pain", "difficulty breathing", "severe bleeding",
    "sudden numbness", "loss of consciousness", "stroke symptoms",
    "suicidal thoughts", "severe burns", "choking", "heart attack",
    "severe headache", "poisoning", "allergic reaction"
}

DISCLAIMER = "\n🔒 Privacy Note: {mode_detail}"

##########################
### 3. GUI CHATBOT CLASS ###
##########################

class GUIChatbot:
    def __init__(self, 
                 mode: str = "auto", 
                 server_url: Optional[str] = None,
                 model_path: Optional[str] = None,
                 status_callback: Optional[Callable[[str], None]] = None,
                 progress_callback: Optional[Callable[[float], None]] = None):
        """
        Initialize chatbot for GUI integration
        
        Args:
            mode: 'local' (Ollama), 'server' (remote), or 'auto'
            server_url: Custom Ollama server URL
            model_path: Custom path to the model (if using local file)
            status_callback: Function to update status in GUI
            progress_callback: Function to update progress bar in GUI
        """
        self.status_callback = status_callback or (lambda x: print(f"Status: {x}"))
        self.progress_callback = progress_callback or (lambda x: None)
        
        self.mode = "local"  # Force local mode since user has downloaded model
        self.model_path = model_path  # Custom model path if provided
        self.conversation_history: List[Dict[str, str]] = []
        self.is_initialized = False
        
        # Use the user's downloaded model directly
        self.current_model = "gemma:2b"  # User's installed model
        
        # Initialize in background thread
        self._initialize_async()

    def _validate_mode(self, mode: str) -> str:
        """Ensure valid operation mode is selected"""
        valid_modes = ("local", "server", "auto")
        if mode.lower() not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be: {valid_modes}")
        return mode.lower()

    def _find_available_model(self) -> str:
        """Find the first available model from the list"""
        try:
            # Get list of installed models
            models = ollama.list()
            installed_models = [model['name'] for model in models.get('models', [])]
            
            # Find first available model
            for model in self.available_models:
                if any(model in installed for installed in installed_models):
                    logger.info(f"Found available model: {model}")
                    return model
            
            # If no preferred models found, use the first available one
            if installed_models:
                first_model = installed_models[0]
                logger.info(f"Using first available model: {first_model}")
                return first_model
                
        except Exception as e:
            logger.warning(f"Could not list models: {e}")
        
        # Fallback to a common model
        return "llama3.2:3b"

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
                self.progress_callback(0.4)

                # Using local mode with gemma:2b model
                self.status_callback(f"Using local model: {self.current_model}")
                self.progress_callback(0.6)

                # Privacy notices
                self.mode_details = {
                    "local": "All processing occurs on your local device"
                }

                # Initialize conversation
                self.status_callback("Setting up conversation...")
                self.conversation_history = [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT.format(
                            critical_list=", ".join(sorted(CRITICAL_SYMPTOMS)),
                            reassure_sentences=", ".join(sorted(REASSURE_SENTENCES))
                        )
                    }
                ]
                self.progress_callback(0.8)

                # Test local model
                self.status_callback("Testing local model...")
                self._test_local_model()
                self.progress_callback(1.0)
                
                self.is_initialized = True
                self.status_callback(f"✅ Ready in {self.mode} mode with {self.current_model}")
                logger.info(f"GUI System initialized in {self.mode} mode with model {self.current_model}")
                
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

    def _warn_if_unsupported_hardware(self) -> None:
        """Notify user about potential performance issues via GUI"""
        if self.mode == "local":
            warnings = []
            if self.system_info["cpu_cores"] < 4:
                warnings.append(f"Limited CPU cores ({self.system_info['cpu_cores']}/4 recommended)")
            if self.system_info["ram_gb"] < 8:
                warnings.append(f"Limited RAM ({self.system_info['ram_gb']:.1f}GB/8GB recommended)")
            if not self.system_info["has_avx"]:
                warnings.append("Missing AVX CPU instructions (required for optimal performance)")

            if warnings:
                warning_msg = "⚠️ Performance warnings detected:\n" + "\n".join(f"- {w}" for w in warnings)
                self.status_callback(warning_msg)
                logger.warning(f"Hardware limitations detected: {warnings}")

    def _test_local_model(self) -> None:
        """Test if the local gemma:2b model is working"""
        test_prompt = "Hello"
        try:
            ollama.generate(model=self.current_model, prompt=test_prompt, options={'num_predict': 1})
            logger.info(f"Local model {self.current_model} test successful")
        except Exception as e:
            raise RuntimeError(f"Local model test failed: {str(e)}")

    def _add_to_conversation(self, role: str, content: str) -> None:
        """Manage conversation history with rolling window"""
        self.conversation_history.append({"role": role, "content": content})
        
        # Maintain 6-turn memory (3 user + 3 assistant) plus system prompt
        if len(self.conversation_history) > 7:  # system + 6 turns
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-6:]

    def _format_for_llm(self) -> str:
        """Engineer the final prompt sent to the LLM"""
        conversation = []
        for msg in self.conversation_history[1:]:  # Skip system prompt
            if msg['role'] == 'user':
                conversation.append(f"Patient: {msg['content']}")
            else:
                conversation.append(f"Doctor: {msg['content']}")
        
        # Add system prompt at the beginning
        formatted_prompt = f"{self.conversation_history[0]['content']}\n\n"
        formatted_prompt += "\n".join(conversation)
        formatted_prompt += "\nDoctor:"
        
        return formatted_prompt

    def _process_local(self, prompt: str) -> str:
        """Handle local Ollama processing"""
        try:
            start_time = time.time()
            response = ollama.generate(
                model=self.current_model,
                prompt=prompt,
                options={
                    'num_thread': max(2, self.system_info["cpu_cores"]),
                    'temperature': 0.5,  # Increased for more flexible responses
                    'top_p': 0.9,
                    'num_predict': 512  # Limit response length
                },
                stream=False
            )
            latency = time.time() - start_time
            logger.info(f"Local processing completed in {latency:.2f}s")
            return response['response']
        except Exception as e:
            logger.error(f"Local processing failed: {str(e)}")
            raise RuntimeError(f"Local model unavailable: {str(e)}")

    def _process_remote(self, prompt: str) -> str:
        """Handle remote server processing"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.server_url}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 512
                    }
                },
                timeout=30  # Increased timeout
            )
            response.raise_for_status()
            latency = time.time() - start_time
            logger.info(f"Server response in {latency:.2f}s")
            return response.json().get('response', '')
        except requests.exceptions.RequestException as e:
            logger.error(f"Server connection failed: {str(e)}")
            raise RuntimeError(f"Server unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected server error: {str(e)}")
            raise RuntimeError(f"Server processing error: {str(e)}")

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
                callback(f"❌ Error generating response: {str(e)}")

        response_thread = threading.Thread(target=response_worker, daemon=True)
        response_thread.start()

    def generate_response(self, user_input: str) -> str:
        """Main method to generate medical responses"""
        try:
            if not self.is_initialized:
                return "⚠️ System is still initializing. Please wait..."
            
            # Add user input to history
            self._add_to_conversation("user", user_input)

            # Let AI handle all logic based on SYSTEM_PROMPT
            llm_prompt = self._format_for_llm()

            # Process with local model only
            llm_response = self._process_local(llm_prompt)

            # Post-processing
            clean_response = self._postprocess_response(llm_response)
            self._add_to_conversation("assistant", clean_response)
            return f"{clean_response}\n{DISCLAIMER.format(mode_detail=self.mode_details[self.mode])}"

        except Exception as e:
            logger.critical(f"Response generation failed: {str(e)}")
            return f"❌ System error: {str(e)}. Please try again later."

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

        return response.strip()

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
            "model": self.current_model,
            "mode_detail": self.mode_details.get(self.mode, "Unknown"),
            "conversation_turns": len(self.conversation_history) - 1,  # Exclude system prompt
            "system_info": self.system_info if hasattr(self, 'system_info') else {}
        }

    def get_system_requirements(self) -> Dict[str, any]:
        """Get detailed system requirements and recommendations"""
        if not hasattr(self, 'system_info'):
            return {"error": "System not initialized"}
        
        requirements = {
            "current_specs": {
                "cpu_cores": self.system_info["cpu_cores"],
                "ram_gb": round(self.system_info["ram_gb"], 1),
                "has_avx": self.system_info["has_avx"],
                "os_type": self.system_info["os_type"]
            },
            "recommended_specs": {
                "cpu_cores": 4,
                "ram_gb": 8,
                "has_avx": True,
                "os_type": "Any"
            },
            "meets_requirements": {
                "cpu": self.system_info["cpu_cores"] >= 4,
                "ram": self.system_info["ram_gb"] >= 8,
                "avx": self.system_info["has_avx"],  
                "overall": (
                    self.system_info["cpu_cores"] >= 4 and 
                    self.system_info["ram_gb"] >= 8 and 
                    self.system_info["has_avx"]
                )
            },
            "performance_tips": self._get_performance_tips()
        }
        return requirements

    def _get_performance_tips(self) -> List[str]:
        """Generate performance improvement tips based on system specs"""
        tips = []
        
        if self.system_info["cpu_cores"] < 4:
            tips.append("Consider upgrading to a CPU with 4+ cores for better performance")
        
        if self.system_info["ram_gb"] < 8:
            tips.append(f"Current RAM: {self.system_info['ram_gb']:.1f}GB. Recommended: 8GB+ for optimal performance")
        
        if not self.system_info["has_avx"]:
            tips.append("Your CPU lacks AVX instructions. Performance may be limited in local mode")
        
        if self.mode == "server":
            tips.append("Using server mode. Ensure stable internet connection for best experience")
        
        if not tips:
            tips.append("Your system meets all recommended requirements! 🎉")
            
        return tips