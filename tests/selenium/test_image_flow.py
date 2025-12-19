"""Selenium tests cho chức năng tạo ảnh qua chat.

Flow:
- Đảm bảo chưa đăng nhập.
- Đăng nhập bằng user test.
- Gửi yêu cầu tạo ảnh.
- Kiểm tra có text đường dẫn ảnh hoặc phần tử <img> xuất hiện.
"""
import os
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


BASE_URL = os.getenv("STREAMLIT_BASE_URL", "http://localhost:8501")


def _wait_for_login_form(driver):
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(., 'Đăng Nhập')]")
        )
    )


def _login_as_test_user(driver):
    username = os.getenv("TEST_USER_USERNAME")
    password = os.getenv("TEST_USER_PASSWORD")

    assert username and password, (
        "Cần đặt TEST_USER_USERNAME / TEST_USER_PASSWORD cho image tests."
    )

    _wait_for_login_form(driver)

    def fill_input(label_contains: str, value: str):
        xpath = f"//label[contains(., '{label_contains}')]/following::input[1]"
        el = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        el.clear()
        el.send_keys(value)
        time.sleep(0.3)

    fill_input("Tên đăng nhập", username)
    fill_input("Mật khẩu", password)

    login_btn = driver.find_element(By.XPATH, "//button[contains(., 'Đăng Nhập')]")
    login_btn.click()

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Tài Khoản')]")
        )
    )


def _get_chat_input(driver):
    return WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//textarea[@aria-label='Hỏi tôi...'] | "
                "//textarea[contains(@placeholder, 'Hỏi tôi')]",
            )
        )
    )


@pytest.mark.selenium
def test_generate_image_flow(chrome_driver):
    """Gửi yêu cầu tạo ảnh và chờ thấy dấu hiệu tạo ảnh."""

    driver = chrome_driver
    driver.get(BASE_URL)
    time.sleep(1)

    # Logout nếu cần
    try:
        logout_btn = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(., 'Đăng Xuất')]")
            )
        )
        logout_btn.click()
        _wait_for_login_form(driver)
        time.sleep(1)
    except Exception:
        pass

    _login_as_test_user(driver)

    chat_input = _get_chat_input(driver)
    prompt = "Hãy tạo một hình minh hoạ căn hộ 2 phòng ngủ hiện đại, sáng sủa"

    chat_input.clear()
    chat_input.send_keys(prompt)
    time.sleep(0.5)
    chat_input.send_keys(Keys.ENTER)

    # Chờ xem có text đường dẫn ảnh hoặc thẻ img
    # Tool generate_image_tool trả về chuỗi: "Image generated successfully: data/generated_images/...png"
    try:
        WebDriverWait(driver, 90).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'data/generated_images')]")
            )
        )
    except Exception:
        # Nếu không thấy text, thử tìm thẻ img như fallback (ảnh đã được render trực tiếp)
        WebDriverWait(driver, 90).until(
            EC.presence_of_element_located((By.TAG_NAME, "img"))
        )
