"""Selenium tests cho luồng chat cơ bản.

Flow chính:
- Đảm bảo chưa đăng nhập.
- Đăng nhập với user có sẵn (test user).
- Vào màn hình chat.
- Gửi một message qua chat input và xác nhận message xuất hiện trong lịch sử.

Lưu ý:
- Cần chuẩn bị sẵn 1 tài khoản test trong hệ thống, ví dụ đặt biến môi trường:
  - TEST_USER_USERNAME
  - TEST_USER_PASSWORD
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
    """Đợi form đăng nhập xuất hiện."""
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(., 'Đăng Nhập')]")
        )
    )


def _login_as_test_user(driver):
    """Đăng nhập bằng tài khoản test có sẵn (đọc từ env)."""
    username = os.getenv("TEST_USER_USERNAME")
    password = os.getenv("TEST_USER_PASSWORD")

    assert username and password, (
        "Cần đặt biến môi trường TEST_USER_USERNAME và TEST_USER_PASSWORD "
        "để chạy Selenium chat tests mà không đăng ký user mới."
    )

    # Chắc chắn đang ở màn hình đăng nhập
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

    # Đợi vào được app (sidebar Tài Khoản xuất hiện)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Tài Khoản')]")
        )
    )


@pytest.mark.selenium
def test_basic_chat_flow(chrome_driver):
    """Đăng nhập user có sẵn và gửi một tin nhắn chat."""

    driver = chrome_driver
    driver.get(BASE_URL)
    time.sleep(1)

    # Nếu đang login rồi thì logout trước
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
        # Không thấy nút Đăng Xuất thì coi như đang ở trang login
        pass

    # Đăng nhập bằng test user
    _login_as_test_user(driver)

    # Tìm ô chat_input (label "Hỏi tôi...")
    # Streamlit chat_input thường render thành một textarea với aria-label là label
    chat_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//textarea[@aria-label='Hỏi tôi...'] | "
                "//textarea[contains(@placeholder, 'Hỏi tôi')]",
            )
        )
    )

    user_message = "Test chat bằng Selenium"
    chat_input.clear()
    chat_input.send_keys(user_message)
    time.sleep(0.5)
    chat_input.send_keys(Keys.ENTER)

    # Đợi message của user xuất hiện trong history
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, f"//*[contains(text(), '{user_message}')]")
        )
    )
