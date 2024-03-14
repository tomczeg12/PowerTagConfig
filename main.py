import getpass
import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from file_operations import File
import time

# Formatter configuration
formatter = logging.Formatter('%%(name)s - %(levelname)s - %(message)s')

# FileHandler configurationgi
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(formatter)

# StreamHandler configuration
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# Logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


# JavaScript Script
script = """
console.log('Script started');
var parentElement = document.querySelector('se-fab');
if (parentElement && parentElement.shadowRoot) {
    console.log('Shadow root found');
    // First button click
    var firstButton = parentElement.shadowRoot.querySelector('se-button');
    if (firstButton) {
        console.log('First button found:', firstButton);
        firstButton.click();
        console.log('First button clicked');
    } else {
        console.log('First button not found in shadow root');
    }
    // Second button click
    var secondButton = parentElement.querySelector('se-button[icon="action_save"]');
    if (secondButton) {
        console.log('Second button found:', secondButton);
        secondButton.click();
        console.log('Second button clicked');
    } else {
        console.log('Second button not found in shadow root');
    }
} else {
    console.log('Parent element or shadow root not found');
}
"""


def initialize_driver() -> webdriver.Chrome:
    """
    Initializes and returns a Chrome WebDriver with implicit wait set.

    :return: An instance of Chrome WebDriver with implicit wait configured.
    """
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    return driver


def navigate_to_url(driver: webdriver.Chrome, url: str) -> None:
    """
    Navigates to a specified URL using the provided WebDriver.

    :param driver: The WebDriver instance to use for navigation.
    :param url: The URL to navigate to.
    """
    driver.get(url)


def handle_security_warning(driver: webdriver.Chrome) -> None:
    """
    Attempts to bypass any security warning that might appear when navigating to a site.


    :param driver: The WebDriver instance to use for navigating.
    """
    try:
        # Wait for the security details button to be clickable and click it
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'details-button'))).click()
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'proceed-link'))).click()
    except (NoSuchElementException, TimeoutException):
        logging.info("Security warning not found or not clickable.")


def login_to_site(driver: webdriver.Chrome, password: str) -> None:
    """
    Logs into the website using provided credentials.

    :param driver: The WebDriver instance to use for operations.
    :param password: The password for logging in.
    """
    try:
        login_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'username')))
        password_input = driver.find_element(By.ID, 'password')
        login_button = driver.find_element(By.CLASS_NAME, 'login-btn')

        login_input.send_keys("SecurityAdmin")
        password_input.send_keys(password)
        login_button.click()
    except NoSuchElementException:
        logging.error("Login elements not found.")


def search_for_new_powertags(driver: webdriver.Chrome) -> None:
    """
    Initiates a search for new PowerTags on the PAS600 site.

    :param driver: The WebDriver instance used for interacting with the webpage.
    """
    # Navigations and interactions for finding new PowerTags
    try:
        driver.find_element(By.XPATH, '//a[@routerlink="/settings"]').click()
        driver.find_element(By.XPATH, '//app-card-menu-dumb[@cardtitle="Wireless Devices"]').click()
        driver.find_element(By.XPATH, '//se-list-item[2]').click()  # Simplified XPATH
        driver.find_element(By.XPATH, '//*[@id="switchbutton"]').click()
        logger.info("Searching for new PowerTags...")
        WebDriverWait(driver, 120, 1).until_not(lambda d: d.find_element(By.XPATH,
                                                                         '//*[@id="ZigBeePermitJoin.Information_elements.disco_status"]').text == "Searching")
        logger.info("Search completed.")
    except NoSuchElementException:
        logger.error("Error occurred while searching for new PowerTags.")


