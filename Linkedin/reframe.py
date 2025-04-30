import re
import time
import random
import pandas as pd
import os
import json
from selenium import webdriver
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
# Use undetected_chromedriver consistently
import undetected_chromedriver as uc
# Need this to parse the Google redirect URL
from urllib.parse import urlparse, parse_qs, unquote
from fake_useragent import UserAgent
from typing import List, Dict, Optional, Set
import traceback # For detailed errors if needed

class LinkedInScraper:
    def __init__(self):
        self.driver: Optional[uc.Chrome] = None
        self.data: List[Dict] = []
        self.ua = UserAgent()
        self.window_sizes = [(1366, 768), (1440, 900), (1536, 864), (1920, 1080)]
        self.checkpoint_file = "linkedin_scrape_checkpoint.json"
        self.visited_urls: Set[str] = set()
        self.current_query_page = 0
        self.total_pages_scraped = 0
        self.queries = []
        self.current_query_index = 0
        self.max_profiles = 50  # Default, will be updated

    def setup_driver(self) -> uc.Chrome:
        """Sets up undetected_chromedriver, letting it auto-detect the version."""
        print("Setting up undetected_chromedriver (auto-detecting version)...")
        try:
            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox") # Add if needed in specific environments
            options.add_argument("--disable-dev-shm-usage") # Add if needed in specific environments
            # options.add_argument("--headless") # Keep headless off for debugging

            # Add user agent rotation
            user_agent = self.ua.random
            options.add_argument(f'--user-agent={user_agent}')
            print(f"Using user agent: {user_agent}")

            print("Calling uc.Chrome()...")
            driver = uc.Chrome(options=options) # Ensure version_main is NOT specified
            print("uc.Chrome() call successful.")

            driver.set_window_size(*random.choice(self.window_sizes))
            print("Driver setup successful, window resized.")
            return driver
        except Exception as e:
            print(f"Failed to setup undetected_chromedriver: {str(e)}")
            print("--- DETAILED ERROR ---")
            traceback.print_exc()
            print("--- END DETAILED ERROR ---")
            print("Common causes: Chrome/driver mismatch (should be auto handled by UC), Chrome not found, zombie processes, antivirus.")
            print("Exiting.")
            exit()

    def human_like_delay(self, min_sec=0.5, max_sec=1.5):
        time.sleep(random.uniform(min_sec, max_sec))

    def human_like_typing(self, element, text: str):
        """Simpler typing simulation."""
        try:
            element.click()
            time.sleep(random.uniform(0.1, 0.3))
        except Exception: pass

        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.18))
        self.human_like_delay(0.3, 0.7)

    def generate_search_queries(self, city: str, designation: str) -> List[str]:
        """Generate multiple search queries to maximize results."""
        base_queries = [
            f'"{designation}" "{city}" site:linkedin.com/in',
            f'"{designation}" {city} site:linkedin.com/in',
            f'{designation} "{city}" site:linkedin.com/in',
            f'{designation} {city} site:linkedin.com/in'
        ]

        # Create variants by adding professional terms
        professional_terms = ["professional", "profile", "experience", "resume"]
        variant_queries = []

        for query in base_queries:
            for term in professional_terms:
                variant_queries.append(f"{query} {term}")

        # Add education variants if appropriate
        education_variants = []
        if designation.lower() in ["developer", "engineer", "analyst", "scientist", "doctor", "professor"]:
            education_terms = ["degree", "university", "college", "education", "graduate"]
            for query in base_queries:
                for term in education_terms:
                    education_variants.append(f"{query} {term}")

        # Combine and remove duplicates while preserving order
        all_queries = base_queries + variant_queries + education_variants
        unique_queries = []
        seen = set()
        for query in all_queries:
            if query not in seen:
                unique_queries.append(query)
                seen.add(query)

        return unique_queries

    def perform_search(self, query: str):
        """Navigates to Google and performs the search."""
        print(f"Navigating to Google and searching for: {query}")
        try:
            # Rotate between Google domains
            google_domains = [
                "https://www.google.com",
                "https://www.google.co.uk",
                "https://www.google.ca",
                "https://www.google.com.au"
            ]
            chosen_domain = random.choice(google_domains)
            self.driver.get(chosen_domain)
            self.human_like_delay(1, 2.5)

            # Basic Cookie Handling
            try:
                # Combine selectors with | (OR) in XPath
                cookie_button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Reject all') or contains(., 'Alle ablehnen') or contains(., 'Accept all') or contains(., 'Alle akzeptieren')]")))
                button_text = cookie_button.text
                cookie_button.click()
                print(f"Clicked cookie button: '{button_text}'")
                self.human_like_delay(0.5, 1)
            except TimeoutException:
                 print("Cookie consent buttons not immediately visible or already handled.")
                 pass

            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'q'))
            )

            search_box.send_keys(Keys.CONTROL + "a")
            time.sleep(random.uniform(0.1, 0.3))
            search_box.send_keys(Keys.DELETE)
            self.human_like_delay(0.3, 0.6)
            self.human_like_typing(search_box, query)

            search_box.send_keys(Keys.RETURN)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#search'))
            )
            print("Search results page loaded.")
            self.human_like_delay(1, 2)

        except Exception as e:
            print(f"Failed during search navigation/input: {str(e)}")
            try: self.driver.save_screenshot(f'error_search_page_{time.strftime("%Y%m%d_%H%M%S")}.png')
            except: pass
            raise

    def extract_profile_data(self, result_element):
        """
        Extracts core data from a single Google search result block,
        targeting the structure shown in the example HTML.
        """
        entry = {'Name': None, 'Title': None, 'Company_Name': None, 'LinkedIn_URL': None}
        try:
            link_element = None
            google_href = None
            try:
                link_element = WebDriverWait(result_element, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.zReHs")) # Specific link class from example
                )
            except (TimeoutException, NoSuchElementException):
                 try: # Fallback 1: Common structure
                      link_element = WebDriverWait(result_element, 1).until(
                           EC.presence_of_element_located((By.CSS_SELECTOR, "div.yuRUbf > a"))
                      )
                 except (TimeoutException, NoSuchElementException):
                      try: # Fallback 2: Any link within the block
                           link_element = result_element.find_element(By.TAG_NAME, "a")
                      except NoSuchElementException:
                           return None # No link found

            google_href = link_element.get_attribute('href')
            if not google_href: return None

            try:
                parsed_url = urlparse(google_href)
                query_params = parse_qs(parsed_url.query)
                actual_urls = query_params.get('url', [])
                if actual_urls:
                    entry['LinkedIn_URL'] = unquote(actual_urls[0])
                elif 'linkedin.com/in/' in google_href or 'linkedin.com/pub/' in google_href: # Check if href is direct URL
                     entry['LinkedIn_URL'] = google_href
                else: return None

                if not entry['LinkedIn_URL'] or not ('linkedin.com/in/' in entry['LinkedIn_URL'] or 'linkedin.com/pub/' in entry['LinkedIn_URL']):
                    return None
            except Exception: return None # Error during URL parsing

            full_title = None
            try:
                title_element = link_element.find_element(By.CSS_SELECTOR, "h3.LC20lb") # Specific class from example
                full_title = title_element.text.strip()
            except NoSuchElementException:
                 try: # Fallback to generic H3
                      title_element = link_element.find_element(By.TAG_NAME, "h3")
                      full_title = title_element.text.strip()
                 except NoSuchElementException: pass

            if full_title:
                parts = full_title.split(' - ', 1)
                entry['Name'] = parts[0].strip()
                if len(parts) > 1:
                    title_company_part = parts[1]
                    title_company_split = title_company_part.split(' - ', 1)
                    entry['Title'] = title_company_split[0].strip()
                    if len(title_company_split) > 1:
                        entry['Company_Name'] = title_company_split[1].replace('...', '').strip()
                    else: entry['Title'] = title_company_part.strip() # Whole part is title if no second hyphen
                else: entry['Name'] = full_title # Assume whole H3 is Name if no hyphen

            # Fallback name extraction from URL
            if not entry['Name'] and entry['LinkedIn_URL']:
                 url_name_match = re.search(r'/in/([\w-]+)', entry['LinkedIn_URL'])
                 if url_name_match:
                     name_from_url = url_name_match.group(1).replace('-', ' ').title()
                     entry['Name'] = re.sub(r'\s+\w*\d+\w*$', '', name_from_url).strip()

            return entry
        except Exception:
            return None

    def process_results_page(self):
        """Processes search results on the current page."""
        print("Processing search results...")
        processed_count = 0
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#search'))
            )

            result_blocks = []
            try:
                 # Try multiple selector strategies for better coverage
                 result_blocks = self.driver.find_elements(By.CSS_SELECTOR, "div:has(a.zReHs)")
                 if not result_blocks:
                      result_blocks = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
                 if not result_blocks:
                      result_blocks = self.driver.find_elements(By.CSS_SELECTOR, "div[data-sokoban-container]")
                 print(f"Found {len(result_blocks)} potential result blocks.")
            except Exception as find_e:
                 print(f"Error finding blocks, falling back to 'div.g': {find_e}")
                 result_blocks = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
                 print(f"Found {len(result_blocks)} potential result blocks using 'div.g'.")

            if not result_blocks:
                print("Warning: No result blocks found.")
                try: self.driver.save_screenshot(f'error_no_results_blocks_{time.strftime("%Y%m%d_%H%M%S")}.png')
                except: pass
                return

            for i, result_element in enumerate(result_blocks):
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", result_element)
                    time.sleep(random.uniform(0.1, 0.3))
                except Exception: pass

                entry = self.extract_profile_data(result_element)

                if entry and entry.get('LinkedIn_URL'):
                    url = entry['LinkedIn_URL']
                    if url not in self.visited_urls:
                        self.data.append(entry)
                        self.visited_urls.add(url)
                        processed_count += 1

            print(f"Added {processed_count} new unique profiles from this page.")
            self.save_checkpoint()

        except Exception as e:
            print(f"Error processing results page: {str(e)}")
            try: self.driver.save_screenshot(f'error_process_page_{time.strftime("%Y%m%d_%H%M%S")}.png')
            except: pass

    def save_checkpoint(self):
        """Save current progress to allow resuming."""
        checkpoint_data = {
            "data": self.data,
            "visited_urls": list(self.visited_urls),
            "current_query_index": self.current_query_index,
            "current_query_page": self.current_query_page,
            "total_pages_scraped": self.total_pages_scraped,
            "max_profiles": self.max_profiles,
            "queries": self.queries
        }

        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f)
            print(f"Checkpoint saved: {len(self.data)} profiles, {self.total_pages_scraped} pages")
        except Exception as e:
            print(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self):
        """Load checkpoint if available."""
        if not os.path.exists(self.checkpoint_file):
            return False

        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)

            self.data = checkpoint_data["data"]
            self.visited_urls = set(checkpoint_data["visited_urls"])
            self.current_query_index = checkpoint_data["current_query_index"]
            self.current_query_page = checkpoint_data["current_query_page"]
            self.total_pages_scraped = checkpoint_data["total_pages_scraped"]
            self.max_profiles = checkpoint_data["max_profiles"]
            self.queries = checkpoint_data["queries"]

            print(f"Checkpoint loaded: {len(self.data)} profiles, {self.total_pages_scraped} pages")
            print(f"Resuming from query {self.current_query_index+1}/{len(self.queries)}, page {self.current_query_page+1}")
            return True
        except Exception as e:
            print(f"Failed to load checkpoint: {e}")
            return False

    def navigate_next_page(self):
        """Clicks the 'Next' page button, using JS click as the primary method."""
        print("Attempting to navigate to next page...")
        try:
            # Locate the button first using standard methods
            # Combine common selectors for robustness
            next_page_selector = "a#pnnext, a[aria-label='Next page'], a[aria-label='Næste']"
            try:
                # Wait for the element to be PRESENT in the DOM first
                next_btn = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, next_page_selector))
                )
                print("Found next page button element in DOM.")
            except TimeoutException:
                print("Next page button element not found in DOM (likely end of results).")
                return False


            # Scroll the button into view (still good practice)
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_btn)
                self.human_like_delay(0.8, 1.5) # Wait a bit after scrolling
            except Exception as scroll_err:
                print(f"Warning: Could not scroll next button into view: {scroll_err}")
                # Proceed to click anyway


            # --- Use JavaScript click as the PRIMARY method ---
            try:
                print("Attempting JavaScript click on next page button...")
                self.driver.execute_script("arguments[0].click();", next_btn)
                print("JavaScript click executed.")
            except Exception as js_click_err:
                 # This block might run if the JS click itself fails unexpectedly
                 print(f"JavaScript click failed: {js_click_err}.")
                 print("Attempting standard Selenium click as fallback...")
                 try:
                      # Wait for clickable state before standard click fallback
                      next_btn_clickable = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, next_page_selector))
                      )
                      next_btn_clickable.click()
                      print("Standard click executed as fallback.")
                 except Exception as standard_click_err:
                      print(f"Standard Selenium click also failed: {standard_click_err}")
                      raise standard_click_err # Re-raise the error to stop navigation


            # Wait for the next page's results container to load to confirm navigation
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#search'))
            )
            print("Next page search results container loaded.")
            self.human_like_delay(1, 2) # Small pause after page load confirmed
            return True

        except TimeoutException:
            # This might catch the wait for #search on the *next* page if nav failed silently
            print("Timed out waiting for next page results to load after click attempt.")
            return False
        except Exception as e:
            # Catches errors during the initial find, scroll, or click attempts
            print(f"An unexpected error occurred during next page navigation: {str(e)}")
            # traceback.print_exc() # Uncomment for full detail if needed
            try: self.driver.save_screenshot(f'error_next_page_navigate_{time.strftime("%Y%m%d_%H%M%S")}.png')
            except: pass
            return False

    def restart_browser(self):
        """Restart the browser to avoid detection."""
        print("Restarting browser to avoid detection...")
        try:
            if self.driver:
                self.driver.quit()
                print("Browser closed.")
        except Exception as e:
            print(f"Error closing browser: {e}")

        self.human_like_delay(10, 15)  # Wait longer before starting new browser
        self.driver = self.setup_driver()
        if not self.driver:
            raise Exception("Failed to restart browser")
        print("Browser restarted successfully.")

    def check_for_captcha(self):
        """Check if Google is showing a CAPTCHA or unusual activity warning."""
        try:
            captcha_selectors = [
                "//form[@id='captcha-form']",
                "//div[contains(text(), 'unusual traffic')]",
                "//div[contains(text(), 'automated requests')]",
                "//div[contains(text(), 'suspicious activity')]"
            ]

            for selector in captcha_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    print("CAPTCHA or unusual activity warning detected.")
                    return True
            return False
        except Exception:
            return False

    def handle_captcha(self):
        """Handle CAPTCHA situation by rotating proxy/IP or waiting."""
        print("CAPTCHA detected! Taking action...")

        # Save screenshot for manual inspection
        try:
            self.driver.save_screenshot(f'captcha_detected_{time.strftime("%Y%m%d_%H%M%S")}.png')
        except Exception:
            pass

        # Save checkpoint before handling
        self.save_checkpoint()

        # First strategy: wait for manual intervention
        print("\n" + "="*50)
        print("CAPTCHA DETECTED! Please complete the CAPTCHA manually in the browser window.")
        print("You have 5 minutes to solve the CAPTCHA.")
        print("The script will continue automatically after that time.")
        print("="*50 + "\n")

        # Wait for manual intervention (5 minutes max)
        max_wait = 300  # 5 minutes
        wait_interval = 15
        waited = 0

        while waited < max_wait:
            if not self.check_for_captcha():
                print("CAPTCHA appears to be solved. Continuing...")
                self.human_like_delay(2, 3)
                return True

            print(f"Waiting for manual CAPTCHA solving... ({waited}/{max_wait} seconds)")
            time.sleep(wait_interval)
            waited += wait_interval

        # If waiting didn't work, restart browser
        print("CAPTCHA not solved in time. Restarting browser...")
        self.restart_browser()
        return False

    def run(self):
        """Main method to run the scraping process."""
        resume = self.load_checkpoint()

        if not resume:
            # Get new inputs for a fresh start
            city = input("Enter city name: ").strip()
            designation = input("Enter designation: ").strip()

            max_profiles_input = input("Enter the maximum number of profiles to scrape (e.g., 6000): ").strip()
            try:
                self.max_profiles = int(max_profiles_input)
                if self.max_profiles <= 0:
                    print("Number of profiles must be positive. Defaulting to 6000.")
                    self.max_profiles = 6000
            except ValueError:
                print("Invalid number entered. Defaulting to 6000 profiles.")
                self.max_profiles = 6000

            # Generate multiple search queries for more comprehensive results
            self.queries = self.generate_search_queries(city, designation)
            print(f"\nGenerated {len(self.queries)} search queries for more comprehensive results.")
            for i, query in enumerate(self.queries):
                print(f"{i+1}. {query}")

            print(f"Targeting up to {self.max_profiles} profiles.")

            self.driver = self.setup_driver()
            if self.driver is None: return
        else:
            print(f"Resuming previous scraping session targeting {self.max_profiles} profiles.")
            self.driver = self.setup_driver()
            if self.driver is None: return

        try:
            max_pages_per_query = 20  # Increased from 10
            max_consecutive_errors = 3
            consecutive_errors = 0
            browser_restart_count = 0
            max_browser_restarts = 5

            while self.current_query_index < len(self.queries) and len(self.data) < self.max_profiles:
                current_query = self.queries[self.current_query_index]

                if self.current_query_page == 0:
                    print(f"\n=== Starting new query ({self.current_query_index+1}/{len(self.queries)}): {current_query} ===")
                    self.perform_search(current_query)
                else:
                    print(f"\n=== Resuming query ({self.current_query_index+1}/{len(self.queries)}): {current_query} ===")
                    print(f"=== Navigating to page {self.current_query_page+1} ===")

                    # Perform search again and navigate to the target page
                    self.perform_search(current_query)
                    page_navigation_successful = True

                    for page in range(self.current_query_page):
                        print(f"Navigating to intermediate page {page+1}...")
                        if not self.navigate_next_page():
                            page_navigation_successful = False
                            print(f"Failed to navigate to page {page+1}. Starting from page 1.")
                            self.current_query_page = 0
                            break

                    if not page_navigation_successful:
                        continue

                while self.current_query_page < max_pages_per_query and len(self.data) < self.max_profiles:
                    print(f"\n--- Processing Page {self.current_query_page + 1} for Query {self.current_query_index + 1} (Found {len(self.data)}/{self.max_profiles} profiles) ---")

                    # Check for CAPTCHA before processing
                    if self.check_for_captcha():
                        captcha_handled = self.handle_captcha()
                        if not captcha_handled:
                            # If captcha wasn't handled, we'd have restarted the browser
                            # Go back to the beginning of the current query
                            self.current_query_page = 0
                            break

                    try:
                        self.process_results_page()
                        consecutive_errors = 0  # Reset error counter on success
                        self.total_pages_scraped += 1
                    except Exception as e:
                        print(f"Error processing page: {str(e)}")
                        consecutive_errors += 1

                        if consecutive_errors >= max_consecutive_errors:
                            print(f"Too many consecutive errors ({consecutive_errors}). Restarting browser...")
                            browser_restart_count += 1

                            if browser_restart_count >= max_browser_restarts:
                                print(f"Exceeded maximum browser restarts ({max_browser_restarts}). Moving to next query.")
                                self.current_query_index += 1
                                self.current_query_page = 0
                                browser_restart_count = 0
                                consecutive_errors = 0
                                break

                            self.restart_browser()
                            consecutive_errors = 0
                            break  # Break out and restart current query

                        # Try to continue despite error
                        print("Attempting to continue despite error...")

                    if len(self.data) >= self.max_profiles:
                        print(f"\nTarget number of profiles ({self.max_profiles}) reached.")
                        break

                    # Add longer random delay between page navigations to avoid detection
                    page_delay = random.uniform(5, 15) if self.current_query_page % 5 == 0 else random.uniform(3, 7)
                    print(f"Pausing for {page_delay:.1f} seconds before next page...")
                    time.sleep(page_delay)

                    if not self.navigate_next_page():
                        print("No more results pages for this query.")
                        break

                    self.current_query_page += 1

                    # Mandatory page delay if we've crawled many pages
                    if self.total_pages_scraped > 0 and self.total_pages_scraped % 10 == 0:
                        long_delay = random.uniform(30, 60)
                        print(f"\n*** Taking a longer break ({long_delay:.1f}s) after {self.total_pages_scraped} pages to avoid detection ***")
                        time.sleep(long_delay)

                # Move to next query
                self.current_query_index += 1
                self.current_query_page = 0

                # Take a longer break between queries
                if self.current_query_index < len(self.queries):
                    query_delay = random.uniform(20, 40)
                    print(f"\n*** Taking a break ({query_delay:.1f}s) before next query ***")
                    time.sleep(query_delay)

                    # Every few queries, restart the browser completely
                    if self.current_query_index % 3 == 0:
                        print("\n*** Restarting browser between queries to avoid detection ***")
                        self.restart_browser()

            print(f"\nScraping finished. Total profiles collected: {len(self.data)}")

        except Exception as e:
            print(f"\nA critical error occurred during scraping: {str(e)}")
            traceback.print_exc()
        finally:
            if self.driver:
                print("Closing browser window...")
                self.driver.quit()

            if self.data:
                final_data = self.data[:self.max_profiles]
                print(f"\nPreparing data for saving ({len(final_data)} entries)...")

                df = pd.DataFrame(final_data, columns=['Name', 'Title', 'Company_Name', 'LinkedIn_URL'])
                df.dropna(subset=['LinkedIn_URL'], inplace=True)
                df.drop_duplicates(subset=['LinkedIn_URL'], keep='first', inplace=True)
                for col in ['Name', 'Title', 'Company_Name']:
                     if col in df.columns:
                          df[col] = df[col].astype(str).str.strip().replace('None', '', regex=False).replace('^$', '', regex=True)
                          df.loc[df[col] == '', col] = None

                df.reset_index(drop=True, inplace=True)

                # Split into chunks if a very large number of profiles
                if len(df) > 5000:
                    chunk_size = 5000
                    chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

                    for i, chunk in enumerate(chunks):
                        output_filename = f'linkedin_scrape_part{i+1}_{time.strftime("%Y%m%d_%H%M")}.xlsx'
                        try:
                            chunk.to_excel(output_filename, index=False, engine='openypxl')
                            print(f"Successfully saved {len(chunk)} profiles to '{output_filename}'")
                        except Exception as save_e:
                            print(f"Error saving data chunk {i+1} to Excel: {save_e}")
                            csv_filename = output_filename.replace('.xlsx', '.csv')
                            try:
                                chunk.to_csv(csv_filename, index=False)
                                print(f"Successfully saved {len(chunk)} profiles to '{csv_filename}'")
                            except Exception as csv_e:
                                print(f"Error saving data chunk {i+1} to CSV: {csv_e}")
                else:
                    output_filename = f'linkedin_scrape_{time.strftime("%Y%m%d_%H%M")}.xlsx'
                    try:
                        df.to_excel(output_filename, index=False, engine='openpyxl')
                        print(f"\nSuccessfully saved {len(df)} profiles to '{output_filename}'")
                    except Exception as save_e:
                        print(f"\nError saving data to Excel: {save_e}")
                        csv_filename = output_filename.replace('.xlsx', '.csv')
                        try:
                            df.to_csv(csv_filename, index=False)
                            print(f"Successfully saved {len(df)} profiles to '{csv_filename}'")
                        except Exception as csv_e:
                            print(f"Error saving data to CSV: {csv_e}")

                # Delete checkpoint file after successful completion
                try:
                    if os.path.exists(self.checkpoint_file):
                        os.remove(self.checkpoint_file)
                        print("Checkpoint file removed after successful completion.")
                except Exception as e:
                    print(f"Failed to remove checkpoint file: {e}")
            else:
                print("\nNo LinkedIn profiles were successfully extracted.")

# Example usage (add this outside the class definition)
if __name__ == "__main__":
    scraper = LinkedInScraper()
    scraper.run()
