from typing import List, Dict, Optional, Callable
from Conversation.handle_chatbot import ConversationHandler
import threading
import ollama
import requests
import psutil
import platform
import logging
import time
import sys
import os

#import 
# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, parent_dir])

logger = logging.getLogger(__name__)

# Prompt (moved here instead of importing)
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

DISCLAIMER = "\nPrivacy Note: {mode_detail}"

class GUIChatbot(ConversationHandler):
    def __init__(self, 
                 mode: str = "auto", 
                 server_url: Optional[str] = None,
                 model_path: Optional[str] = None,
                 status_callback: Optional[Callable[[str], None]] = None,
                 progress_callback: Optional[Callable[[float], None]] = None):
        """
        Initialize chatbot for GUI integration
        """
        super().__init__()
        
        self.status_callback = status_callback or (lambda x: print(f"Status: {x}"))
        self.progress_callback = progress_callback or (lambda x: None)
        
        self.mode = "local"
        self.server_url = server_url
        self.model_path = model_path  
        self.conversation_history: List[Dict[str, str]] = []
        self.is_initialized = False
        self.current_model = "gemma3n" 
        self.system_info = self._get_system_info()
        
        # Start initialization
        self._initialize_async()

    def _initialize_async(self):
        """Initialize system in background thread"""
        def init_worker():
            try:
                self.status_callback("Initializing system...")
                self.progress_callback(0.1)
                
                # Hardware capabilities
                self.status_callback("Checking hardware capabilities...")
                self.system_info = self._get_system_info()
                self.progress_callback(0.4)

                # Initialize conversation with system prompt
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
            except Exception as e:
                logger.error(f"Initialization failed: {str(e)}")
                self.status_callback(f"Initialization failed: {str(e)}")

        init_thread = threading.Thread(target=init_worker, daemon=True)
        init_thread.start()

    def _check_cpu_instructions(self) -> bool:
        """Verify CPU supports required instructions (AVX)"""
        try:
            import cpuinfo
            cpu_flags = cpuinfo.get_cpu_info().get('flags', [])
            return 'avx' in cpu_flags
        except Exception:
            return True  # Assume true if can't detect

    def _add_to_conversation(self, role: str, content: str) -> None:
        """Manage conversation history with rolling window"""
        self.conversation_history.append({"role": role, "content": content})
        
        # Keep only recent conversation 
        if len(self.conversation_history) > 7:  
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-6:]

    def get_status(self) -> dict:
        """Get current system status"""
        return {
            "initialized": self.is_initialized,
            "mode": self.mode,
            "model": self.current_model,
            "conversation_turns": len(self.conversation_history) - 1,
        }

    def get_system_requirements(self) -> dict:
        """Get system requirements info"""
        try:
            if not hasattr(self, 'system_info'):
                return {"error": "System not initialized"}
            
            current = self.system_info
            recommended = {
                "cpu_cores": 4,
                "ram_gb": 8,
                "has_avx": True
            }
            
            meets = {
                "cpu": current["cpu_cores"] >= recommended["cpu_cores"],
                "ram": current["ram_gb"] >= recommended["ram_gb"],
                "avx": current["has_avx"],
                "overall": all([
                    current["cpu_cores"] >= recommended["cpu_cores"],
                    current["ram_gb"] >= recommended["ram_gb"],
                    current["has_avx"]
                ])
            }
            
            performance_tips = []
            if not meets["cpu"]:
                performance_tips.append("Consider upgrading CPU for better performance")
            if not meets["ram"]:
                performance_tips.append("Consider adding more RAM")
            if not meets["avx"]:
                performance_tips.append("CPU lacks AVX support")
            
            return {
                "current_specs": current,
                "recommended_specs": recommended,
                "meets_requirements": meets,
                "performance_tips": performance_tips
            }
        except Exception as e:
            return {"error": str(e)}

    def reset_conversation(self) -> bool:
        """Reset conversation history"""
        try:
            if self.conversation_history:
                # Keep only the system prompt
                self.conversation_history = [self.conversation_history[0]]
            return True
        except Exception:
            return False

    def _validate_mode(self, mode: str) -> str:
        """Ensure valid operation mode is selected"""
        valid_modes = ("local", "server", "auto", "fallback")
        if mode.lower() not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be: {valid_modes}")
        return mode.lower()

    def _test_local_model(self) -> None:
        """Test if the local model is working"""
            
        test_prompt = "Hello"
        try:
            ollama.generate(model=self.current_model, prompt=test_prompt, options={'num_predict': 1})
            logger.info(f"Local model {self.current_model} test successful")
        except Exception as e:
            raise RuntimeError(f"Local model test failed: {str(e)}")

#role prompting
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
                    'temperature': 0.5,  
                    'top_p': 0.9,
                    'num_predict': 512  
                },
                stream=False
            )
            latency = time.time() - start_time
            logger.info(f"Local processing completed in {latency:.2f}s")
            return response['response']
        except Exception as e:
            logger.error(f"Local processing failed: {str(e)}")
            return self._fallback_response(prompt)

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
                timeout=30  
            )
            response.raise_for_status()
            latency = time.time() - start_time
            logger.info(f"Server response in {latency:.2f}s")
            return response.json().get('response', '')
        except Exception as e:
            logger.error(f"Server processing failed: {str(e)}")
            return self._fallback_response(prompt)

    def generate_response_async(self, user_input: str, callback: Callable[[str], None]):
        """Generate response asynchronously"""
        def response_worker():
            try:
                # Add user input to conversation
                self._add_to_conversation("user", user_input)
                
                # Generate response based on mode
                if self.current_model == "fallback":
                    response = self._fallback_response(user_input)
                else:
                    # Format prompt for LLM
                    formatted_prompt = self._format_for_llm()
                    response = self._process_local(formatted_prompt)
                
                # Add response to conversation
                self._add_to_conversation("assistant", response)
                
                # Call callback with response
                callback(response)
                
            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"
                logger.error(error_msg)
                callback(self._fallback_response(user_input))
        
        import threading
        response_thread = threading.Thread(target=response_worker, daemon=True)
        response_thread.start()

    def generate_response(self, user_input: str) -> str:
        """Generate response synchronously"""
        try:
            # Add user input to conversation
            self._add_to_conversation("user", user_input)
            
            # Generate response based on mode
            if self.current_model == "fallback" :
                response = self._fallback_response(user_input)
            else:
                # Format prompt for LLM
                formatted_prompt = self._format_for_llm()
                response = self._process_local(formatted_prompt)
            
            # Add response to conversation
            self._add_to_conversation("assistant", response)
            
            return response
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            return self._fallback_response(user_input)



