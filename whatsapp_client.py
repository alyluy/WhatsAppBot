"""whatsapp_client.py
Интеграция с WhatsApp Web через Selenium.
"""

import os
import re
import subprocess
import time
from typing import Dict, Optional

import chromedriver_autoinstaller
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
        self.auth_timeout_sec = int(os.getenv("WA_AUTH_TIMEOUT_SEC", "300"))

        self.driver = None
        self.wait = None
        self.last_error = ""

    @staticmethod
    def _extract_major(version_text: str) -> Optional[str]:
        match = re.search(r"(\\d+)\\.", version_text)
        if not match:
            return None
        return match.group(1)

    def _read_chrome_major(self) -> Optional[str]:
        chrome_bin = self.chrome_binary or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if not chrome_bin or not os.path.exists(chrome_bin):
            return None
        try:
            output = subprocess.check_output([chrome_bin, "--version"], text=True).strip()
            return self._extract_major(output)
        except Exception:
            return None

    def _read_driver_major(self, driver_path: str) -> Optional[str]:
        if not driver_path or not os.path.exists(driver_path):
            return None
        try:
            output = subprocess.check_output([driver_path, "--version"], text=True).strip()
            return self._extract_major(output)
        except Exception:
            return None

    def start(self):
        options = webdriver.ChromeOptions()

        if self.chrome_binary:
            options.binary_location = self.chrome_binary

        if self.chrome_user_data_dir:
            options.add_argument(f"user-data-dir={self.chrome_user_data_dir}")

        service = None
        chrome_major = self._read_chrome_major()
        driver_major = self._read_driver_major(self.chromedriver_path) if self.chromedriver_path else None

        # Если путь задан и версия совпадает, используем его.
        if self.chromedriver_path and chrome_major and driver_major and chrome_major == driver_major:
            service = Service(executable_path=self.chromedriver_path)
        else:
            # Иначе подбираем совместимый драйвер автоматически.
            auto_driver_path = chromedriver_autoinstaller.install()
            service = Service(executable_path=auto_driver_path)

        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 25)

    def open(self):
        if not self.driver:
            raise RuntimeError("Driver is not started")

        self.driver.get(self.web_url)
        # После открытия может быть:
        # 1) уже авторизованный сеанс -> сразу список чатов
        # 2) QR-страница -> нужен логин и затем загрузка списка чатов
        ready_selectors = [
            (By.ID, "pane-side"),
            (By.ID, "side"),
            (By.XPATH, "//div[@role='grid']"),
            (By.XPATH, "//div[@aria-label='Chat list']"),
            (By.XPATH, "//div[contains(@data-testid, 'chat-list')]"),
            (By.XPATH, "//div[contains(@class, 'two') and @id='app']"),
        ]

        for by, selector in ready_selectors:
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((by, selector))
                )
                return
            except TimeoutException:
                continue

        print("Ожидание авторизации по QR и загрузки списка чатов...")
        qr_selectors = [
            (By.XPATH, "//canvas"),
            (By.XPATH, "//div[contains(@data-ref,'@')]"),
            (By.XPATH, "//div[contains(., 'Сканируйте QR-код')]"),
            (By.XPATH, "//div[contains(., 'Scan the QR code')]"),
        ]
        has_qr = any(self.driver.find_elements(by, selector) for by, selector in qr_selectors)
        if has_qr:
            print("Обнаружен QR-код. Отсканируйте его в WhatsApp на телефоне.")

        try:
            WebDriverWait(self.driver, self.auth_timeout_sec).until(
                lambda d: any(d.find_elements(by, selector) for by, selector in ready_selectors)
            )
        except TimeoutException as error:
            raise TimeoutException(
                f"Не удалось дождаться авторизации WhatsApp за {self.auth_timeout_sec} сек."
            ) from error

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None

    def get_last_error(self) -> str:
        return self.last_error

    def _open_chat(self, chat_name: str):
        if not self.driver or not self.wait:
            raise RuntimeError("Driver is not started")

        # Сначала пытаемся кликнуть чат напрямую, если он уже виден в списке.
        direct_chat_xpath = f"//span[@title=\"{chat_name}\"]"
        direct_chat_elements = self.driver.find_elements(By.XPATH, direct_chat_xpath)
        if direct_chat_elements:
            try:
                direct_chat_elements[0].click()
                time.sleep(0.5)
                return
            except Exception:
                pass

        search_xpath_candidates = [
            "//div[@role='textbox' and @contenteditable='true'][@data-tab='3']",
            "//div[@role='textbox' and @contenteditable='true'][@data-tab='2']",
            "//div[@contenteditable='true'][@data-tab='10']",
            "//div[@id='side']//div[@role='textbox' and @contenteditable='true']",
            "//div[@id='side']//div[@contenteditable='true']",
            "//div[@role='textbox' and @contenteditable='true'][contains(@aria-label, 'Search')]",
            "//div[@role='textbox' and @contenteditable='true'][contains(@aria-label, 'Поиск')]",
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
        # Для contenteditable clear() часто не работает, используем Cmd+A + Delete.
        search_box.send_keys(Keys.COMMAND, "a")
        search_box.send_keys(Keys.BACKSPACE)
        search_box.send_keys(chat_name)
        time.sleep(1)

        chat_title_xpath = f"//span[@title=\"{chat_name}\"]"
        chat_element = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, chat_title_xpath))
        )
        chat_element.click()
        time.sleep(0.5)

    def ensure_chat_open(self, chat_name: str):
        """Гарантирует, что нужный чат открыт."""
        self._open_chat(chat_name)

    def send_message(self, chat_name: str, message: str) -> bool:
        try:
            self.last_error = ""
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
            safe_message = "".join(ch for ch in str(message) if ord(ch) <= 0xFFFF)
            if safe_message != str(message):
                self.last_error = "Сообщение содержит символы вне BMP, они удалены перед отправкой."
            input_box.send_keys(safe_message)
            input_box.send_keys(Keys.ENTER)
            return True
        except Exception as error:
            self.last_error = f"{type(error).__name__}: {error}"
            return False

    def _read_last_message(self, direction_class: str) -> Optional[str]:
        candidates = []

        # Основной путь: контейнеры copyable-text внутри message-in/message-out
        candidates.extend(
            self.driver.find_elements(
                By.XPATH,
                f"//div[contains(@class,'{direction_class}')]//div[contains(@class,'copyable-text')]",
            )
        )
        # Fallback: selectable-text span
        candidates.extend(
            self.driver.find_elements(
                By.XPATH,
                f"//div[contains(@class,'{direction_class}')]//span[contains(@class,'selectable-text')]",
            )
        )

        if not candidates:
            return None

        for element in reversed(candidates):
            text = (element.text or "").strip()
            if text:
                return text

        return None

    @staticmethod
    def _extract_sender_from_pre_plain_text(pre_plain_text: str) -> Optional[str]:
        if not pre_plain_text:
            return None
        # Формат обычно вида: "[12:34, 29.03.2026] Имя: "
        match = re.search(r"\]\s(.+?):\s*$", pre_plain_text)
        if not match:
            return None
        return match.group(1).strip() or None

    def _read_last_message_event(self, direction_class: str) -> Optional[Dict[str, str]]:
        message_containers = self.driver.find_elements(
            By.XPATH,
            f"//div[contains(@class,'{direction_class}')]//div[contains(@class,'copyable-text')]",
        )

        for container in reversed(message_containers):
            text = (container.text or "").strip()
            if not text:
                continue

            pre_plain_text = container.get_attribute("data-pre-plain-text") or ""
            sender = self._extract_sender_from_pre_plain_text(pre_plain_text) or "unknown"
            signature = f"{pre_plain_text}|{text}"
            return {
                "sender": sender,
                "text": text,
                "signature": signature,
            }

        # Fallback: если copyable-text не найден, пробуем по selectable-text.
        selectable = self.driver.find_elements(
            By.XPATH,
            f"//div[contains(@class,'{direction_class}')]//span[contains(@class,'selectable-text')]",
        )
        for element in reversed(selectable):
            text = (element.text or "").strip()
            if text:
                return {
                    "sender": "unknown",
                    "text": text,
                    "signature": text,
                }

        return None

    def read_last_incoming_message(self, chat_name: str, ensure_open: bool = True) -> Optional[str]:
        """Читает последнее входящее сообщение из выбранного чата."""
        if ensure_open:
            self._open_chat(chat_name)

        return self._read_last_message("message-in")

    def read_last_outgoing_message(self, chat_name: str, ensure_open: bool = True) -> Optional[str]:
        """Читает последнее исходящее сообщение (режим локального теста)."""
        if ensure_open:
            self._open_chat(chat_name)

        return self._read_last_message("message-out")

    def read_last_incoming_event(self, chat_name: str, ensure_open: bool = True) -> Optional[Dict[str, str]]:
        """Читает последнее входящее сообщение с автором."""
        if ensure_open:
            self._open_chat(chat_name)
        return self._read_last_message_event("message-in")

    def read_last_outgoing_event(self, chat_name: str, ensure_open: bool = True) -> Optional[Dict[str, str]]:
        """Читает последнее исходящее сообщение с автором (режим локального теста)."""
        if ensure_open:
            self._open_chat(chat_name)
        return self._read_last_message_event("message-out")
