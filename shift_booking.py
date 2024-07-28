from shared_utils import setup_logging, get_webdriver, login_to_website, find_today_column, save_debug_info
from dotenv import load_dotenv
import os
import asyncio
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
from faker import Faker
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

load_dotenv()
fake = Faker()

async def handle_popup(driver):
    try:
        right_panel = await asyncio.to_thread(driver.find_element, By.CSS_SELECTOR, 'div.right-panel.right-panel-active')
        full_name_field = await asyncio.to_thread(right_panel.find_element, By.CSS_SELECTOR, 'input[placeholder="Full name"]')
        accept_button = await asyncio.to_thread(right_panel.find_element, By.XPATH, '//button[contains(text(), "Accept Shift")]')

        random_first_name = fake.first_name()
        await asyncio.to_thread(full_name_field.send_keys, random_first_name)
        await asyncio.to_thread(accept_button.click)

        await asyncio.sleep(2)
        await confirm_job(driver)
    except Exception as e:
        print(f"Error handling popup: {e}")

async def confirm_job(driver):
    try:
        confirm_button = await asyncio.to_thread(driver.find_element, By.NAME, 'Confirm')
        await asyncio.to_thread(confirm_button.click)
        await asyncio.sleep(2)
    except Exception as e:
        print(f"Error confirming job: {e}")

async def check_and_click_shifts(driver, today_column):
    try:
        # Find the available section for today
        available_section = await asyncio.to_thread(
            today_column.find_element,
            By.XPATH,
            ".//div[contains(@class, 'sub-header') and contains(., 'Available')]/following-sibling::div[contains(@class, 'cal-event-container')]"
        )
        
        # Find all available shifts
        available_shifts = await asyncio.to_thread(available_section.find_elements, By.CLASS_NAME, 'cal-event')

        if not available_shifts:
            print("No Shift Available")
            await asyncio.to_thread(save_debug_info, driver, 'no_shifts_found')
            return False
        
        # Filter shifts based on role
        filtered_shifts = []
        for shift in available_shifts:
            role_element = await asyncio.to_thread(shift.find_element, By.CLASS_NAME, 'role')
            role_text = await asyncio.to_thread(role_element.get_attribute, 'innerText')
            if role_text in ['AIN', 'CSE']:
                filtered_shifts.append(shift)
        
        if not filtered_shifts:
            print("No AIN or CSE Shift Available")
            await asyncio.to_thread(save_debug_info, driver, 'no_ain_cse_shifts_found')
            return False
        
        # Click on each filtered shift and handle the popup
        for shift in filtered_shifts:
            await asyncio.to_thread(shift.click)
            await asyncio.sleep(2)
            await handle_popup(driver)
        
        return True

    except NoSuchElementException:
        print("No shifts found.")
        await asyncio.to_thread(save_debug_info, driver, 'no_shifts_found')
        return False

async def check_and_book_shifts():
    setup_logging()
    
    with get_webdriver() as driver:
        username = os.getenv('USERNAME')
        password = os.getenv('PASSWORD')
        
        if await asyncio.to_thread(login_to_website, driver, username, password):
            today_column = await asyncio.to_thread(find_today_column, driver)
            if today_column:
                await check_and_click_shifts(driver, today_column)

def run_shift_booking():
    asyncio.run(check_and_book_shifts())
    logging.info("Shift booking script triggered.")

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/trigger':
            run_shift_booking()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Shift booking triggered')
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, RequestHandler)
    logging.info('Starting server on port 8000...')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()