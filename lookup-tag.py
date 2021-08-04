import logging
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import selenium.common.exceptions as exc

LOG = logging.getLogger(__name__)


options = Options()
driver = webdriver.Chrome(chrome_options=options)


def wait_for_element_by_xpath(expr, maxwait=10):
    start = time.time()
    LOG.info('looking for xpath expression=%s', expr)
    while True:
        try:
            res = driver.find_element_by_xpath(expr)
            return res
        except exc.NoSuchElementException:
            if time.time() - maxwait > start:
                raise
            time.sleep(0.5)


def wait_for_element_by_id(expr, maxwait=10):
    start = time.time()
    LOG.info('looking for element id=%s', expr)
    while True:
        try:
            res = driver.find_element_by_id(expr)
            return res
        except exc.NoSuchElementException:
            if time.time() - start > maxwait:
                raise
            time.sleep(0.5)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    service_tag = sys.argv[1]

    driver.get("https://www.dell.com/support/home/en-us")
    field = wait_for_element_by_id('inpEntrySelection')
    btn = wait_for_element_by_id('txtSearchEs')
    field.send_keys(service_tag)
    btn.click()

    link = wait_for_element_by_id('quicklink-sysconfig')
    link.click()

    ele = wait_for_element_by_id('systab_originalconfig')
    print(ele.text)
    driver.close()
