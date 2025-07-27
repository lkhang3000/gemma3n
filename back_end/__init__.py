# Backend package initialization
from .chatbot_backend import GUIChatbot
from .prompt import SYSTEM_PROMPT, CRITICAL_SYMPTOMS, RESPONSE_TEMPLATES

__all__ = ['GUIChatbot', 'SYSTEM_PROMPT', 'CRITICAL_SYMPTOMS', 'RESPONSE_TEMPLATES']
