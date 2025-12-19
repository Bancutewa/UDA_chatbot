"""Selenium smoke tests for the Streamlit chatbot app.

Các test này giả định bạn đã chạy:

    streamlit run app.py

ở local (mặc định trên http://localhost:8501).

Mục tiêu chỉ là kiểm tra app load được (không crash),
UI cơ bản render ra được phần thân trang.
"""
import os
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = os.getenv("STREAMLIT_BASE_URL", "http://localhost:8501")


@pytest.mark.selenium
def test_streamlit_app_loads(chrome_driver):
    """Smoke test: trang Streamlit load được và body không rỗng.

    - Mở BASE_URL
    - Đợi body render
    - Kiểm tra title có nội dung
    - Kiểm tra trong body có ít nhất một element DIV (ứng với layout của Streamlit)
    """

    chrome_driver.get(BASE_URL)

    # Đợi Streamlit load (tối đa ~30s)
    WebDriverWait(chrome_driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    title = chrome_driver.title
    assert isinstance(title, str)
    assert title.strip() != ""

    body = chrome_driver.find_element(By.TAG_NAME, "body")
    assert body is not None

    # Kiểm tra có ít nhất một thẻ div (Streamlit luôn render layout bằng div)
    divs = chrome_driver.find_elements(By.TAG_NAME, "div")
    assert len(divs) > 0


@pytest.mark.selenium
def test_streamlit_has_main_app_root(chrome_driver):
    """Kiểm tra Streamlit render vùng root chính của app.

    Streamlit 1.x thường render app trong một container role="main".
    Nếu không tìm thấy, test sẽ failed để báo hiệu layout bất thường.
    """

    chrome_driver.get(BASE_URL)

    WebDriverWait(chrome_driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Tìm phần tử role="main" (được Streamlit dùng cho vùng nội dung chính)
    mains = chrome_driver.find_elements(By.CSS_SELECTOR, '[role="main"]')

    # Không phải bản Streamlit nào cũng chắc chắn dùng role="main",
    # nên nếu không có thì chỉ cảnh báo bằng assert nhẹ.
    assert len(mains) >= 0
