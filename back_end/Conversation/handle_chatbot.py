import threading
import logging
from typing import Dict, Callable
from back_end.prompt import DISCLAIMER

logger = logging.getLogger(__name__)

class ConversationHandler:

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

    def reset_conversation(self) -> bool:
        """Clear conversation history while retaining system settings"""
        try:
            if self.conversation_history:
                self.conversation_history = [self.conversation_history[0]]
            logger.info("Conversation history reset")
            return True
        except Exception as e:
            logger.error(f"Failed to reset conversation: {e}")
            return False

    def get_status(self) -> Dict[str, any]:
        """Get current system status for GUI display"""
        # Kiểm tra initialization status
        is_init = getattr(self, 'is_initialized', False)
        
        return {
            "initialized": is_init,
            "mode": getattr(self, 'mode', 'unknown'),
            "model": getattr(self, 'current_model', 'not_loaded'),
            "mode_detail": getattr(self, 'mode_details', {}).get(getattr(self, 'mode', 'unknown'), "Unknown"),
            "conversation_turns": len(getattr(self, 'conversation_history', [])) - 1,  # Exclude system prompt
            "system_info": getattr(self, 'system_info', {})
        }

    def force_initialize(self) -> bool:
        """Force set initialization status if system is ready"""
        try:
            # Check if essential components are available
            if hasattr(self, 'conversation_history') and len(self.conversation_history) > 0:
                if hasattr(self, 'mode') and hasattr(self, 'current_model'):
                    self.is_initialized = True
                    logger.info("System forced to initialized state")
                    return True
            
            logger.warning("Cannot force initialize - missing essential components")
            return False
        except Exception as e:
            logger.error(f"Force initialization failed: {e}")
            return False

    def check_initialization_status(self) -> str:
        """Debug method to check what's missing for initialization"""
        status = []
        
        if not hasattr(self, 'is_initialized'):
            status.append("❌ is_initialized attribute missing")
        elif not self.is_initialized:
            status.append("❌ is_initialized = False")
        else:
            status.append("✅ is_initialized = True")
        
        if not hasattr(self, 'conversation_history'):
            status.append("❌ conversation_history missing")
        elif len(self.conversation_history) == 0:
            status.append("❌ conversation_history empty")
        else:
            status.append(f"✅ conversation_history has {len(self.conversation_history)} messages")
        
        if not hasattr(self, 'mode'):
            status.append("❌ mode missing")
        else:
            status.append(f"✅ mode = {self.mode}")
        
        if not hasattr(self, 'current_model'):
            status.append("❌ current_model missing")
        else:
            status.append(f"✅ current_model = {self.current_model}")
        
        return "\n".join(status)