def configure_powertags(driver: webdriver.Chrome, file_path: str) -> None:
    """
    Configures PowerTags using data from a file.

    :param driver: The WebDriver instance used for webpage interactions.
    :param file_path: The path to the CSV file containing PowerTags data.
    """
    file_object = File(file_path)
    pt_data = file_object.load_data()
    if pt_data is None:
        logging.error("Failed to load PowerTag data from file.")
        return

    n = 0
    while True:
        n += 1
        path = (f'/html/body/se-app/app-root/app-shell/se-container/app-tab/se-container/se-block/se-block-content/se'
                f'-list/se-container/se-list/app-generic-treeview/app-generic-treeview-dumb/se-list-group/se-block[{str(n)}]')
        try:
            driver.find_element(By.XPATH, path).click()
            # Finding QR code
            time.sleep(5)
            rfid = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="ZigBeeGreenPowerDevice.Identification_elements.source_id.value"]'))).get_attribute(
                "value")[-4::]
            logging.info(f'A PowerTag with RFID: {rfid} is currently being configured.')

            name, label = file_object.get_information(rfid)
            if name != '' and label != '':
                # Filling the field Name
                fname = driver.find_element(By.XPATH, '//*[@id="PhysicalIdentification.UserApplicationName_value"]')
                fname.clear()
                fname.send_keys(name)
                # Filling the field Label
                flabel = driver.find_element(By.XPATH, '//*[@id="ElectricalTopology.Label"]')
                flabel.clear()
                flabel.send_keys(label)
                # Filling the field Virtual server ID
                fserver_id = driver.find_element(By.XPATH,
                                                 '//*[@id="Device.Component_virtual_device_elements.unit_id.value-number"]')
                fserver_id.clear()
                fserver_id.send_keys(name[-2::])

                driver.execute_script(script)

                logging.info(f"Powertag {name} : {label} has been configured correctly.")
                file_object.mark_mounted(name, "OK")
                time.sleep(3)

                # Checking if the values are correct
                reply = check_values(driver)
                if reply == 0:
                    file_object.mark_mounted(name, 'Attention, check the readings!')
                    logging.warning(f"{name}: Attention, check the readings!")
                else:
                    if reply == -1:
                        # Changing the orientation of the current flow
                        select_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "ElectricalCharacteristics.CurrentFlow"))
                        )
                        # Now that we have the <select> element, we initialize a Select object
                        select_obj = Select(select_element)
                        # And then select the "Reverse" option by visible text
                        select_obj.select_by_visible_text("Reverse")
                        logging.warning(f"{name}: The direction of current flow has been changed")
                    else:
                        logging.info(f"{name}: Correct readings")
                    file_object.mark_mounted(name, 'OK')
        except NoSuchElementException:
            logging.info(f"Adding {n} PowerTags has been completed")
            break

    file_object.save_data()


def check_values(driver: webdriver.Chrome) -> int:
    """
        Checks if data from current PowerTag is correct.

        :param driver: The WebDriver instance used for webpage interactions.
    """
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(By.XPATH, '//*[@id="real-time-button"]')).click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(By.XPATH,
                                                                   '/html/body/se-app/app-root/app-shell/se-container/app-real-time/se-container/se-block/se-block-content/div/div[1]/div[2]')).click()
    time.sleep(5)
    # -1 - Current flow needs to be change; 0 - Electrical or other problem to check by engineer, 1 - readings are OK
    is_correct = 0

    try:
        # Locate the element containing "Total power factor" text
        # This assumes that the title attribute's presence is a reliable indicator
        pf_element = driver.find_element(By.XPATH, "//se-table-item[@title='Total power factor']")
        pa_element = driver.find_element(By.XPATH, "//se-table-item[@title='Active power A']")
        pb_element = driver.find_element(By.XPATH, "//se-table-item[@title='Active power B']")
        pc_element = driver.find_element(By.XPATH, "//se-table-item[@title='Active power C']")
        if pf_element and pa_element and pb_element and pc_element:
            # This XPATH finds the `se-table-item` following the one with "Total power factor"
            pf = pf_element.find_element(By.XPATH, "./following-sibling::se-table-item").text.strip()
            pa = pa_element.find_element(By.XPATH, "./following-sibling::se-table-item").text.strip()
            pb = pb_element.find_element(By.XPATH, "./following-sibling::se-table-item").text.strip()
            pc = pc_element.find_element(By.XPATH, "./following-sibling::se-table-item").text.strip()

            logging.info(f"Current readings for this PowerTag: PF={pf}, Pa={pa}, Pb={pb}, Pc={pc}")

            if is_float(pa) and is_float(pf):
                if is_float(pb) and is_float(pc):
                    if float(pa) > 0 and float(pb) > 0 and float(pc) > 0 and float(pf) > 0.5:
                        is_correct = 1
                    elif float(pa) < 0 and float(pb) < 0 and float(pc) < 0 and float(pf) < 0.5:
                        is_correct = -1
                else:
                    if float(pa) > 0 and float(pf) > 0.5:
                        is_correct = 1
                    elif float(pa) < 0 and float(pf) < 0.5:
                        is_correct = -1
            else:
                is_correct = 0

        else:
            logging.warning("Some of values not found.")

    except NoSuchElementException:
        logging.warning("Element containing 'Total power factor' not found, unable to check values.")

    driver.find_element(By.XPATH,
                        '//*[@id="settings-button"]').click()
    return is_correct


def is_float(string: str) -> bool:
    """
    Check if the given string can be converted to float.

    :param string: String to check.
    :return: Boolean information whether the string is a floating point number.
    """
    try:
        float(string)
        return True
    except ValueError:
        return False


def configure_start(url: str, password: str, file_path: str) -> WebDriver:
    """
    Starts webdriver and runs functions to write and read data on the web page.

    :param url: URL of the page to open.
    :param password: Password to log in to the site.
    :param file_path: Path to the CSV file.
    """
    driver = None
    driver = initialize_driver()
    navigate_to_url(driver, url)
    handle_security_warning(driver)
    login_to_site(driver, password)
    search_for_new_powertags(driver)
    configure_powertags(driver, file_path)

    return driver


def main():
    """
    Main function to run the automation script.
    """
    from gui import Application
    file_path = 'data/PowerTags.csv'

    app = Application(file_path)
    app.mainloop()


if __name__ == "__main__":
    main()
