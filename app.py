#!/usr/bin/env python3
"""
AI Chatbot Assistant - Main Entry Point
"""
import sys
import os
import streamlit as st

# Thêm thư mục src vào Python path để import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import main chatbot
from src.main_chatbot import main
from src.core.exceptions import APIKeyMissingError

def run_app():
    """Run the streamlit app with proper error handling"""
    try:
        main()
    except APIKeyMissingError as e:
        st.error(f"❌ {str(e)}")
        st.info("Vui lòng thiết lập biến môi trường GEMINI_API_KEY")
        st.code("export GEMINI_API_KEY=your_api_key_here", language="bash")
        st.markdown("[Lấy API key tại Google AI Studio](https://aistudio.google.com/)")
    except Exception as e:
        st.error(f"❌ Lỗi nghiêm trọng: {str(e)}")
        st.info("Vui lòng kiểm tra logs để biết thêm chi tiết.")

if __name__ == "__main__":
    run_app()
