import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from contextlib import contextmanager
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import os
import requests

# Configure logging
class UTCPlus10Formatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc) + timedelta(hours=10)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

def setup_logging():
    log_dir = Path('./logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'app.log'
    formatter = UTCPlus10Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[handler])

@contextmanager
def get_webdriver():
    options = Options()
    options.add_argument('--incognito')
    
    if os.getenv('DOCKER_ENV') == 'true':
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        options.add_argument("--disable-gpu")
        options.add_argument('--remote-debugging-port=9222')

    # Use the specific ChromeDriver version installed in the Dockerfile
    driver_path = '/usr/local/bin/chromedriver'
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    try:
        yield driver
    finally:
        driver.quit()

def login_to_website(driver, username, password):
    driver.get('https://work.emprevo.com/login')
    time.sleep(2)

    try:
        email_field = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, 'emailaddress'))
        )
        password_wrapper = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, 'password'))
        )
        password_field = password_wrapper.find_element(By.CSS_SELECTOR, 'input[type="password"]')
        login_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, 'login-button'))
        )

        logging.info("Found email & password fields, and login button.")

        email_field.send_keys(username)
        logging.info("Email address entered.")

        password_field.send_keys(password)
        logging.info("Password entered.")

        actual_password = driver.execute_script("return arguments[0].value;", password_field)
        if actual_password != password:
            logging.error("Password not entered correctly.")
            return False

        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'login-button'))
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        logging.info("Scrolled login button into view.")

        driver.execute_script("arguments[0].click();", login_button)
        logging.info("Login button clicked.")

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.worker-calendar-panel'))
        )
        logging.info("Login successful!")
        return True
    except (TimeoutException, ValueError) as e:
        logging.error(f"Login failed: {e}")
        save_debug_info(driver, 'login_failure')
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during login: {e}")
        save_debug_info(driver, 'login_failure')
        return False

def save_debug_info(driver, prefix):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    Path('debug_screenshots').mkdir(exist_ok=True)
    driver.save_screenshot(f'debug_screenshots/{prefix}_{timestamp}.png')

def find_today_column(driver):
    today_date = datetime.now().strftime('%a %-d').lstrip('0')
    try:
        today_column = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{today_date}')]/ancestor::div[contains(@class, 'daycolumn')]"))
        )
        return today_column
    except TimeoutException:
        logging.error("Today's column not found.")
        return None

def get_shift_data(today_column):
    try:
        available_section = today_column.find_element(By.XPATH, ".//div[contains(@class, 'sub-header') and contains(., 'Available')]/following-sibling::div[contains(@class, 'cal-event-container')]")
        shift_data = available_section.text
        return shift_data
    except NoSuchElementException:
        return None