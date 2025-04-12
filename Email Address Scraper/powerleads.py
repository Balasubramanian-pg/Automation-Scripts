import pandas as pd
import time
import os
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# ========== CONFIGURATION ========== 
LINKEDIN_EMAIL = "balasubramanian.ganeshan@flipcarbon.in"    # Replace with your email
LINKEDIN_PASSWORD = "Burner23!"     # Replace with your password
EXTENSION_ID = "ijfmjempkpegmlhcacclfckeimbfgabp"  # Power Leads extension ID

# File paths - REPLACE WITH YOUR PATHS
excel_file = r"F:\Flipcarbon\2025\4. April\10-04-2025\Cleaned leads.xlsx"
output_file = r"F:\Flipcarbon\2025\4. April\10-04-2025\Cleaned leads with contact info.xlsx"
cookies_file = r"F:\Flipcarbon\2025\4. April\10-04-2025\linkedin_cookies.pkl"

# ========== SETUP CHROME DRIVER ==========
def setup_driver():
    """Configure Chrome browser with extension support"""
    options = webdriver.ChromeOptions()
    
    # Essential settings
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    
    # Enable extensions and automation
    options.add_argument("--enable-extensions")
    options.add_experimental_option("useAutomationExtension", True)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # IMPORTANT: Configure Chrome to use your existing profile (update path)
    # Find your Chrome profile path: chrome://version/ -> "Profile Path"
    # Example for Windows:
    # options.add_argument(r"--user-data-dir=C:\Users\YOUR_USERNAME\AppData\Local\Google\Chrome\User Data")
    # options.add_argument("--profile-directory=Default")
    
    try:
        driver = webdriver.Chrome(options=options)
        print("Chrome driver started successfully!")
        return driver
    except Exception as e:
        print(f"Failed to start Chrome: {e}")
        return None

# ========== LINKEDIN LOGIN ==========
def login_to_linkedin(driver):
    """Handle LinkedIn login with cookies or credentials"""
    try:
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        
        # Try using saved cookies first
        if os.path.exists(cookies_file):
            print("Loading cookies...")
            with open(cookies_file, 'rb') as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except Exception:
                        continue
            driver.refresh()
            time.sleep(3)
            
            if "feed" in driver.current_url:
                print("Logged in via cookies!")
                return True
        
        # Manual login if cookies fail
        print("Performing manual login...")
        try:
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(LINKEDIN_EMAIL)
            
            password_field = driver.find_element(By.ID, "password")
            password_field.send_keys(LINKEDIN_PASSWORD)
            
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            time.sleep(5)
            
            # Save cookies if login successful
            if "feed" in driver.current_url:
                with open(cookies_file, 'wb') as f:
                    pickle.dump(driver.get_cookies(), f)
                print("Login successful! Cookies saved.")
                return True
                
            return False
        except TimeoutException:
            print("Login page elements not found. Check if already logged in.")
            return "feed" in driver.current_url
    except Exception as e:
        print(f"Login error: {e}")
        return False

# ========== POWER LEADS AUTOMATION ==========
def open_extension_popup(driver):
    """Open the Power Leads extension popup using keyboard shortcuts"""
    try:
        # Open extension menu
        ActionChains(driver).key_down(Keys.ALT).send_keys('F').key_up(Keys.ALT).perform()
        time.sleep(1)
        
        # Navigate to extensions
        ActionChains(driver).send_keys(Keys.ARROW_DOWN * 3).send_keys(Keys.ENTER).perform()
        time.sleep(2)
        
        print("Opened extension menu")
        return True
    except Exception as e:
        print(f"Failed to open extension menu: {e}")
        return False

def get_contact_info(driver, profile_url):
    """Automate contact info extraction using Power Leads"""
    original_window = driver.current_window_handle
    try:
        # Open profile in new tab
        driver.switch_to.new_window('tab')
        driver.get(profile_url)
        print(f"Opened profile: {profile_url}")
        time.sleep(5)
        
        # Try to activate Power Leads
        try:
            # Use keyboard shortcut (Alt+Shift+P)
            ActionChains(driver)\
                .key_down(Keys.ALT)\
                .key_down(Keys.SHIFT)\
                .send_keys('p')\
                .key_up(Keys.SHIFT)\
                .key_up(Keys.ALT)\
                .perform()
            print("Sent keyboard shortcut for Power Leads")
            time.sleep(3)
        except Exception as e:
            print(f"Keyboard shortcut failed: {e}")
        
        # Switch to extension popup
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if "chrome-extension" in driver.current_url:
                break
                
        # Extract contact information
        emails = []
        phones = []
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.email-result, .phone-result'))
            )
            
            # Get emails
            email_elements = driver.find_elements(By.CSS_SELECTOR, '.email-result')
            emails = [e.text.strip() for e in email_elements if '@' in e.text]
            
            # Get phones
            phone_elements = driver.find_elements(By.CSS_SELECTOR, '.phone-result')
            phones = [p.text.strip() for p in phone_elements if any(c.isdigit() for c in p.text)]
            
            print(f"Found {len(emails)} emails and {len(phones)} phones")
        except Exception as e:
            print(f"Error extracting info: {e}")
        
        # Close extension window
        driver.close()
        driver.switch_to.window(original_window)
        
        return emails[:2], phones[:2]
    
    except Exception as e:
        print(f"Error in get_contact_info: {e}")
        driver.switch_to.window(original_window)
        return [], []

# ========== MAIN PROCESS ==========
def main():
    driver = setup_driver()
    if not driver:
        return
    
    if not login_to_linkedin(driver):
        print("Failed to login. Exiting.")
        driver.quit()
        return
    
    try:
        df = pd.read_excel(excel_file)
        if 'URL' not in df.columns:
            raise Exception("Missing 'URL' column in Excel file")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        driver.quit()
        return
    
    # Prepare columns
    for col in ['Email 1', 'Email 2', 'Primary Phone', 'Secondary Phone']:
        if col not in df.columns:
            df[col] = pd.NA
    
    # Process profiles
    for index, row in df.iterrows():
        if pd.isna(row['URL']) or not row['URL'].strip():
            continue
            
        print(f"\nProcessing {index+1}/{len(df)}: {row['URL']}")
        
        if not pd.isna(row['Email 1']):
            print("Already processed, skipping...")
            continue
            
        emails, phones = get_contact_info(driver, row['URL'])
        
        # Update dataframe
        df.at[index, 'Email 1'] = emails[0] if len(emails) > 0 else pd.NA
        df.at[index, 'Email 2'] = emails[1] if len(emails) > 1 else pd.NA
        df.at[index, 'Primary Phone'] = phones[0] if len(phones) > 0 else pd.NA
        df.at[index, 'Secondary Phone'] = phones[1] if len(phones) > 1 else pd.NA
        
        # Save progress
        if (index + 1) % 5 == 0:
            df.to_excel(output_file, index=False)
            print(f"Auto-saved after {index+1} profiles")
        
        time.sleep(2 + (index % 4))
    
    # Final save
    df.to_excel(output_file, index=False)
    print(f"\nProcess completed! Results saved to: {output_file}")
    driver.quit()

if __name__ == "__main__":
    main()
