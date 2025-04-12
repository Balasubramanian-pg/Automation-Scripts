import os
import time
import random
import logging
import pandas as pd
from urllib.parse import parse_qs, urlparse
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_scraper.log'),
        logging.StreamHandler()
    ]
)

class LinkedInScraper:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.df = None
        self.driver = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        ]
        self.setup_driver()
        self.setup_stealth()

    def setup_driver(self):
        """Configure Chrome with advanced stealth settings"""
        chrome_options = webdriver.ChromeOptions()

        # Anti-detection configurations
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # Random user agent
        chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")

        # Proxy configuration (uncomment and add your proxies)
        # chrome_options.add_argument("--proxy-server=ip:port")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Mask webdriver properties
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def setup_stealth(self):
        """Additional stealth measures"""
        self.driver.execute_cdp_cmd(
            'Network.setUserAgentOverride',
            {"userAgent": random.choice(self.user_agents)}
        )

    def human_delay(self):
        """Randomized human-like delays with mouse movements"""
        time.sleep(random.uniform(0.8, 1))  # Reduced delay range
        self.human_mouse_movement()

    def human_mouse_movement(self):
        """Generate random mouse movements"""
        try:
            actions = ActionChains(self.driver)
            for _ in range(random.randint(0.5, 1)):
                x_offset = random.randint(-50, 50)
                y_offset = random.randint(-50, 50)
                actions.move_by_offset(x_offset, y_offset)
            actions.perform()
        except Exception as e:
            logging.debug(f"Mouse movement error: {str(e)}")

    def search_google(self, query):
        """Perform Google search with enhanced human-like interactions"""
        self.driver.get("https://www.google.com")
        self.human_delay()

        try:
            cookie_btn = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "L2AGLb")))
            cookie_btn.click()
            self.human_delay()
        except:
            pass

        search_box = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )

        # Type like a human
        for char in query:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.08, 0.3))
            if random.random() < 0.1:  # 10% chance to "mistype" and correct
                search_box.send_keys('\b')
                time.sleep(0.2)
                search_box.send_keys(char)

        # Random delay before submitting
        time.sleep(random.uniform(0.5, 1.2))
        search_box.submit()
        self.human_delay()

    def check_for_captcha(self):
        """Detect and handle CAPTCHA challenges"""
        try:
            captcha_frame = self.driver.find_elements(By.TAG_NAME, "iframe")
            if any("challenge" in frame.get_attribute("src") for frame in captcha_frame):
                logging.warning("CAPTCHA detected! Please solve manually")
                input("Press Enter after solving CAPTCHA...")
                return True
        except:
            pass
        return False

    def get_linkedin_profiles_from_search_results(self, company):
        """Extract LinkedIn URLs and names from first 3 pages of Google search results"""
        linkedin_profiles = []
        page_number = 0
        max_pages = 3

        while page_number < max_pages:
            try:
                if self.check_for_captcha():
                    return linkedin_profiles # Stop if CAPTCHA and return current profiles

                # Wait for search results page to load (ensure search ID is present) - Wait only on first page
                if page_number == 0:
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.ID, "search"))
                    )
                    logging.info(f"Search results page {page_number+1} loaded, proceeding to find links.")
                else:
                    logging.info(f"Processing search results page {page_number+1}...")


                # Get all result links - Use the CSS selector: a.zReHs
                results = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.zReHs"))
                )
                logging.info(f"Found {len(results)} search result links on page {page_number+1} using selector 'a.zReHs'.")

                if not results:
                    logging.warning(f"No search results found on page {page_number+1} using selector 'a.zReHs'!")
                    break # No more results on this page, stop paginating

                for result in results:
                    try:
                        logging.info(f"Processing result: {result.text}")
                        href = result.get_attribute("href")
                        if not href:
                            logging.warning("Result link has no href attribute.")
                            continue

                        # Handle Google redirects
                        if "google.com/url" in href:
                            parsed = urlparse(href)
                            actual_url = parse_qs(parsed.query).get('q', [''])[0]
                        else:
                            actual_url = href

                        logging.info(f"Extracted URL: {actual_url}")

                        if 'linkedin.com/in/' in actual_url.lower():
                            linkedin_url = actual_url
                            logging.info(f"Found LinkedIn URL: {linkedin_url}")

                            # Extract Full Name from result.text (before " - LinkedIn")
                            try:
                                name_part = result.text.split(" - LinkedIn")[0].strip()
                                full_name = name_part
                                logging.info(f"Extracted Full Name: {full_name}")
                            except:
                                logging.debug("Could not reliably extract Full Name from result text.")
                                full_name = None

                            linkedin_profiles.append({'linkedin_url': linkedin_url, 'full_name': full_name})

                        else:
                            logging.info(f"Skipping non-LinkedIn URL: {actual_url}")

                    except Exception as e:
                        logging.debug(f"Result processing error: {str(e)}")
                        continue

                if page_number < max_pages:
                    try:
                        next_page_links = self.driver.find_elements(By.ID, "pnnext") # Find 'Next' page button(s) - using find_elements
                        if next_page_links: # Check if any 'Next' buttons are found
                            next_page_link = next_page_links[0] # Take the first one if multiple
                            self.human_delay()
                            next_page_link.click()
                            WebDriverWait(self.driver, 2).until(
                                EC.staleness_of(results[0]) # Wait for page to change and old results to be stale
                            )
                        else:
                            logging.info("No 'Next' page button found on page, stopping pagination.")
                            break # No next page button, stop pagination
                    except (NoSuchElementException, TimeoutException) as e: # Catch specific exceptions
                        logging.info(f"Problem finding/clicking 'Next' page button or timeout: {str(e)}. Stopping pagination.")
                        break # Stop pagination if 'Next' button issues or timeout


            except TimeoutException:
                logging.warning(f"Timeout waiting for next page or search results on page {page_number+1}. Stopping pagination.")
                break # Timeout, stop pagination
            except Exception as e:
                logging.error(f"Search/Pagination error on page {page_number+1}: {str(e)}")
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                self.driver.save_screenshot(f"error_page_{page_number+1}_{company}_{timestamp}.png")
                with open(f"page_source_page_{page_number+1}_{company}_{timestamp}.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                break # Stop pagination on general error

            page_number += 1


        logging.info(f"Found {len(linkedin_profiles)} LinkedIn profiles for {company} across {page_number} pages.")
        return linkedin_profiles


    def process_companies(self):
        """Main processing - Extracts LinkedIn URLs and Names from 3 pages of search results"""
        logging.info(f"Reading Excel file: {self.excel_path}")
        self.df = pd.read_excel(self.excel_path)

        # Prepare columns for multiple LinkedIn profiles (up to 15 - 5 per page * 3 pages)
        for i in range(1, 16):
            if f'LinkedIn URL {i}' not in self.df.columns:
                self.df[f'LinkedIn URL {i}'] = ''
            if f'Full Name {i}' not in self.df.columns:
                self.df[f'Full Name {i}'] = ''

        total = len(self.df)
        for index, row in self.df.iterrows():
            company = row['Company']
            if pd.isna(company):
                continue

            try:
                # Vary search terms randomly and include "India"
                position = random.choice(['Sales Director', 'VP Sales',
                                         'Managing Director', 'Sales VP'])
                query = f"{company} {position} LinkedIn India" # Added "India" to search
                logging.info(f"Searching ({index+1}/{total}): {query}")

                self.search_google(query)
                linkedin_profiles = self.get_linkedin_profiles_from_search_results(company) # Get list of profiles

                for i, profile in enumerate(linkedin_profiles):
                    if i < 15: # Limit to 15 profiles max (5 per page * 3 pages)
                        self.df.at[index, f'LinkedIn URL {i+1}'] = profile['linkedin_url']
                        self.df.at[index, f'Full Name {i+1}'] = profile['full_name']
                        logging.info(f"  Profile {i+1}: LinkedIn URL - {profile['linkedin_url']}, Full Name - {profile['full_name']}")

                if not linkedin_profiles:
                    logging.warning(f"No LinkedIn results found for {company} in first 3 pages.")


                # Save progress regularly
                if index % 5 == 0:
                    self.save_progress()

                # Randomized long break
                time.sleep(random.uniform(0.6, 1.9))

            except Exception as e:
                logging.error(f"Critical error processing {company}: {str(e)}")
                self.save_progress()
                continue

        self.save_progress()
        self.driver.quit()

    def save_progress(self):
        """Save results with error handling"""
        try:
            backup_path = os.path.join(
                os.path.dirname(self.excel_path),
                f"BACKUP_{os.path.basename(self.excel_path)}"
            )
            self.df.to_excel(backup_path, index=False)
            self.df.to_excel(self.excel_path, index=False)
            logging.info("Progress saved to primary and backup files")
        except Exception as e:
            logging.error(f"Save error: {str(e)}")

if __name__ == "__main__":
    excel_path = r"F:\Flipcarbon\2025\4. April\10-04-2025\Automotive Directors.xlsx"

    if not os.path.exists(excel_path):
        logging.error("Excel file not found!")
        exit()

    scraper = LinkedInScraper(excel_path)
    try:
        scraper.process_companies()
        logging.info("Process completed successfully")
    except KeyboardInterrupt:
        logging.info("User interrupted process - saving current progress")
        scraper.save_progress()
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
    finally:
        if scraper.driver:
            scraper.driver.quit()
