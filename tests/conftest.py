"""Pytest configuration và hooks để ghi kết quả test vào CSV/Excel."""
import os
import csv
import pytest
from datetime import datetime
from pathlib import Path


# Đường dẫn file kết quả test
TEST_RESULTS_DIR = Path(__file__).parent.parent / "test_results"
TEST_RESULTS_DIR.mkdir(exist_ok=True)

CSV_RESULTS_FILE = TEST_RESULTS_DIR / "test_results.csv"
EXCEL_RESULTS_FILE = TEST_RESULTS_DIR / "test_results.xlsx"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook để capture kết quả từng test case."""
    outcome = yield
    rep = outcome.get_result()

    # Chỉ ghi khi test kết thúc (call.when == "call")
    if rep.when == "call":
        test_name = item.nodeid
        test_status = rep.outcome  # "passed", "failed", "skipped"
        duration = rep.duration
        error_msg = str(rep.longrepr) if rep.longrepr else ""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ghi vào CSV
        file_exists = CSV_RESULTS_FILE.exists()
        with open(CSV_RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Timestamp",
                    "Test Name",
                    "Status",
                    "Duration (s)",
                    "Error Message",
                    "Screenshot"
                ])
            screenshot_path = ""
            # Chụp screenshot cho Selenium tests khi fail
            if "selenium" in item.keywords and rep.outcome == "failed":
                if hasattr(item, "funcargs") and "chrome_driver" in item.funcargs:
                    driver = item.funcargs["chrome_driver"]
                    try:
                        screenshot_dir = TEST_RESULTS_DIR / "screenshots"
                        screenshot_dir.mkdir(exist_ok=True)
                        
                        safe_test_name = test_name.replace("::", "_").replace("/", "_").replace("\\", "_")
                        timestamp_safe = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_file = screenshot_dir / f"{safe_test_name}_{timestamp_safe}.png"
                        
                        driver.save_screenshot(str(screenshot_file))
                        screenshot_path = str(screenshot_file.relative_to(TEST_RESULTS_DIR.parent))
                    except Exception:
                        pass
            
            writer.writerow([
                timestamp,
                test_name,
                test_status,
                f"{duration:.2f}",
                error_msg[:500] if error_msg else "",
                screenshot_path
            ])

        # Ghi vào Excel (nếu có pandas)
        try:
            import pandas as pd

            # Đọc dữ liệu hiện có nếu file đã tồn tại
            if EXCEL_RESULTS_FILE.exists():
                df_existing = pd.read_excel(EXCEL_RESULTS_FILE)
            else:
                df_existing = pd.DataFrame(columns=[
                    "Timestamp",
                    "Test Name",
                    "Status",
                    "Duration (s)",
                    "Error Message",
                    "Screenshot"
                ])

            # Chụp screenshot cho Selenium tests khi fail
            screenshot_path = ""
            if "selenium" in item.keywords and rep.outcome == "failed":
                if hasattr(item, "funcargs") and "chrome_driver" in item.funcargs:
                    driver = item.funcargs["chrome_driver"]
                    try:
                        screenshot_dir = TEST_RESULTS_DIR / "screenshots"
                        screenshot_dir.mkdir(exist_ok=True)
                        
                        safe_test_name = test_name.replace("::", "_").replace("/", "_").replace("\\", "_")
                        timestamp_safe = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_file = screenshot_dir / f"{safe_test_name}_{timestamp_safe}.png"
                        
                        driver.save_screenshot(str(screenshot_file))
                        screenshot_path = str(screenshot_file.relative_to(TEST_RESULTS_DIR.parent))
                    except Exception:
                        pass

            # Thêm dòng mới
            new_row = pd.DataFrame([{
                "Timestamp": timestamp,
                "Test Name": test_name,
                "Status": test_status,
                "Duration (s)": f"{duration:.2f}",
                "Error Message": error_msg[:500] if error_msg else "",
                "Screenshot": screenshot_path
            }])

            df_updated = pd.concat([df_existing, new_row], ignore_index=True)
            df_updated.to_excel(EXCEL_RESULTS_FILE, index=False, engine="openpyxl")

        except ImportError:
            # Nếu không có pandas/openpyxl thì chỉ ghi CSV
            pass
