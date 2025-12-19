"""Selenium tests cho các luồng liên quan đến người dùng (auth).

Flow chính trong file này:
- Nếu đang logged-in thì logout trước để về màn hình đăng nhập.
- Đăng ký tài khoản mới.
- Kiểm tra đã auto-login (thấy sidebar tài khoản).
- Logout và kiểm tra quay lại màn hình đăng nhập.
"""
import os
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = os.getenv("STREAMLIT_BASE_URL", "http://localhost:8501")


def _ensure_logged_out(driver):
    """Nếu đang thấy nút Đăng Xuất thì click để đảm bảo về trạng thái chưa đăng nhập."""
    try:
        logout_button = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Đăng Xuất')]"))
        )
        logout_button.click()
        # Chờ màn hình đăng nhập hiện ra
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//*[contains(text(), 'Đăng Nhập')]")
            )
        )
        # Cho một chút thời gian để UI ổn định
        time.sleep(1)
    except Exception:
        # Không tìm thấy nút Đăng Xuất => coi như đã ở trạng thái logged-out
        pass


@pytest.mark.selenium
def test_register_login_logout_flow(chrome_driver):
    """Test end-to-end cho luồng đăng ký -> auto login -> logout.

    - Mở app
    - Đảm bảo đang ở trạng thái chưa đăng nhập
    - Click chuyển sang form Đăng Ký
    - Đăng ký user mới (username unique theo timestamp)
    - Kiểm tra đã auto login (sidebar tài khoản xuất hiện)
    - Logout, kiểm tra quay lại màn hình đăng nhập
    """

    driver = chrome_driver
    driver.get(BASE_URL)
    # Đợi trang load hẳn
    time.sleep(1)

    # Đảm bảo logged-out
    _ensure_logged_out(driver)

    # Nếu đang ở màn hình Đăng Ký từ lần trước thì quay về Đăng Nhập
    try:
        back_to_login_btn = driver.find_element(
            By.XPATH, "//button[contains(., 'Đăng nhập')]"
        )
        back_to_login_btn.click()
    except Exception:
        pass

    # Chờ form đăng nhập xuất hiện
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(., 'Đăng Nhập')]")
        )
    )

    # Bấm nút "Chưa có tài khoản? Đăng ký ngay"
    register_link_btn = driver.find_element(
        By.XPATH, "//button[contains(., 'Đăng ký ngay')]"
    )
    register_link_btn.click()
    time.sleep(0.5)

    # Chờ tiêu đề Đăng Ký
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Đăng Ký Tài Khoản Mới')]")
        )
    )

    # Tạo username/email unique
    suffix = int(time.time())
    username = f"selenium_user_{suffix}"
    email = f"selenium_{suffix}@example.com"
    password = "selenium123"

    # Điền form đăng ký
    def fill_input(label_contains: str, value: str):
        xpath = f"//label[contains(., '{label_contains}')]/following::input[1]"
        el = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        el.clear()
        el.send_keys(value)
        # Cho người xem kịp quan sát
        time.sleep(0.5)

    fill_input("Tên đăng nhập", username)
    fill_input("Mật khẩu *", password)
    fill_input("Xác nhận mật khẩu", password)
    fill_input("Họ và tên", f"Selenium User {suffix}")
    fill_input("Email", email)

    # Submit form Đăng Ký
    submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Đăng Ký')]")
    submit_btn.click()
    time.sleep(1)

    # Sau khi đăng ký thành công, hệ thống auto-login và rerun app.
    # Kiểm tra sự xuất hiện của phần sidebar "👤 Tài Khoản".
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Tài Khoản')]")
        )
    )

    # Tìm và click nút Đăng Xuất (đợi cho tới khi hiện & clickable)
    logout_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(normalize-space(), 'Đăng Xuất')]")
        )
    )
    logout_button.click()

    # Kiểm tra quay lại màn hình đăng nhập
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Đăng Nhập')]")
        )
    )

    # Đăng nhập lại với tài khoản vừa tạo để test login flow
    def fill_login_input(label_contains: str, value: str):
        xpath = f"//label[contains(., '{label_contains}')]/following::input[1]"
        el = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        el.clear()
        el.send_keys(value)
        time.sleep(0.5)

    fill_login_input("Tên đăng nhập", username)
    fill_login_input("Mật khẩu", password)

    login_btn = driver.find_element(By.XPATH, "//button[contains(., 'Đăng Nhập')]")
    login_btn.click()
    time.sleep(1)

    # Sau login lại phải thấy sidebar Tài Khoản
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Tài Khoản')]")
        )
    )
