"""Common Selenium fixtures for UI tests.

Yêu cầu:
- Đã chạy: `streamlit run app.py`
- Có Chrome/Chromium trên máy.
"""
import os
import pytest
from dotenv import load_dotenv 

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

@pytest.fixture(scope="module")
def chrome_driver():
    """Khởi tạo Chrome WebDriver dùng webdriver-manager (headless).

    Sử dụng chung cho tất cả test trong thư mục `tests/selenium`.
    """

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-features=PasswordLeakDetection")

    options.add_experimental_option(
    "prefs",
    {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    },
)

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options,
    )
    driver.set_window_size(1400, 900)
    yield driver
    driver.quit()
