import re
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# Use undetected_chromedriver consistently
import undetected_chromedriver as uc
# Need this to parse the Google redirect URL
from urllib.parse import urlparse, parse_qs, unquote
from fake_useragent import UserAgent
from typing import List, Dict, Optional
import traceback # For detailed errors if needed

class LinkedInScraper:
    def __init__(self):
        self.driver: Optional[uc.Chrome] = None
        self.data: List[Dict] = []
        self.ua = UserAgent()
        self.window_sizes = [(1366, 768), (1440, 900), (1536, 864), (1920, 1080)]

    def setup_driver(self) -> uc.Chrome:
        """Sets up undetected_chromedriver, letting it auto-detect the version."""
        print("Setting up undetected_chromedriver (auto-detecting version)...")
        try:
            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox") # Add if needed in specific environments
            options.add_argument("--disable-dev-shm-usage") # Add if needed in specific environments
            # options.add_argument("--headless") # Keep headless off for debugging

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

    def perform_search(self, query: str):
        """Navigates to Google and performs the search."""
        print(f"Navigating to Google and searching for: {query}")
        try:
            self.driver.get("https://www.google.com")
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
            try: self.driver.save_screenshot('error_search_page.png')
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

            # Commented out verbose print for cleaner output during run
            # print(f"  + Extracted: Name='{entry.get('Name')}', Title='{entry.get('Title')}', Company='{entry.get('Company_Name')}', URL='{entry.get('LinkedIn_URL')}'")
            return entry
        except Exception:
            # print(f"  - Error processing result block: {e}") # Keep minimal output
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
                 # Prioritize divs containing the specific link class from example
                 result_blocks = self.driver.find_elements(By.CSS_SELECTOR, "div:has(a.zReHs)")
                 if not result_blocks: # If primary fails, fallback to div.g
                      result_blocks = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
                 print(f"Found {len(result_blocks)} potential result blocks.")
            except Exception as find_e:
                 print(f"Error finding blocks, falling back to 'div.g': {find_e}")
                 result_blocks = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
                 print(f"Found {len(result_blocks)} potential result blocks using 'div.g'.")

            if not result_blocks:
                print("Warning: No result blocks found.")
                try: self.driver.save_screenshot('error_no_results_blocks.png')
                except: pass
                return

            global_urls = {d['LinkedIn_URL'] for d in self.data if d.get('LinkedIn_URL')}

            for i, result_element in enumerate(result_blocks):
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", result_element)
                    time.sleep(random.uniform(0.1, 0.3))
                except Exception: pass

                entry = self.extract_profile_data(result_element)

                if entry and entry.get('LinkedIn_URL'):
                    url = entry['LinkedIn_URL']
                    if url not in global_urls:
                        self.data.append(entry)
                        global_urls.add(url)
                        processed_count += 1

            print(f"Added {processed_count} new unique profiles from this page.")

        except Exception as e:
            print(f"Error processing results page: {str(e)}")
            try: self.driver.save_screenshot('error_process_page.png')
            except: pass

    # --- UPDATED navigate_next_page with JavaScript Click ---
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
            try: self.driver.save_screenshot('error_next_page_navigate.png')
            except: pass
            return False
    # --- END UPDATED navigate_next_page ---

    def run(self):
        """Main method to run the scraping process."""
        city = input("Enter city name: ").strip()
        designation = input("Enter designation: ").strip()

        max_profiles_input = input("Enter the maximum number of profiles to scrape (e.g., 50): ").strip()
        try:
            max_profiles = int(max_profiles_input)
            if max_profiles <= 0:
                print("Number of profiles must be positive. Defaulting to 50.")
                max_profiles = 50
        except ValueError:
            print("Invalid number entered. Defaulting to 50 profiles.")
            max_profiles = 50

        query = f'"{designation}" "{city}" site:linkedin.com/in'
        print(f"\nStarting search for query: {query}")
        print(f"Targeting up to {max_profiles} profiles.")

        self.driver = self.setup_driver()
        if self.driver is None: return

        try:
            self.perform_search(query)
            page_count = 0
            max_pages = 10 # Safety page limit
            stop_reason = "Reached page limit or no more results"

            while page_count < max_pages and len(self.data) < max_profiles:
                print(f"\n--- Processing Page {page_count + 1} (Found {len(self.data)}/{max_profiles} profiles) ---")
                self.process_results_page()

                if len(self.data) >= max_profiles:
                    print(f"\nTarget number of profiles ({max_profiles}) reached.")
                    stop_reason = f"Reached target of {max_profiles} profiles"
                    break

                if len(self.data) < max_profiles and page_count < max_pages - 1:
                    if not self.navigate_next_page(): # Use the updated navigation function
                        stop_reason = "No next page found or error during navigation"
                        break
                elif page_count >= max_pages - 1:
                     print(f"\nReached maximum page limit ({max_pages}).")
                     stop_reason = f"Reached maximum page limit ({max_pages})"
                     break

                page_count += 1
                if len(self.data) < max_profiles and page_count < max_pages:
                     print(f"Pausing before next page...")
                     self.human_like_delay(3, 6)

            print(f"\nScraping finished. Reason: {stop_reason}.")

        except Exception as e:
            print(f"\nAn critical error occurred during scraping: {str(e)}")
            traceback.print_exc()
        finally:
            if self.driver:
                print("Closing browser window...")
                self.driver.quit()

            if self.data:
                final_data = self.data[:max_profiles]
                print(f"\nPreparing data for saving ({len(final_data)} entries)...")

                df = pd.DataFrame(final_data, columns=['Name', 'Title', 'Company_Name', 'LinkedIn_URL'])
                df.dropna(subset=['LinkedIn_URL'], inplace=True)
                df.drop_duplicates(subset=['LinkedIn_URL'], keep='first', inplace=True)
                for col in ['Name', 'Title', 'Company_Name']:
                     if col in df.columns:
                          df[col] = df[col].astype(str).str.strip().replace('None', '', regex=False).replace('^$', '', regex=True)
                          df.loc[df[col] == '', col] = None

                df.reset_index(drop=True, inplace=True)
                df = df.head(max_profiles) # Ensure exact number
                print(f"Final unique profiles count: {len(df)}")

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
            else:
                print("\nNo LinkedIn profiles were successfully extracted.")

if __name__ == "__main__":
    # Ensure necessary libraries are installed:
    # pip install selenium pandas undetected-chromedriver fake-useragent openpyxl requests
    scraper = LinkedInScraper()
    scraper.run()
