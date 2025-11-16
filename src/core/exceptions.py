"""
Custom exceptions for the application
"""

class ChatbotError(Exception):
    """Base exception for chatbot application"""
    pass

class APIKeyMissingError(ChatbotError):
    """Raised when required API key is missing"""
    pass

class AgentInitializationError(ChatbotError):
    """Raised when agent fails to initialize"""
    pass

class IntentAnalysisError(ChatbotError):
    """Raised when intent analysis fails"""
    pass

class DatabaseConnectionError(ChatbotError):
    """Raised when database connection fails"""
    pass

class AudioGenerationError(ChatbotError):
    """Raised when audio generation fails"""
    pass

class ImageGenerationError(ChatbotError):
    """Raised when image generation fails"""
    pass

class RAGError(ChatbotError):
    """Raised when RAG pipeline fails"""
    pass

class ValidationError(ChatbotError):
    """Raised when data validation fails"""
    pass

class AuthenticationError(ChatbotError):
    """Raised when authentication fails"""
    pass

class AuthorizationError(ChatbotError):
    """Raised when authorization fails"""
    pass
