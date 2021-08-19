import logging
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

    inventory = []
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
                'tag': serial,
                'cpu': [],
                'ram': [],
                'storage': [],
                'network': [],
                'psu': []
            }

            for id,line in enumerate(lines):
                if re.search("drive", line, re.IGNORECASE) and (re.search("gb", line, re.IGNORECASE) or re.search("tb", line, re.IGNORECASE)):
                    #
                    # STORAGE DEVICE
                    #
                    specs = {
                        'capacity': "",
                        'type': "",
                        'connector': "",
                        'quantity': ""
                    }

                    # find capacity
                    index = line.find("GB")
                    if index == -1:
                        index = line.find("TB")

                    if index != -1:
                        start_index = line.rfind(" ", 0, index) + 1  # find space right before capacity
                        end_index = index + 2  # two char 'GB' or 'TB'
                        specs['capacity'] = line[start_index:end_index]

                    # find type
                    if re.search("solid state", line, re.IGNORECASE):
                        # ssd
                        if re.search("mix use", line, re.IGNORECASE):
                            specs['type'] = "Mix Use SSD"
                        else:
                            specs['type'] = "SSD"
                    elif re.search("hard drive", line, re.IGNORECASE):
                        # hdd
                        index = line.find("RPM")
                        if index == -1:
                            specs['type'] = "HDD"
                        else:
                            start_index = line.rfind(" ", 0, index) + 1  # find space right before capacity
                            end_index = index + 3  # three char 'RPM'
                            rpm = line[start_index:end_index]
                            specs['type'] = rpm + " HDD"

                    # find connector
                    if re.search("sata", line, re.IGNORECASE):
                        # sata
                        specs['connector'] = "SATA"
                    elif re.search("sas", line, re.IGNORECASE):
                        # sas
                        specs['connector'] = "SAS"

                    # find quantity (need to expand dialog for this)
                    quan_line = lines[id + 2]  # two lines down is the quantity
                    start_index = quan_line.rfind(" ") + 1  # find space right before capacity
                    specs['quantity'] = quan_line[start_index:]

                    # final array
                    out_arr['storage'].append(specs)
                elif (re.search("intel", line, re.IGNORECASE) or re.search("amd", line, re.IGNORECASE)) and re.search("ghz", line, re.IGNORECASE):
                    #
                    # CPU
                    #
                    specs = {
                        'type': "",
                        'speed': "",
                        'cores': "",
                        'quantity': ""
                    }

                    # find type
                    index = line.find("Intel")
                    if index == -1:
                        index = line.find("AMD")

                    speed_index = line.find("GHz")
                    if index != -1:
                        start_index = index
                        end_index = speed_index - 4
                        specs['type'] = line[start_index:end_index]

                    # find speed
                    start_index = speed_index - 3
                    end_index = speed_index + 3
                    specs['speed'] = line[start_index:end_index]

                    # find core count
                    index = line.find("C/")
                    start_index = index - 2
                    end_index = index + 4
                    specs['cores'] = line[start_index:end_index]

                    # find quantity
                    quan_line = lines[id + 2]  # two lines down is the quantity
                    start_index = quan_line.rfind(" ") + 1  # find space right before capacity
                    specs['quantity'] = quan_line[start_index:]

                    # final array
                    out_arr['cpu'].append(specs)
                elif re.search("gb", line, re.IGNORECASE) and re.search("dimm", line, re.IGNORECASE) and line.count(' ') == 2:
                    #
                    # RAM
                    #
                    specs = {
                        'capacity': "",
                        'type': "",
                        'quantity': ""
                    }

                    parts = line.split(" ")
                    if len(parts) != 3:
                        continue

                    part_num = parts[0]
                    desc = parts[1]
                    specs['quantity'] = parts[2]

                    speclist = desc.split(",")

                    for item in speclist:
                        if "GB" in item:
                            specs['capacity'] = item
                        elif "DDR" in item:
                            specs['type'] = item

                    out_arr['ram'].append(specs)

            inventory.append(out_arr)

    with open(args.output, 'w') as output_file:
        writer = csv.writer(output_file)
        header = ['service tag', 'cpu', 'gpu', 'ram', 'storage', 'network', 'psu']
        writer.writerow(header)
        for item in inventory:
            row = []
            row.append(item['tag'])  # add service tag to row

            out_string = ""
            for cpu_item in item['cpu']:
                if out_string != "":
                    out_string += " | "
                out_string += cpu_item['quantity'] + "x " + cpu_item['type'] + " " + cpu_item['cores'] + " " + cpu_item['speed']
            row.append(out_string)  # add CPU to row

            # GPU NOT YET IMPLEMENTED
            row.append("")

            out_string = ""
            for ram_item in item['ram']:
                if out_string != "":
                    out_string += " | "
                total_capacity = int(ram_item['capacity'][:ram_item['capacity'].find("GB")]) * int(ram_item['quantity'])
                out_string = ram_item['quantity'] + "x " + ram_item['capacity'] + " " + ram_item['type'] + " Total: " + str(total_capacity) + "GB"
            row.append(out_string)  # add RAM to row

            out_string = ""
            for storage_item in item['storage']:
                if out_string != "":
                    out_string += " | "
                out_string = storage_item['quantity'] + "x " + storage_item['capacity'] + " " + storage_item['type'] + " " + storage_item['connector']
            row.append(out_string)

            # NETWORK NOT YET IMPLEMENTED
            row.append("")

            # PSU NOT YET IMPLEMENTED
            row.append("")

            writer.writerow(row)

    driver.close()