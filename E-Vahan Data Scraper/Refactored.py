from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Union, Any


class VahanScraperConfig:
    """Configuration class for Vahan scraper settings."""

    def __init__(self,
                 chrome_binary_path: str,
                 download_path: str = None,
                 wait_timeout: int = 30,
                 download_timeout: int = 60,
                 max_retries: int = 3,
                 retry_delay: int = 60,
                 year: str = None):
        """
        Initialize configuration with customizable parameters.

        Args:
            chrome_binary_path: Path to Chrome executable
            download_path: Base path for downloads
            wait_timeout: Timeout for WebDriverWait operations in seconds
            download_timeout: Timeout for download operations in seconds
            max_retries: Maximum number of retries for operations
            retry_delay: Delay between retries in seconds
            year: Year to select in Vahan dashboard
        """
        self.chrome_binary_path = chrome_binary_path
        self.download_path = download_path or os.path.join(os.path.expanduser("~"), "Downloads", "VahanData")
        self.wait_timeout = wait_timeout
        self.download_timeout = download_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.year = str(datetime.now().year) if year is None else year

        # Set up logging
        self.setup_logging()

        # Create base download directory
        os.makedirs(self.download_path, exist_ok=True)

    def setup_logging(self):
        """Configure logging for the application."""
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"vahan_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        logging.info(f"Logging initialized, output to {log_file}")


