"""whatsapp_client.py
Интеграция с WhatsApp Web через Selenium.
"""

import os
import time
from typing import Optional

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


load_dotenv()


class WhatsAppClient:
    def __init__(self):
        self.web_url = os.getenv("WA_WEB_URL", "https://web.whatsapp.com/")
        self.chrome_binary = os.getenv("WA_CHROME_BINARY")
        self.chromedriver_path = os.getenv("WA_CHROMEDRIVER_PATH")
        self.chrome_user_data_dir = os.getenv("WA_CHROME_USER_DATA_DIR")
        self.default_chat = os.getenv("WA_DEFAULT_CHAT", "")

        self.driver = None
        self.wait = None

    def start(self):
        options = webdriver.ChromeOptions()

        if self.chrome_binary:
            options.binary_location = self.chrome_binary

        if self.chrome_user_data_dir:
            options.add_argument(f"user-data-dir={self.chrome_user_data_dir}")

        service = None
        if self.chromedriver_path:
            service = Service(executable_path=self.chromedriver_path)

        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 25)

    def open(self):
        if not self.driver:
            raise RuntimeError("Driver is not started")

        self.driver.get(self.web_url)
        # Ждем загрузку левого списка чатов.
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='pane-side']"))
        )

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None

    def _open_chat(self, chat_name: str):
        if not self.driver or not self.wait:
            raise RuntimeError("Driver is not started")

        search_xpath_candidates = [
            "//div[@role='textbox' and @contenteditable='true'][@data-tab='3']",
            "//div[@role='textbox' and @contenteditable='true'][@data-tab='2']",
            "//div[@role='textbox' and @contenteditable='true'][contains(@aria-label, 'Search')]",
        ]

        search_box = None
        for xpath in search_xpath_candidates:
            try:
                search_box = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if search_box:
                    break
            except TimeoutException:
                continue

        if not search_box:
            raise RuntimeError("Не найдено поле поиска чатов в WhatsApp Web")

        search_box.click()
        search_box.clear()
        search_box.send_keys(chat_name)
        time.sleep(1)

        chat_title_xpath = f"//span[@title=\"{chat_name}\"]"
        chat_element = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, chat_title_xpath))
        )
        chat_element.click()
        time.sleep(0.5)

    def send_message(self, chat_name: str, message: str) -> bool:
        try:
            self._open_chat(chat_name)
            input_box = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//footer//div[@role='textbox' and @contenteditable='true']",
                    )
                )
            )
            input_box.click()
            input_box.send_keys(message)
            input_box.send_keys(Keys.ENTER)
            return True
        except Exception:
            return False

    def read_last_incoming_message(self, chat_name: str) -> Optional[str]:
        """Читает последнее входящее сообщение из выбранного чата."""
        self._open_chat(chat_name)

        incoming_messages = self.driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'message-in')]//span[contains(@class,'selectable-text')]/span",
        )

        if not incoming_messages:
            return None

        return incoming_messages[-1].text.strip()
