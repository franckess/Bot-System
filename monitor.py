import logging
from dotenv import load_dotenv
import os
from shared_utils import setup_logging, get_webdriver, login_to_website, save_debug_info
from datetime import datetime, timedelta
from difflib import unified_diff
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import subprocess
import requests

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
log_dir = Path('./logs')
log_file = log_dir / 'app.log'

def get_days_of_week():
    today = datetime.now()
    # If today is Sunday (weekday() == 6), start from today; otherwise, start from the previous Sunday
    start_of_week = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    days_of_week = [(start_of_week + timedelta(days=i)).strftime('%a %-d') for i in range(7)]
    return days_of_week

def get_specific_section_html(driver):
    try:
        today_date = datetime.now().strftime('%a %-d')
        xpath_string = f"//div[contains(@class, 'daycolumn')]//span[contains(text(), '{today_date}')]/ancestor::div[contains(@class, 'daycolumn')]"
        specific_section = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, xpath_string))
        )
        section_html = specific_section.get_attribute('outerHTML')
        return section_html
    except TimeoutException:
        logging.error("Specific section not found.")
        return None

def get_all_sections_html(driver):
    try:
        days_of_week = get_days_of_week()
        all_sections_html = {}

        for day in days_of_week:
            xpath_string = f"//div[contains(@class, 'daycolumn')]//span[contains(text(), '{day}')]/ancestor::div[contains(@class, 'daycolumn')]"
            try:
                specific_section = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, xpath_string))
                )
                section_html = specific_section.get_attribute('outerHTML')
                all_sections_html[day] = section_html
            except TimeoutException:
                logging.error(f"Section for {day} not found.")
                all_sections_html[day] = None

        return all_sections_html
    except Exception as e:
        logging.error(f"An error occurred while retrieving sections: {e}")
        return None

def extract_ng_star_inserted_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    ng_star_inserted = soup.find_all(class_='ng-star-inserted')
    filtered_events = []
    for element in ng_star_inserted:
        if element.find(class_='role') and element.find(class_='role').get_text() in ['AIN', 'CSE']:
            filtered_events.append(str(element))
    return '\n'.join(filtered_events)

def compare_html(old_html, new_html):
    old_event_container = extract_ng_star_inserted_content(old_html)
    new_event_container = extract_ng_star_inserted_content(new_html)
    
    diff = unified_diff(
        old_event_container.splitlines(), 
        new_event_container.splitlines(), 
        fromfile='old_event_container.html', 
        tofile='new_event_container.html', 
        lineterm=''
    )
    return list(diff)

def log_changes(changes):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'./logs/html_changes_{timestamp}.log'
    with open(log_file, 'w') as f:
        for line in changes:
            f.write(line + '\n')
    logging.info(f'Changes logged to {log_file}')

def monitor_available_section(driver, username, password, check_interval=3, max_duration_mins=10):
    max_runs = (max_duration_mins * 60) // check_interval

    if not login_to_website(driver, username, password):
        return

    run_count = 0
    previous_html = {}
    signal_file = log_dir / 'trigger_shift_booking_signal.txt'

    while run_count < max_runs:
        time.sleep(check_interval)
        driver.refresh()

        current_html = get_all_sections_html(driver)
        if not current_html:
            continue

        for day, html in current_html.items():
            if html and html != previous_html.get(day):
                changes = compare_html(previous_html.get(day, ''), html)
                if changes:
                    logging.info(f"Change detected in the monitored section for {day}.")
                    log_changes(changes)
                    previous_html[day] = html
                    with open(signal_file, 'w') as f:
                        f.write('trigger')
                    
                    # Trigger shift_booking service
                    response = requests.post('http://shift_booking_service:8000/trigger')
                    if response.status_code == 200:
                        logging.info("Shift booking triggered successfully.")
                    else:
                        logging.error(f"Failed to trigger shift booking: {response.status_code}")
                else:
                    logging.info(f"No significant change detected in the monitored section for {day}.")
            else:
                logging.info(f"No change in the monitored section for {day}.")

        run_count += 1
        logging.info(f"Run {run_count}/{max_runs} completed.")

        with open(log_file, 'r') as f:
            log_contents = f.read()
            print(log_contents)

    logging.info("Max duration reached. Stopping monitoring.")

def main():
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')

    with get_webdriver() as driver:
        monitor_available_section(driver, username, password)

if __name__ == '__main__':
    main()