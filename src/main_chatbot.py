"""
Main Chatbot - Orchestrator cho toàn bộ hệ thống
"""
import os
import streamlit as st
from typing import Optional

from .core.config import config
from .core.exceptions import APIKeyMissingError
from .ui.chat_interface import chat_interface
from .ui.auth_interface import auth_interface
from .core.logger import logger


class MainChatbot:
    """Main orchestrator for the chatbot system"""

    def __init__(self):
        self._validate_config()
        logger.info("MainChatbot initialized")

    def _validate_config(self):
        """Validate configuration and dependencies"""
        # Check API key
        if not config.GEMINI_API_KEY:
            raise APIKeyMissingError("GEMINI_API_KEY is required")

        # Validate config
        config.validate()

        logger.info("Configuration validated successfully")

    def run(self):
        """Run the chatbot application"""
        try:
            # Check authentication first
            user_session = auth_interface.render()

            # If user is authenticated, show chat interface
            if user_session:
                chat_interface.render(user_session)
            # auth_interface.render() already handles the auth UI when not logged in

        except Exception as e:
            logger.error(f"Error running chatbot: {e}")
            st.error(f"❌ Lỗi hệ thống: {str(e)}")


def main():
    """Main entry point"""
    try:
        chatbot = MainChatbot()
        chatbot.run()
    except APIKeyMissingError as e:
        logger.error(f"API Key missing: {e}")
        # Re-raise để streamlit app handle
        raise e
    except Exception as e:
        logger.error(f"Critical error: {e}")
        # Re-raise để streamlit app handle
        raise e


if __name__ == "__main__":
    main()
