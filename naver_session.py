import json

import chromedriver_autoinstaller_fix
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

CHROMEDRIVER_PATH = "./chromedriver/"


class NaverSession:
    session: requests.Session

    def __init__(self, session: requests.Session):
        self.session = session

    def save(self, file_name: str):
        cookies = self.session.cookies.get_dict()
        with open(file_name, mode="w", encoding="utf8") as f:
            f.write(json.dumps(cookies))

    @classmethod
    def _get_driver(cls) -> webdriver.Chrome:
        driver_path = chromedriver_autoinstaller_fix.install(path=CHROMEDRIVER_PATH)
        assert driver_path
        return webdriver.Chrome(service=Service(executable_path=driver_path))

    @classmethod
    def from_cookies(cls, cookies: dict):
        s = requests.Session()

        for name, value in cookies.items():
            s.cookies.set(name, value)

        return cls(s)

    @classmethod
    def login(cls, username: str, password: str):
        driver = cls._get_driver()

        driver.get("https://nid.naver.com/nidlogin.login")

        timeout = 5
        try:
            element_present = EC.presence_of_element_located((By.ID, "id"))
            WebDriverWait(driver, timeout).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load")

        driver.find_element(By.ID, "id").send_keys(username)
        driver.find_element(By.ID, "pw").send_keys(password)
        driver.find_element(By.ID, "log.login").click()

        wait = WebDriverWait(driver, 600)
        wait.until(lambda driver: "https://nid.naver.com/" not in driver.current_url)

        cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}

        return cls.from_cookies(cookies)

    @classmethod
    def from_file(cls, file_name: str):
        with open(file_name, mode="r", encoding="utf8") as f:
            cookies = json.loads(f.read())
        return cls.from_cookies(cookies)
