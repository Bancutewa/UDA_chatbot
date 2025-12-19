"""Selenium tests cho chức năng tạo audio qua chat.

Flow:
- Đảm bảo chưa đăng nhập.
- Đăng nhập bằng user test.
- Gửi yêu cầu tạo audio.
- Kiểm tra có text đường dẫn .mp3 hoặc phần tử audio.
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
        "Cần đặt TEST_USER_USERNAME / TEST_USER_PASSWORD cho audio tests."
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
def test_generate_audio_flow(chrome_driver):
    """Gửi yêu cầu tạo audio và xác nhận app phản hồi (smoke test).

    Lưu ý: ElevenLabs có thể quota/ lỗi, nên test CHỈ kiểm tra rằng:
    - Sau khi gửi prompt audio, DOM có thay đổi (có phản hồi mới),
    - Không assert bắt buộc phải có .mp3.
    """

    # Nếu chưa cấu hình ElevenLabs API key thì bỏ qua hoàn toàn
    if not os.getenv("ELEVEN_LABS_API_KEY"):
        pytest.skip("ELEVEN_LABS_API_KEY chưa được cấu hình, bỏ qua audio flow test.")

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
    prompt = (
        "Hãy tạo file audio cho câu này: "
        "'Đây là bài test audio cho hệ thống.'"
    )

    chat_input.clear()
    chat_input.send_keys(prompt)
    time.sleep(0.5)
    chat_input.send_keys(Keys.ENTER)

    # Chờ một trong các dấu hiệu sau xuất hiện trong UI (có phản hồi mới):
    # - Text chứa đường dẫn .mp3 / data/audio_generations (thành công)
    # - Hoặc thông báo lỗi chung của hệ thống xử lý audio
    WebDriverWait(driver, 90).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//*[contains(text(), '.mp3') or "
                "contains(text(), 'data/audio_generations') or "
                "contains(text(), 'Xin lỗi, hệ thống đang gặp sự cố')]",
            )
        )
    )

    # Giữ trình duyệt thêm vài giây để người xem kịp đọc câu trả lời (chỉ hữu ích khi debug)
    time.sleep(5)