class VahanScraper:
    """
    Enhanced Vahan portal scraper that dynamically detects PrimeFaces j_idt values
    and processes data for all states and RTOs.
    """

    def __init__(self, config: VahanScraperConfig):
        """
        Initialize the scraper with configuration.

        Args:
            config: VahanScraperConfig object with scraper settings
        """
        self.config = config
        self.driver = None
        self.wait = None
        self.actions = None

        # Dynamic j_idt labels - initialized as None
        self.j_idt_labels = {
            'state_dropdown_j_idt': None,
            'refresh_button_j_idt': None,
            'excel_img_j_idt': None
        }

        # Create date folder dynamically
        self.current_date = datetime.now().strftime("%d-%m-%Y")
        self.date_folder = os.path.join(self.config.download_path, self.current_date)
        os.makedirs(self.date_folder, exist_ok=True)

        # Progress tracking
        self.progress_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vahan_scraping_progress.json')
        self.progress = self._init_progress()

        # State and RTO tracking
        self.current_state_index = self.progress.get('current_state_index', 0)
        self.current_rto_index = self.progress.get('current_rto_index', 0)

        # List of all states and UTs
        self.states_ut = [
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

    def _init_progress(self) -> Dict[str, Any]:
        """Initialize new scraping progress or load existing progress."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    logging.info(f"Loaded existing progress from {self.progress_file}")

                    # Restore j_idt labels if available
                    if progress.get('j_idt_labels'):
                        self.j_idt_labels = progress['j_idt_labels']
                        logging.info(f"Restored j_idt labels: {self.j_idt_labels}")

                    return progress
            except Exception as e:
                logging.error(f"Error loading progress file: {e}")

        # Initialize new progress
        logging.info("Starting fresh scraping progress")
        return {
            'current_state_index': 0,
            'current_rto_index': 0,
            'completed_states': {},
            'j_idt_labels': {}
        }

    def save_progress(self) -> None:
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

    def setup_driver(self) -> bool:
        """Set up Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            chrome_options.binary_location = self.config.chrome_binary_path

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
            self.wait = WebDriverWait(self.driver, self.config.wait_timeout)
            self.actions = ActionChains(self.driver)
            logging.info("Chrome WebDriver set up successfully")
            return True
        except Exception as e:
            logging.error(f"Error setting up Chrome WebDriver: {e}")
            return False

    def _extract_j_idt_from_id(self, id_value: str) -> Optional[str]:
        """Extract j_idt pattern from an ID attribute."""
        if not id_value:
            return None
        match = re.search(r'j_idt\d+', id_value)
        if match:
            return match.group(0)
        return None

    def detect_j_idt_labels(self) -> bool:
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
                state_dropdown_j_idt = self._extract_j_idt_from_id(state_dropdown_id)
                self.j_idt_labels['state_dropdown_j_idt'] = state_dropdown_j_idt
                logging.info(f"Found state dropdown j_idt: {state_dropdown_j_idt}")
            else:
                # Fallback: look for select elements
                selects = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'ui-selectonemenu')]")
                if len(selects) >= 3:
                    state_dropdown_id = selects[2].get_attribute("id")
                    state_dropdown_j_idt = self._extract_j_idt_from_id(state_dropdown_id)
                    self.j_idt_labels['state_dropdown_j_idt'] = state_dropdown_j_idt
                    logging.info(f"Found state dropdown j_idt by position: {state_dropdown_j_idt}")
                else:
                    logging.warning("Could not detect state dropdown j_idt")

            # Detect refresh button
            logging.info("Detecting refresh button j_idt...")
            refresh_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@id, 'j_idt') and .//span[text()='Refresh']]")
            if refresh_buttons:
                refresh_button_id = refresh_buttons[0].get_attribute("id")
                refresh_button_j_idt = self._extract_j_idt_from_id(refresh_button_id)
                self.j_idt_labels['refresh_button_j_idt'] = refresh_button_j_idt
                logging.info(f"Found refresh button j_idt: {refresh_button_j_idt}")
            else:
                # Fallback: look for refresh icon
                refresh_icons = self.driver.find_elements(By.XPATH, "//button[contains(@id, 'j_idt')]/span[contains(@class, 'ui-icon-refresh')]/..")
                if refresh_icons:
                    refresh_button_id = refresh_icons[0].get_attribute("id")
                    refresh_button_j_idt = self._extract_j_idt_from_id(refresh_button_id)
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

                # Try alternate methods
                self._find_excel_export_button_alternatives()

            # Save the detected labels to progress file
            self.save_progress()

            # Debug information
            self._save_debug_information()

            logging.info("j_idt labels detection completed")
            return all(self.j_idt_labels.values())  # Return success only if all labels were found

        except Exception as e:
            logging.error(f"Error detecting j_idt labels: {e}")
            return False

    def _find_excel_export_button_alternatives(self) -> None:
        """Find Excel export button using alternative methods."""
        # Fallback: look for any images with j_idt in their ID
        excel_imgs = self.driver.find_elements(By.XPATH, "//img[contains(@id, 'j_idt') and (contains(@src, 'csv.png') or contains(@title, 'Excel') or contains(@title, 'EXCEL'))]")
        if excel_imgs:
            excel_img_id = excel_imgs[0].get_attribute("id")
            self.j_idt_labels['excel_img_j_idt'] = excel_img_id
            logging.info(f"Found Excel export button id by attributes: {excel_img_id}")
            return

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
                        return
            except Exception as e:
                logging.error(f"Error processing an image: {e}")

    def _save_debug_information(self) -> None:
        """Save screenshot and page source for debugging."""
        debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug")
        os.makedirs(debug_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(debug_dir, f"vahan_dashboard_{timestamp}.png")
        source_path = os.path.join(debug_dir, f"vahan_page_source_{timestamp}.html")

        try:
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Saved screenshot to {screenshot_path}")

            with open(source_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logging.info(f"Saved page source to {source_path}")
        except Exception as e:
            logging.error(f"Error saving debug information: {e}")

    def select_year(self, year: str = None) -> bool:
        """Select specific year from the year dropdown."""
        year = year or self.config.year
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

    def initialize_filters(self) -> bool:
        """Initialize the dropdown filters on the Vahan dashboard."""
        try:
            # Select Year
            self.select_year()
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

    def select_primefaces_dropdown(self, dropdown_id: str, option_text: str, max_retries: int = None) -> bool:
        """Select an option from a PrimeFaces dropdown."""
        max_retries = max_retries or self.config.max_retries

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

        return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename by removing invalid characters."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = re.sub(r'\s*\([^)]*\)', '', filename)
        filename = ' '.join(filename.split())
        return filename.strip()

    def wait_for_download_complete(self, timeout: int = None) -> bool:
        """Wait for download to complete."""
        timeout = timeout or self.config.download_timeout

        try:
            start_time = time.time()
            while True:
                if not any(f.endswith('.crdownload') for f in os.listdir(self.date_folder)):
                    time.sleep(1)  # Wait a bit more to ensure file is fully processed
                    return True

                if time.time() - start_time > timeout:
                    raise TimeoutException(f"Download timed out after {timeout} seconds")
                time.sleep(1)
        except Exception as e:
            logging.error(f"Error waiting for download: {e}")
            return False

    def move_file_to_state_folder(self, rto_name: str, state: str) -> bool:
        """Move downloaded file to state folder."""
        try:
            if not self.wait_for_download_complete():
                raise TimeoutException("Download timed out or failed")

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

    def process_rto(self, rto_option, rto_text: str, state: str) -> bool:
        """Process a single RTO within a state."""
        try:
            logging.info(f"Processing RTO: {rto_text}")

            # Click on the RTO option
            self.driver.execute_script("arguments[0].click();", rto_option)
            time.sleep(0.5)

            # Click refresh button
            refresh_button_j_idt = self.j_idt_labels.get('refresh_button_j_idt')
            refresh_button = self.wait.until(EC.presence_of_element_located((By.ID, refresh_button_j_idt)))
            self.driver.execute_script("arguments[0].click();", refresh_button)
            time.sleep(2)

            # Click Excel export button
            excel_img_j_idt = self.j_idt_labels.get('excel_img_j_idt')
            download_button = self.wait.until(EC.presence_of_element_located((By.ID, excel_img_j_idt)))
            self.driver.execute_script("arguments[0].click();", download_button)
            time.sleep(2)

            # Move the downloaded file to the state folder
            if not self.move_file_to_state_folder(rto_text, state):
                raise Exception(f"Failed to move downloaded file for RTO: {rto_text}")

            logging.info(f"Successfully processed RTO: {rto_text}")
            return True

        except Exception as e:
            logging.error(f"Error processing RTO {rto_text}: {e}")
            return False

    def process_state(self, state: str) -> bool:
        """Process a single state and its RTOs."""
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
            success_count = 0
            for i in range(self.current_rto_index, len(rto_options)):
                rto_option = rto_options[i]
                rto_text = rto_option.text

                # Skip "All Vahan4 Running Office"
                if "All Vahan4 Running Office" in rto_text:
                    logging.info(f"Skipping RTO: {rto_text}")
                    continue

                # Process the RTO
                if self.process_rto(rto_option, rto_text, state):
                    success_count += 1

                # Update progress after each RTO
                self.current_rto_index = i + 1
                self.save_progress()

                # Reopen the RTO dropdown for next iteration (if not the last one)
                if i < len(rto_options) - 1:
                    trigger = self.wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, f"#{rto_dropdown_id} .ui-selectonemenu-trigger")
                    ))
                    self.driver.execute_script("arguments[0].click();", trigger)
                    time.sleep(0.5)

                    # Re-fetch the options if they might have changed
                    rto_options = self.driver.find_elements(By.CSS_SELECTOR, f"#{rto_dropdown_id}_items .ui-selectonemenu-item")

            # Record state as completed if any RTOs were processed successfully
            if success_count > 0:
                self.progress['completed_states'][state] = True
                self.save_progress()
                logging.info(f"Successfully processed {success_count} RTOs in state: {state}")
                return True
            else:
                logging.warning(f"No RTOs were successfully processed in state: {state}")
                return False

        except Exception as e:
            logging.error(f"Error processing state {state}: {e}")
            return False

    def scrape_data(self) -> None:
        """Main scraping method."""
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
            while self.current_state_index < len(self.states_ut):
                state = self.states_ut[self.current_state_index]

                # Skip already completed states unless forced to reprocess
                if state in self.progress.get('completed_states', {}) and self.progress['completed_states'][state]:
                    logging.info(f"Skipping already completed state: {state}")
                    self.current_state_index += 1
                    self.current_rto_index = 0
                    continue

                # Process the state with retry logic
                state_processed = self._process_state_with_retry(state)

                # Move to next state if successful or max retries exceeded
                if state_processed:
                    self.current_state_index += 1
                    self.current_rto_index = 0
                    self.save_progress()

            logging.info("All states processed successfully")

        except Exception as e:
            logging.critical(f"Fatal error: {e}")
        finally:
            # Clean up
            self._cleanup()

    def _process_state_with_retry(self, state: str) -> bool:
        """Process a state with retry logic."""
        retry_key = f'retry_count_{self.current_state_index}'
        retry_count = self.progress.get(retry_key, 0)

        for attempt in range(retry_count, self.config.max_retries):
            try:
                # Navigate to the website
                self.driver.get('https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml')
                time.sleep(2)

                # Initialize filters
                if not self.initialize_filters():
                    raise Exception("Failed to initialize filters")

                # Process the state
                if self.process_state(state):
                    # Reset retry count on success
                    self.progress[retry_key] = 0
                    return True

                # If we get here, processing failed but didn't raise an exception
                raise Exception(f"Failed to process state: {state}")

            except Exception as e:
                # Update retry count
                self.progress[retry_key] = attempt + 1
                self.save_progress()

                if attempt + 1 >= self.config.max_retries:
                    logging.error(f"State {state} failed after {self.config.max_retries} attempts, skipping")
                    return True  # Return True to move to next state

                logging.warning(f"Attempt {attempt + 1}/{self.config.max_retries} failed for state {state}. Retrying in {self.config.retry_delay} seconds.")
                time.sleep(self.config.retry_delay)

        return False

    def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.driver:
                self.driver.quit()
                logging.info("WebDriver closed successfully")
        except Exception as e:
            logging.error(f"Error closing WebDriver: {e}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Vahan Data Scraper")

    parser.add_argument(
        "--chrome-path",
        type=str,
        default="C:/Program Files (x86)/chrome-win64/chrome.exe",
        help="Path to Chrome executable"
    )

    parser.add_argument(
        "--download-path",
        type=str,
        default=None,
        help="Base path for downloads (default: ~/Downloads/VahanData)"
    )

    parser.add_argument(
        "--year",
        type=str,
        default=str(datetime.now().year), # This is the crucial change
        help="Year to select in Vahan dashboard"  # Removed choices
    )

    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=30,
        help="Timeout for WebDriverWait operations in seconds"
    )

    parser.add_argument(
        "--download-timeout",
        type=int,
        default=60,
        help="Timeout for download operations in seconds"
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries for operations"
    )

    parser.add_argument(
        "--retry-delay",
        type=int,
        default=60,
        help="Delay between retries in seconds"
    )

    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Reset progress and start from beginning"
    )

    parser.add_argument(
        "--state",
        type=str,
        help="Process only a specific state (must match exactly as in the dropdown)"
    )

    return parser.parse_args()


