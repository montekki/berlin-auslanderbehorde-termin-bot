import time
import os
import logging
from platform import system

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

system = system()

logging.basicConfig(
    format='%(asctime)s\t%(levelname)s\t%(message)s',
    level=logging.INFO,
)

class WebDriver:
    def __init__(self):
        self._driver: webdriver.Chrome
        self._implicit_wait_time = 20

    def __enter__(self) -> webdriver.Chrome:
        logging.info("Open browser")
        # some stuff that prevents us from being locked out
        options = webdriver.ChromeOptions() 
        options.add_argument('--disable-blink-features=AutomationControlled')
        self._driver = webdriver.Chrome(options=options)
        self._driver.implicitly_wait(self._implicit_wait_time) # seconds
        self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
        return self._driver

    def __exit__(self, exc_type, exc_value, exc_tb):
        logging.info("Close browser")
        self._driver.quit()

class BerlinBot:
    def __init__(self):
        self.wait_time = 20
        self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
        self._error_message = """Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte"""

    @staticmethod
    def enter_start_page(driver: webdriver.Chrome):
        logging.info("Visit start page")
        driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen")
        driver.find_element(By.XPATH, '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a').click()

    @staticmethod
    def tick_off_some_bullshit(driver: webdriver.Chrome):
        logging.info("Ticking off agreement")

        tick_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="xi-div-1"]/div[4]/label[2]/p')
                ))

        tick_element.click()

        proceed_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'applicationForm:managedForm:proceed'))
                )

        proceed_element.click()

    @staticmethod
    def enter_form(driver: webdriver.Chrome):
        logging.info("Fill out form")

        first_choice = WebDriverWait(driver, 50).until(
                EC.presence_of_element_located(
                    (By.ID, 'xi-sel-400'))
                )

        s = Select(first_choice)
        s.select_by_visible_text("Russische Föderation")

        second_choice = WebDriverWait(driver, 50).until(
                EC.presence_of_element_located(
                    (By.ID, 'xi-sel-422'))
                )

        s = Select(second_choice)
        s.select_by_visible_text("zwei Personen")

        third_choice = WebDriverWait(driver, 50).until(
                EC.presence_of_element_located(
                    (By.ID, 'xi-sel-427'))
                )

        s = Select(third_choice)
        s.select_by_visible_text("ja")


        fourth_choice = WebDriverWait(driver, 50).until(
                EC.presence_of_element_located(
                    (By.ID, 'xi-sel-428'))
                )

        time.sleep(5)

        s = Select(fourth_choice)
        s.select_by_visible_text("Russische Föderation")

        time.sleep(5)
        # apply for residence
        apply = WebDriverWait(driver, 50).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="xi-div-30"]/div[1]/label/p'))
                )

        apply.click()

        erwerbst = WebDriverWait(driver, 50).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(),'Erwerbstätigkeit')]"))
                )

        erwerbst.click()


        blau = WebDriverWait(driver, 50).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Blaue Karte EU')]")))


        blau.click()

        submit = WebDriverWait(driver, 50).until(
                EC.element_to_be_clickable(
                    (By.ID, 'applicationForm:managedForm:proceed')))

        submit.click()
    
    def _success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        while True:
            self._play_sound_osx(self._sound_file)
            time.sleep(15)
        
        # todo play something and block the browser


    def run_once(self):
        with WebDriver() as driver:
            self.enter_start_page(driver)
            self.tick_off_some_bullshit(driver)
            self.enter_form(driver)

            # retry submit
            while True:
                if not self._error_message in driver.page_source:
                    self._success()
                logging.info("Retry submitting form")

                time.sleep(60)

                try:
                    submit = WebDriverWait(driver, 40).until(
                        EC.element_to_be_clickable(
                        (By.ID, 'applicationForm:managedForm:proceed')))

                    submit.click()
                except Exception as e:
                    logging.error("{}".format(e))
                    break

    def run_loop(self):
        # play sound to check if it works
        # self._play_sound_osx(self._sound_file)
        while True:
            logging.info("One more round")
            try:
                self.run_once()
            except Exception as e:
                logging.error("{}".format(e))
            # time.sleep(self.wait_time)

    # stolen from https://github.com/JaDogg/pydoro/blob/develop/pydoro/pydoro_core/sound.py
    @staticmethod
    def _play_sound_osx(sound, block=True):
        """
        Utilizes AppKit.NSSound. Tested and known to work with MP3 and WAVE on
        OS X 10.11 with Python 2.7. Probably works with anything QuickTime supports.
        Probably works on OS X 10.5 and newer. Probably works with all versions of
        Python.
        Inspired by (but not copied from) Aaron's Stack Overflow answer here:
        http://stackoverflow.com/a/34568298/901641
        I never would have tried using AppKit.NSSound without seeing his code.
        """
        from AppKit import NSSound
        from Foundation import NSURL
        from time import sleep

        logging.info("Play sound")
        if "://" not in sound:
            if not sound.startswith("/"):
                from os import getcwd

                sound = getcwd() + "/" + sound
            sound = "file://" + sound
        url = NSURL.URLWithString_(sound)
        nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
        if not nssound:
            raise IOError("Unable to load sound named: " + sound)
        nssound.play()

        if block:
            sleep(nssound.duration())

if __name__ == "__main__":
    BerlinBot().run_loop()
