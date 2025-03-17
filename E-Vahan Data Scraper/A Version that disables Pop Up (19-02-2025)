from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import logging
import time
import json
import os
import re
import sys
import requests  # Import requests library for ReadTimeoutError handling

# Configure logging - sets up logging to both a file and the console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vahan_scraper_step6_single_window_debug_load.log'),  # Log file for debugging load issue
        logging.StreamHandler()  # Logs to the console
    ]
)

class VahanScraperStep6: # Class name is now VahanScraperStep6
    """
    Handles the scraping process for Vahan portal data. - STEP 6: Debugging Website Load
    """
    def __init__(self, chrome_binary_path):
        """
        Initializes the scraper with Chrome binary path, download directory, and progress handling.
        Handles resuming from a previous session if available.

        Args:
            chrome_binary_path (str): The path to your Chrome executable.
        """
        self.chrome_binary_path = chrome_binary_path  # Stores the Chrome binary path
        self.driver = None  # Selenium WebDriver instance
        self.wait = None  # WebDriverWait instance for explicit waits
        self.actions = None # ActionChains instance
        self.current_state_index = 0  # Tracks the current state being processed (index in states_ut list)
        self.current_rto_index = 0  # Tracks the current RTO being processed within a state

        # Set base download path - where files will be saved
        self.base_download_path = r"F:\Flipcarbon\Ajax"  # Updated download path
        if not os.path.exists(self.base_download_path):
            os.makedirs(self.base_download_path)  # Creates the directory if it doesn't exist

        # Create date folder dynamically - a folder for each day's downloads
        self.current_date = datetime.now().strftime("%d-%m-%YYYY")  # Gets the current date in DD-MM-YYYY format
        self.date_folder = os.path.join(self.base_download_path, self.current_date)  # Creates a path for the date folder
        os.makedirs(self.date_folder, exist_ok=True)  # Creates the date folder if it doesn't exist

        # Initialize progress handling - load progress from a file or start fresh
        self.progress_file = 'scraping_progress_step6_debug_load.json'  # Progress file for debugging load issue
        self.load_progress()  # Load scraping progress from the progress file
        # self.setup_driver()  # Driver setup is now done per state


    def load_progress(self):
        """
        Initializes scraping progress to the beginning, ignoring any existing progress file.
        This ensures the script always starts from the first state and RTO.
        """
        # Start from scratch, ignoring progress file
        logging.info(f"Starting scraping from beginning. Progress loading from {self.progress_file} is disabled.") # Log fresh start
        self.progress = {
            'current_state_index': 0,  # Start at the first state
            'current_rto_index': 0,  # Start at the first RTO
            'completed_states': {},  # Initializes an empty dictionary to track completed states
        }


    def save_progress(self):
        """
        Saves the current scraping progress to a JSON file. This is called
        periodically to store the current state and RTO indices, allowing the
        script to be resumed later.
        """
        self.progress['current_state_index'] = self.current_state_index  # Saves the current state index
        self.progress['current_rto_index'] = self.current_rto_index  # Saves the current RTO index
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress, f, indent=4) # Added indent for readability in JSON file
            logging.info(f"Progress saved to {self.progress_file} (State Index: {self.current_state_index}, RTO Index: {self.current_rto_index})") # Log save info
        except Exception as e:
            logging.error(f"Error saving progress to {self.progress_file}: {e}") # Log error if saving fails


    def setup_driver(self):
        """
        Initializes the Chrome driver with desired options including disabling pop-ups and notifications, and allowing automatic downloads based on pattern pairs.
        """
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = self.chrome_binary_path  # Specifies Chrome binary path

        # Set download directory and preferences
        prefs = {
            "download.default_directory": self.date_folder,  # Set download directory to date folder
            "download.prompt_for_download": False,  # Auto-download files without prompt
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            'profile.default_content_setting_values.automatic_downloads': 1, # Allow automatic downloads - CORRECT PREFERENCE
            "profile.default_content_settings.popups": 0, # Turn off popups (potentially related to the multiple download warning - trying 0)
            "profile.content_settings.pattern_pairs.*.multiple-automatic-downloads": 1 # Allow multiple automatic downloads for all domains - ROBUST APPROACH
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Re-enable desired options - as requested by the user
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-notifications')
        # --- Profile Options (Comment out if not needed, or configure as required) ---
        # user_data_dir = ...
        # profile_directory = ...
        # chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        # chrome_options.add_argument(f"--profile-directory={profile_directory}")

        try:
            logging.info(f"Attempting to create WebDriver with options: {chrome_options.to_capabilities()}")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            self.actions = ActionChains(self.driver)
            logging.info("Driver setup successful with desired options (allowing automatic downloads with pattern pairs).")
        except Exception as e:
            logging.error(f"Driver setup failed with desired options: {e}")
            self.driver = None
            self.wait = None
            self.actions = None
            raise  # Re-raise the exception to be caught in scrape_data


    def select_primefaces_dropdown(self, dropdown_id, option_text, max_retries=3):
        """
        Selects an option from a PrimeFaces dropdown with retry mechanism.
        PrimeFaces dropdowns are common on the Vahan website, and this function
        automates the selection process, handling potential failures.
        """
        for attempt in range(max_retries):
            try:
                current_value = self.driver.find_element(By.CSS_SELECTOR, f"#{dropdown_id}_label").text.strip()
                if current_value == option_text:
                    logging.info(f"'{option_text}' is already selected in dropdown '{dropdown_id}'")
                    return True

                trigger = self.wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, f"#{dropdown_id} .ui-selectonemenu-trigger")
                ))
                self.driver.execute_script("arguments[0].click();", trigger)
                time.sleep(0.2)

                option_xpath = f"//li[contains(@class, 'ui-selectonemenu-item') and text()='{option_text}']"
                option = self.wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
                self.driver.execute_script("arguments[0].click();", option)
                time.sleep(0.2)

                logging.info(f"Selected '{option_text}' from dropdown '{dropdown_id}'")
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Error selecting '{option_text}' from PrimeFaces dropdown '{dropdown_id}': {str(e)}")
                    return False
                logging.warning(f"Retry {attempt + 1} for dropdown '{dropdown_id}'")
                time.sleep(0.2)

    def initialize_filters(self):
        """
        Initializes the dropdown filters on the Vahan portal.
        This function sets the initial filter values for the data selection.
        """
        try:
            if not self.select_primefaces_dropdown('xaxisVar', 'Month Wise'):
                raise Exception("Failed to set X-axis to Month Wise")
            time.sleep(0.2)

            if not self.select_primefaces_dropdown('yaxisVar', 'Maker'): # Changed to Vehicle Class as per comment
                raise Exception("Failed to set Y-axis to Vehicle Class") # Changed to Vehicle Class as per comment
            time.sleep(0.2)

            if not self.select_primefaces_dropdown('selectedYear', '2025'):
                raise Exception("Failed to set Year to 2025")
            time.sleep(0.2)

            return True
        except Exception as e:
            logging.error(f"Error initializing filters: {str(e)}")
            return False

    def sanitize_filename(self, filename):
        """Sanitizes a filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = re.sub(r'\s*\([^)]*\)', '', filename)
        filename = ' '.join(filename.split())
        return filename.strip()


    def wait_for_download_complete(self, timeout=30):
        """Waits for download to complete."""
        start_time = time.time()
        while True:
            if not any(f.endswith('.crdownload') for f in os.listdir(self.date_folder)):
                break
            if time.time() - start_time > timeout:
                raise Exception("Download timed out")
            time.sleep(0.2)


    def move_file_to_state_folder(self, rto_name, state):
        """Moves downloaded file to state folder."""
        try:
            self.wait_for_download_complete()

            files = [f for f in os.listdir(self.date_folder) if f.endswith('.xlsx')]
            if not files:
                raise FileNotFoundError("No Excel files found in download directory")

            latest_file = max(
                [os.path.join(self.date_folder, f) for f in files],
                key=os.path.getmtime
            )

            sanitized_state = self.sanitize_filename(state)
            state_folder = os.path.join(self.date_folder, sanitized_state)
            os.makedirs(state_folder, exist_ok=True)

            sanitized_rto = self.sanitize_filename(rto_name)
            new_filename = f"{sanitized_rto}.xlsx"
            new_filepath = os.path.join(state_folder, new_filename)

            counter = 1
            while os.path.exists(new_filepath):
                new_filename = f"{sanitized_rto}_{counter}.xlsx"
                new_filepath = os.path.join(state_folder, new_filename)
                counter += 1

            os.rename(latest_file, new_filepath)
            logging.info(f"Successfully moved file to: {new_filepath}")
            return True

        except Exception as e:
            logging.error(f"Error in move_file_to_state_folder: {str(e)}")
            return False


    def process_state(self, state):
        """Processes a single state."""
        success = False
        try:
            if not self.select_primefaces_dropdown('j_idt36', state): # Updated state dropdown ID to 'j_idt36'
                raise Exception(f"Failed to select state: {state}")
            time.sleep(0.4)

            rto_dropdown_id = 'selectedRto'
            trigger = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"#{rto_dropdown_id} .ui-selectonemenu-trigger")
            ))
            self.driver.execute_script("arguments[0].click();", trigger)
            time.sleep(0.2)

            rto_options = self.driver.find_elements(By.CSS_SELECTOR, f"#{rto_dropdown_id}_items .ui-selectonemenu-item")

            for i in range(self.current_rto_index, len(rto_options)):
                rto_option = rto_options[i]
                rto_text = rto_option.text

                if "All Vahan4 Running Office" in rto_text:
                    logging.info(f"Skipping RTO: {rto_text}")
                    continue

                try:
                    self.driver.execute_script("arguments[0].click();", rto_option)
                    time.sleep(0.2)

                    refresh_button = self.wait.until(EC.presence_of_element_located((By.ID, 'j_idt67'))) # Updated refresh button ID to 'j_idt67'
                    self.driver.execute_script("arguments[0].click();", refresh_button)
                    time.sleep(0.4)

                    download_button = self.wait.until(EC.presence_of_element_located(
                        (By.ID, 'groupingTable:j_idt82') # Updated download button ID to 'groupingTable:j_idt82'
                    ))
                    self.driver.execute_script("arguments[0].click();", download_button)
                    time.sleep(0.4)

                    if not self.move_file_to_state_folder(rto_text, state):
                        raise Exception("Failed to move downloaded file")

                    self.current_rto_index = i + 1
                    self.save_progress()
                    logging.info(f"Successfully processed RTO: {rto_text} in state: {state}")

                except Exception as e:
                    logging.error(f"Error processing RTO {rto_text}: {str(e)}")
                    continue

            success = True
            return success

        except Exception as e:
            logging.error(f"Error processing state {state}: {str(e)}")
            return success


    def scrape_data(self):
        """
        Main scraping method - **MODIFIED to use driver per state.**
        """
        states_ut = [ # ... (your states_ut list - no change) ... ]
            'Andaman & Nicobar Island(3)',
            'Andhra Pradesh(83)',
            'Arunachal Pradesh(29)',
            'Assam(33)',
            'Bihar(48)',
            'Chhattisgarh(30)',
            'Chandigarh(1)',
            'UT of DNH and DD(3)',
            'Delhi(16)',
            'Goa(13)',
            'Gujarat(37)',
            'Himachal Pradesh(96)',
            'Haryana(98)',
            'Jharkhand(25)',
            'Jammu and Kashmir(21)',
            'Karnataka(68)',
            'Kerala(87)',
            'Ladakh(3)',
            'Lakshadweep(5)',
            'Maharashtra(56)',
            'Meghalaya(13)',
            'Manipur(13)',
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

        try: # Add a try block to catch errors during the entire scraping process
            while self.current_state_index < len(states_ut):
                state = states_ut[self.current_state_index]
                try:
                    self.setup_driver() # Setup driver at the beginning of each state processing
                    if not self.driver: # Check if driver setup was successful
                        raise Exception("Driver setup failed")

                    self.driver.get('https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml')
                    time.sleep(0.4)

                    if not self.initialize_filters():
                        raise Exception("Failed to initialize filters")


                    if self.process_state(state):
                        self.progress['completed_states'][state] = True
                        self.current_state_index += 1
                        self.current_rto_index = 0
                        self.save_progress()
                        logging.info(f"Successfully completed state: {state}")
                    else:
                        raise Exception(f"Failed to process state: {state}")

                except Exception as e:
                    logging.error(f"Session error for state {state}: {str(e)}") # More specific error log

                    retry_count = self.progress.get(f'retry_count_{self.current_state_index}', 0) + 1
                    self.progress[f'retry_count_{self.current_state_index}'] = retry_count

                    if retry_count >= max_retries:
                        logging.error(f"Skipping state {states_ut[self.current_state_index]} after {max_retries} failures")
                        self.current_state_index += 1
                        self.current_rto_index = 0
                    else:
                        logging.info(f"Waiting {retry_delay} seconds before retrying state {state}...")
                        time.sleep(retry_delay)
                    self.save_progress()


                finally: # Finally block to ensure driver quit after each state
                    if self.driver:
                        try:
                            self.driver.quit() # Quit driver after each state processing
                            self.driver = None # Reset driver to None
                            logging.info(f"Driver quit after processing state: {state} (or error).")
                        except Exception as quit_err:
                            logging.warning(f"Error during driver quit after state {state}: {quit_err}")


        except Exception as main_scrape_error: # Catch errors for the whole scraping process
            logging.critical(f"Fatal error during main scraping loop: {main_scrape_error}")

        logging.info("Scraping completed!")

if __name__ == "__main__":
    try:
        chrome_path = r"C:/Program Files (x86)/chrome-win64/chrome.exe"
        if not os.path.exists(chrome_path):
            raise FileNotFoundError(f"Chrome binary not found at: {chrome_path}")

        scraper = VahanScraperStep6(chrome_path)
        scraper.scrape_data()
    except Exception as e:
        logging.critical(f"Fatal error: {str(e)}")
        sys.exit(1)