def main():
    """Main function to run the scraper."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Check if Chrome binary exists
        chrome_path = args.chrome_path
        if not os.path.exists(chrome_path):
            raise FileNotFoundError(f"Chrome binary not found at: {chrome_path}")

        # Create config
        config = VahanScraperConfig(
            chrome_binary_path=chrome_path,
            download_path=args.download_path,
            wait_timeout=args.wait_timeout,
            download_timeout=args.download_timeout,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay,
            year=args.year
        )

        # Create and run the scraper
        scraper = VahanScraper(config)

        # If reset progress flag is set, delete the progress file
        if args.reset_progress and os.path.exists(scraper.progress_file):
            os.remove(scraper.progress_file)
            logging.info(f"Progress file deleted: {scraper.progress_file}")
            scraper.progress = scraper._init_progress()

        # If state is specified, find its index and set as current
        if args.state:
            try:
                state_index = scraper.states_ut.index(args.state)
                scraper.current_state_index = state_index
                scraper.current_rto_index = 0
                logging.info(f"Starting with specific state: {args.state} (index: {state_index})")
            except ValueError:
                logging.error(f"State '{args.state}' not found in the list. Please check the spelling.")
                print(f"Available states: {', '.join(scraper.states_ut)}")
                return

        # Run the scraper
        scraper.scrape_data()

    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
