"""Selenium tests cho chức năng tìm kiếm bất động sản qua chat.

Flow:
- Đảm bảo chưa đăng nhập.
- Đăng nhập bằng user test có sẵn (TEST_USER_USERNAME / TEST_USER_PASSWORD).
- Gửi câu hỏi tìm kiếm và xác nhận UI có cập nhật (DOM thay đổi).
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
        "Cần đặt biến môi trường TEST_USER_USERNAME và TEST_USER_PASSWORD "
        "để chạy Selenium search tests."
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
def test_search_apartment_flow(chrome_driver):
    """Gửi câu hỏi tìm căn hộ và kiểm tra UI có cập nhật."""

    driver = chrome_driver
    driver.get(BASE_URL)
    time.sleep(1)

    # Nếu đang login thì logout trước
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

    # Đăng nhập
    _login_as_test_user(driver)

    # Lấy số lượng div hiện tại để so sánh DOM thay đổi
    initial_div_count = len(driver.find_elements(By.TAG_NAME, "div"))

    chat_input = _get_chat_input(driver)
    user_message = "Tìm căn 2 phòng ngủ ở Q7 Riverside tầm 3 tỷ"

    chat_input.clear()
    chat_input.send_keys(user_message)
    time.sleep(0.5)
    chat_input.send_keys(Keys.ENTER)

    # Đợi DOM thay đổi (số lượng div tăng lên) - biểu hiện có kết quả/response mới
    def dom_changed(drv):
        return len(drv.find_elements(By.TAG_NAME, "div")) > initial_div_count

    WebDriverWait(driver, 60).until(dom_changed)
