from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import logging
import time
import json
import os
import re
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vahan_scraper.log'),
        logging.StreamHandler()
    ]
)

class VahanScraper:
    """
    Enhanced Vahan portal scraper that dynamically detects PrimeFaces j_idt values
    and processes data for all states and RTOs.
    """
    def __init__(self, chrome_binary_path, download_path=None):
        """
        Initialize the scraper with Chrome binary path and download directory.

        Args:
            chrome_binary_path (str): Path to Chrome executable
            download_path (str, optional): Base path for downloads. Defaults to F:/Flipcarbon/Ajax
        """
        self.chrome_binary_path = chrome_binary_path
        self.driver = None
        self.wait = None
        self.actions = None
        self.current_state_index = 0
        self.current_rto_index = 0

        # Dynamic j_idt labels - initialized as None
        self.j_idt_labels = {
            'state_dropdown_j_idt': None,
            'refresh_button_j_idt': None,
            'excel_img_j_idt': None
        }

        # Set base download path
        self.base_download_path = download_path or r"F:\Flipcarbon\Ajax"
        if not os.path.exists(self.base_download_path):
            os.makedirs(self.base_download_path)

        # Create date folder dynamically
        self.current_date = datetime.now().strftime("%d-%m-%Y")
        self.date_folder = os.path.join(self.base_download_path, self.current_date)
        os.makedirs(self.date_folder, exist_ok=True)

        # Progress tracking
        self.progress_file = 'vahan_scraping_progress.json'
        self.load_progress()

    def load_progress(self):
        """Initialize new scraping progress, ignoring any existing progress file."""
        self.progress = {
            'current_state_index': 0,
            'current_rto_index': 0,
            'completed_states': {},
            'j_idt_labels': {}
        }
        logging.info("Starting fresh scraping progress (ignoring progress file)")


    def save_progress(self):
        """Save current scraping progress to JSON file."""
        self.progress['current_state_index'] = self.current_state_index
        self.progress['current_rto_index'] = self.current_rto_index
        self.progress['j_idt_labels'] = self.j_idt_labels

        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress, f, indent=4)
            logging.info(f"Progress saved to {self.progress_file}")
        except Exception as e:
            logging.error(f"Error saving progress: {e}")

    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            chrome_options.binary_location = self.chrome_binary_path

            # Set download directory and preferences
            prefs = {
                "download.default_directory": self.date_folder,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                'profile.default_content_setting_values.automatic_downloads': 1,
                "profile.default_content_settings.popups": 0,
                "profile.content_settings.pattern_pairs.*.multiple-automatic-downloads": 1
            }
            chrome_options.add_experimental_option("prefs", prefs)

            # Add additional options
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-notifications")

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            self.actions = ActionChains(self.driver)
            logging.info("Chrome WebDriver set up successfully")
            return True
        except Exception as e:
            logging.error(f"Error setting up Chrome WebDriver: {e}")
            return False

    def extract_j_idt_from_id(self, id_value):
        """Extract j_idt pattern from an ID attribute."""
        if not id_value:
            return None
        match = re.search(r'j_idt\d+', id_value)
        if match:
            return match.group(0)
        return None

    def detect_j_idt_labels(self):
        """
        Detects j_idt labels dynamically from the Vahan dashboard.
        This function runs once before processing states and RTOs.
        """
        try:
            # Navigate to the website
            logging.info("Navigating to Vahan dashboard")
            self.driver.get("https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml")

            # Wait for page to load
            time.sleep(3)

            # Initialize filters
            self.initialize_filters()

            # Detect state dropdown
            logging.info("Detecting state dropdown j_idt...")
            state_dropdowns = self.driver.find_elements(By.XPATH, "//label[contains(@id, 'j_idt') and contains(@class, 'ui-selectonemenu-label') and contains(text(), 'All Vahan4 Running States')]")
            if state_dropdowns:
                state_dropdown_id = state_dropdowns[0].get_attribute("id")
                state_dropdown_j_idt = self.extract_j_idt_from_id(state_dropdown_id)
                self.j_idt_labels['state_dropdown_j_idt'] = state_dropdown_j_idt
                logging.info(f"Found state dropdown j_idt: {state_dropdown_j_idt}")
            else:
                # Fallback: look for select elements
                selects = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'ui-selectonemenu')]")
                if len(selects) >= 3:
                    state_dropdown_id = selects[2].get_attribute("id")
                    state_dropdown_j_idt = self.extract_j_idt_from_id(state_dropdown_id)
                    self.j_idt_labels['state_dropdown_j_idt'] = state_dropdown_j_idt
                    logging.info(f"Found state dropdown j_idt by position: {state_dropdown_j_idt}")
                else:
                    logging.warning("Could not detect state dropdown j_idt")

            # Detect refresh button
            logging.info("Detecting refresh button j_idt...")
            refresh_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@id, 'j_idt') and .//span[text()='Refresh']]")
            if refresh_buttons:
                refresh_button_id = refresh_buttons[0].get_attribute("id")
                refresh_button_j_idt = self.extract_j_idt_from_id(refresh_button_id)
                self.j_idt_labels['refresh_button_j_idt'] = refresh_button_j_idt
                logging.info(f"Found refresh button j_idt: {refresh_button_j_idt}")
            else:
                # Fallback: look for refresh icon
                refresh_icons = self.driver.find_elements(By.XPATH, "//button[contains(@id, 'j_idt')]/span[contains(@class, 'ui-icon-refresh')]/..")
                if refresh_icons:
                    refresh_button_id = refresh_icons[0].get_attribute("id")
                    refresh_button_j_idt = self.extract_j_idt_from_id(refresh_button_id)
                    self.j_idt_labels['refresh_button_j_idt'] = refresh_button_j_idt
                    logging.info(f"Found refresh button j_idt by icon: {refresh_button_j_idt}")
                else:
                    logging.warning("Could not detect refresh button j_idt")

            # Detect Excel export button
            logging.info("Detecting Excel export button j_idt...")
            try:
                excel_img = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//img[contains(@id, 'groupingTable:j_idt')]"))
                )
                excel_img_id = excel_img.get_attribute("id")
                self.j_idt_labels['excel_img_j_idt'] = excel_img_id
                logging.info(f"Found Excel export button id: {excel_img_id}")
            except Exception as e:
                logging.warning(f"Could not find Excel export button with specific pattern: {e}")

                # Fallback: look for any images with j_idt in their ID
                excel_imgs = self.driver.find_elements(By.XPATH, "//img[contains(@id, 'j_idt') and (contains(@src, 'csv.png') or contains(@title, 'Excel') or contains(@title, 'EXCEL'))]")
                if excel_imgs:
                    excel_img_id = excel_imgs[0].get_attribute("id")
                    self.j_idt_labels['excel_img_j_idt'] = excel_img_id
                    logging.info(f"Found Excel export button id by attributes: {excel_img_id}")
                else:
                    # Fallback: scan all images
                    all_imgs = self.driver.find_elements(By.TAG_NAME, "img")
                    for img in all_imgs:
                        try:
                            img_id = img.get_attribute("id")
                            img_src = img.get_attribute("src") or ""
                            img_title = img.get_attribute("title") or ""

                            if img_id and "j_idt" in img_id:
                                if "csv" in img_src.lower() or "excel" in img_src.lower() or "excel" in img_title.lower() or "csv" in img_title.lower() or "download" in img_title.lower():
                                    self.j_idt_labels['excel_img_j_idt'] = img_id
                                    logging.info(f"Found Excel export button id by scanning all images: {img_id}")
                                    break
                        except Exception as e:
                            logging.error(f"Error processing an image: {e}")

            # Save the detected labels to progress file
            self.save_progress()

            # Take screenshots and save page source for debugging
            self.driver.save_screenshot("vahan_dashboard.png")
            with open("vahan_page_source.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)

            logging.info("j_idt labels detection completed")
            return True

        except Exception as e:
            logging.error(f"Error detecting j_idt labels: {e}")
            return False

    def select_year(self, year="2024"):
        """Select specific year from the year dropdown."""
        try:
            logging.info(f"Selecting year: {year}")

            # Find and click the year dropdown
            year_dropdown_id = 'selectedYear'
            trigger = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"#{year_dropdown_id} .ui-selectonemenu-trigger")
            ))
            self.driver.execute_script("arguments[0].click();", trigger)
            time.sleep(0.5)

            # Select the specific year
            option_xpath = f"//li[contains(@class, 'ui-selectonemenu-item') and text()='{year}']"
            option = self.wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
            self.driver.execute_script("arguments[0].click();", option)
            time.sleep(0.5)

            logging.info(f"Successfully selected year: {year}")
            return True
        except Exception as e:
            logging.error(f"Error selecting year {year}: {e}")
            return False

    def initialize_filters(self):
        """Initialize the dropdown filters on the Vahan dashboard."""
        try:
            # Select Year 2024
            self.select_year("2023")
            time.sleep(0.5)

            # Select Month Wise for X-axis
            logging.info("Setting X-axis to Month Wise")
            self.select_primefaces_dropdown('xaxisVar', 'Month Wise')
            time.sleep(0.5)

            # Select Maker for Y-axis
            logging.info("Setting Y-axis to Maker")
            self.select_primefaces_dropdown('yaxisVar', 'Maker')
            time.sleep(0.5)

            # Click refresh button
            logging.info("Clicking refresh button")
            refresh_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@id, 'j_idt') and .//span[text()='Refresh']]")
            if refresh_buttons:
                self.driver.execute_script("arguments[0].click();", refresh_buttons[0])
                time.sleep(3)

            return True
        except Exception as e:
            logging.error(f"Error initializing filters: {e}")
            return False

    def select_primefaces_dropdown(self, dropdown_id, option_text, max_retries=3):
        """Select an option from a PrimeFaces dropdown."""
        for attempt in range(max_retries):
            try:
                # Check if the option is already selected
                current_value = self.driver.find_element(By.CSS_SELECTOR, f"#{dropdown_id}_label").text.strip()
                if current_value == option_text:
                    logging.info(f"'{option_text}' is already selected in dropdown '{dropdown_id}'")
                    return True

                # Click the dropdown trigger
                trigger = self.wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, f"#{dropdown_id} .ui-selectonemenu-trigger")
                ))
                self.driver.execute_script("arguments[0].click();", trigger)
                time.sleep(0.5)

                # Select the option
                option_xpath = f"//li[contains(@class, 'ui-selectonemenu-item') and text()='{option_text}']"
                option = self.wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
                self.driver.execute_script("arguments[0].click();", option)
                time.sleep(0.5)

                logging.info(f"Selected '{option_text}' from dropdown '{dropdown_id}'")
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Error selecting '{option_text}' from dropdown '{dropdown_id}': {e}")
                    return False
                logging.warning(f"Retry {attempt + 1} for dropdown '{dropdown_id}'")
                time.sleep(1)

    def sanitize_filename(self, filename):
        """Sanitize a filename by removing invalid characters."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = re.sub(r'\s*\([^)]*\)', '', filename)
        filename = ' '.join(filename.split())
        return filename.strip()

    def wait_for_download_complete(self, timeout=60):
        """Wait for download to complete."""
        start_time = time.time()
        while True:
            if not any(f.endswith('.crdownload') for f in os.listdir(self.date_folder)):
                break
            if time.time() - start_time > timeout:
                raise TimeoutException("Download timed out")
            time.sleep(1)

    def move_file_to_state_folder(self, rto_name, state):
        """Move downloaded file to state folder."""
        try:
            self.wait_for_download_complete()

            # Find the latest downloaded Excel file
            files = [f for f in os.listdir(self.date_folder) if f.endswith('.xlsx')]
            if not files:
                raise FileNotFoundError("No Excel files found in download directory")

            latest_file = max(
                [os.path.join(self.date_folder, f) for f in files],
                key=os.path.getmtime
            )

            # Create state folder if it doesn't exist
            sanitized_state = self.sanitize_filename(state)
            state_folder = os.path.join(self.date_folder, sanitized_state)
            os.makedirs(state_folder, exist_ok=True)

            # Create new filename and filepath
            sanitized_rto = self.sanitize_filename(rto_name)
            new_filename = f"{sanitized_rto}.xlsx"
            new_filepath = os.path.join(state_folder, new_filename)

            # Handle filename conflicts
            counter = 1
            while os.path.exists(new_filepath):
                new_filename = f"{sanitized_rto}_{counter}.xlsx"
                new_filepath = os.path.join(state_folder, new_filename)
                counter += 1

            # Move the file
            os.rename(latest_file, new_filepath)
            logging.info(f"Successfully moved file to: {new_filepath}")
            return True
        except Exception as e:
            logging.error(f"Error moving file: {e}")
            return False

    def process_state(self, state):
        """Process a single state and its RTOs."""
        success = False
        state_dropdown_j_idt = self.j_idt_labels.get('state_dropdown_j_idt')
        refresh_button_j_idt = self.j_idt_labels.get('refresh_button_j_idt')
        excel_img_j_idt = self.j_idt_labels.get('excel_img_j_idt')

        if not state_dropdown_j_idt or not refresh_button_j_idt or not excel_img_j_idt:
            logging.error("Missing required j_idt labels. Cannot process state.")
            return False

        try:
            # Select the state from dropdown
            logging.info(f"Processing state: {state}")
            if not self.select_primefaces_dropdown(state_dropdown_j_idt, state):
                raise Exception(f"Failed to select state: {state}")
            time.sleep(1)

            # Get all RTOs for the state
            rto_dropdown_id = 'selectedRto'
            trigger = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"#{rto_dropdown_id} .ui-selectonemenu-trigger")
            ))
            self.driver.execute_script("arguments[0].click();", trigger)
            time.sleep(0.5)

            rto_options = self.driver.find_elements(By.CSS_SELECTOR, f"#{rto_dropdown_id}_items .ui-selectonemenu-item")
            logging.info(f"Found {len(rto_options)} RTOs for state: {state}")

            # Process each RTO
            for i in range(self.current_rto_index, len(rto_options)):
                rto_option = rto_options[i]
                rto_text = rto_option.text

                # Skip "All Vahan4 Running Office"
                if "All Vahan4 Running Office" in rto_text:
                    logging.info(f"Skipping RTO: {rto_text}")
                    continue

                try:
                    logging.info(f"Processing RTO: {rto_text}")
                    self.driver.execute_script("arguments[0].click();", rto_option)
                    time.sleep(0.5)

                    # Click refresh button
                    refresh_button = self.wait.until(EC.presence_of_element_located((By.ID, refresh_button_j_idt)))
                    self.driver.execute_script("arguments[0].click();", refresh_button)
                    time.sleep(2)

                    # Click Excel export button
                    download_button = self.wait.until(EC.presence_of_element_located((By.ID, excel_img_j_idt)))
                    self.driver.execute_script("arguments[0].click();", download_button)
                    time.sleep(2)

                    # Move the downloaded file to the state folder
                    if not self.move_file_to_state_folder(rto_text, state):
                        raise Exception("Failed to move downloaded file")

                    # Update progress
                    self.current_rto_index = i + 1
                    self.save_progress()
                    logging.info(f"Successfully processed RTO: {rto_text} in state: {state}")

                except Exception as e:
                    logging.error(f"Error processing RTO {rto_text}: {e}")
                    continue

            success = True
            return success
        except Exception as e:
            logging.error(f"Error processing state {state}: {e}")
            return success

    def scrape_data(self):
        """Main scraping method."""
        states_ut = [
            'Madhya Pradesh(53)',
            'Mizoram(10)',
            'Nagaland(9)',
            'Odisha(39)',
            'Punjab(96)',
            'Puducherry(8)',
            'Rajasthan(59)',
            'Sikkim(9)',
            'Tamil Nadu(148)',
            'Tripura(9)',
            'Uttarakhand(21)',
            'Uttar Pradesh(77)',
            'West Bengal(57)'
        ]

        max_retries = 3
        retry_delay = 60

        try:
            # Set up Chrome driver
            if not self.setup_driver():
                raise Exception("Failed to set up Chrome driver")

            # Check if we have already detected j_idt labels
            if not all(self.j_idt_labels.values()):
                # Load from progress file if available
                if self.progress.get('j_idt_labels') and all(self.progress['j_idt_labels'].values()):
                    self.j_idt_labels = self.progress['j_idt_labels']
                    logging.info(f"Loaded j_idt labels from progress file: {self.j_idt_labels}")
                else:
                    # Detect j_idt labels dynamically
                    if not self.detect_j_idt_labels():
                        raise Exception("Failed to detect j_idt labels")

            # Process each state
            while self.current_state_index < len(states_ut):
                state = states_ut[self.current_state_index]
                try:
                    # Navigate to the website
                    self.driver.get('https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml')
                    time.sleep(2)

                    # Initialize filters
                    if not self.initialize_filters():
                        raise Exception("Failed to initialize filters")

                    # Process the state
                    if self.process_state(state):
                        self.progress['completed_states'][state] = True
                        self.current_state_index += 1
                        self.current_rto_index = 0
                        self.save_progress()
                        logging.info(f"Successfully completed state: {state}")
                    else:
                        raise Exception(f"Failed to process state: {state}")

                except Exception as e:
                    logging.error(f"Error processing state {state}: {e}")

                    # Retry or skip state
                    retry_count = self.progress.get(f'retry_count_{self.current_state_index}', 0) + 1
                    self.progress[f'retry_count_{self.current_state_index}'] = retry_count

                    if retry_count >= max_retries:
                        logging.error(f"Skipping state {state} after {max_retries} failures")
                        self.current_state_index += 1
                        self.current_rto_index = 0
                    else:
                        logging.info(f"Waiting {retry_delay} seconds before retrying state {state}")
                        time.sleep(retry_delay)

                    self.save_progress()

            logging.info("All states processed successfully")
        except Exception as e:
            logging.critical(f"Fatal error: {e}")
        finally:
            # Close the browser
            if self.driver:
                self.driver.quit()
                logging.info("Browser closed")

def main():
    """Main function to run the scraper."""
    try:
        chrome_path = r"C:/Program Files (x86)/chrome-win64/chrome.exe"
        if not os.path.exists(chrome_path):
            raise FileNotFoundError(f"Chrome binary not found at: {chrome_path}")

        # Create and run the scraper
        scraper = VahanScraper(chrome_path)
        scraper.scrape_data()

    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
