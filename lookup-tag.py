import logging
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import selenium.common.exceptions as exc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import argparse
import csv
import re

LOG = logging.getLogger(__name__)


options = Options()


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


def Reverse(lst):
    return [ele for ele in reversed(lst)]

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i', '--input', help="CSV input path")
    parser.add_argument('-o', '--output', help="CSV output path")
    parser.add_argument('-c', '--column', help="Input CSV column number, defaults to first or column named 'serial'")
    parser.add_argument('serial', help="serial or service tag of device", nargs='*')
    args = parser.parse_args()

    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=options)  # needs to be in path

    with open(args.input) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        for row in reader:
            serial = row[0]

            driver.get("https://www.dell.com/support/home/en-us")
            field = wait_for_element_by_id('inpEntrySelection')
            field.send_keys(serial)
            btn = wait_for_element_by_id('txtSearchEs')
            btn.click()

            link = wait_for_element_by_id('quicklink-sysconfig')
            link.click()

            ele = wait_for_element_by_id('systab_originalconfig')

            expand_buttons = driver.find_elements_by_class_name("collapse-toggle")
            for toggle in Reverse(expand_buttons):
                try:
                    toggle.click()  # expand all quantity dropdowns
                except:
                    # dell's wonderful feedback survey dialog is getting in the way here, have to close it.
                    driver.switch_to.frame("iframeSurvey")  # They were also nice enough to put it in an iframe so have to account for that as well
                    driver.find_element(By.ID, "noButtonIPDell").click()
                    driver.switch_to.default_content()

                    # try the click again
                    toggle.click()
            
            output = ele.text
            lines = output.splitlines()

            out_arr = {
                'CPU': [],
                'GPU': [],
                'RAM': [],
                'Storage': [],
                'Network': [],
                'PSU': []
            }

            for id,line in enumerate(lines):
                if re.search("drive", line, re.IGNORECASE) and (re.search("gb", line, re.IGNORECASE) or re.search("tb", line, re.IGNORECASE)):
                    #
                    # STORAGE DEVICE
                    #
                    capacity = ""
                    type = ""
                    connector = ""
                    quantity = ""

                    # find capacity
                    index = line.find("GB")
                    if index == -1:
                        index = line.find("TB")

                    if index != -1:
                        start_index = line.rfind(" ", 0, index) + 1  # find space right before capacity
                        end_index = index + 2  # two char 'GB' or 'TB'
                        capacity = line[start_index:end_index]

                    # find type
                    if re.search("solid state", line, re.IGNORECASE):
                        # ssd
                        if re.search("mix use", line, re.IGNORECASE):
                            type = "Mix Use SSD"
                        else:
                            type = "SSD"
                    elif re.search("hard drive", line, re.IGNORECASE):
                        # hdd
                        index = line.find("RPM")
                        if index == -1:
                            type = "HDD"
                        else:
                            start_index = line.rfind(" ", 0, index) + 1  # find space right before capacity
                            end_index = index + 3  # three char 'RPM'
                            rpm = line[start_index:end_index]
                            type = rpm + " HDD"

                    # find connector
                    if re.search("sata", line, re.IGNORECASE):
                        # sata
                        connector = "SATA"
                    elif re.search("sas", line, re.IGNORECASE):
                        # sas
                        connector = "SAS"

                    # find quantity (need to expand dialog for this)
                    quan_line = lines[id + 2]  # two lines down is the quantity
                    start_index = quan_line.rfind(" ") + 1  # find space right before capacity
                    quantity = quan_line[start_index:]
                    print(quantity)

            exit()

    driver.close()