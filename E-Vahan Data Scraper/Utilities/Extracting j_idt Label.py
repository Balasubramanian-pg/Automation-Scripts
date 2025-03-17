from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re

def setup_driver():
    """Set up and return a Chrome webdriver with appropriate options."""
    chrome_options = Options()
    # Uncomment the line below if you want to run headless
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_j_idt_from_id(id_value):
    """Extract j_idt label from an ID attribute."""
    match = re.search(r'j_idt\d+', id_value)
    if match:
        return match.group(0)
    return None

def main():
    # URL of the website
    url = "https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml"
    
    # Initialize the driver
    driver = setup_driver()
    
    try:
        # Navigate to the website
        print("Navigating to the website...")
        driver.get(url)
        
        # Wait for page to load completely
        print("Waiting for page to load...")
        time.sleep(3)  # Increased initial wait time
        
        # Find and select Y-axis (Maker)
        print("Selecting 'Maker' from Y-axis dropdown...")
        try:
            # First, click to open the dropdown
            y_axis_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "yaxisVar"))
            )
            y_axis_element.click()
            time.sleep(0.8)
            
            # Then click on the Maker option
            maker_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//ul[contains(@id, 'yaxisVar_items')]/li[text()='Maker']"))
            )
            maker_option.click()
            time.sleep(1.5)  # Wait for dropdown selection to take effect
            print("Successfully selected Maker")
        except Exception as e:
            print(f"Error selecting Y-axis: {e}")
            # Try alternative method
            js_script = "document.querySelector('#yaxisVar_label').click(); setTimeout(function() { document.querySelector(\"li[data-label='Maker']\").click(); }, 800);"
            driver.execute_script(js_script)
            time.sleep(1.5)
            print("Tried alternative method for Y-axis selection")
        
        # Find and select X-axis (Month Wise)
        print("Selecting 'Month Wise' from X-axis dropdown...")
        try:
            # First, click to open the dropdown
            x_axis_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "xaxisVar"))
            )
            x_axis_element.click()
            time.sleep(0.8)
            
            # Then click on the Month Wise option
            month_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//ul[contains(@id, 'xaxisVar_items')]/li[text()='Month Wise']"))
            )
            month_option.click()
            time.sleep(1.5)  # Wait for dropdown selection to take effect
            print("Successfully selected Month Wise")
        except Exception as e:
            print(f"Error selecting X-axis: {e}")
            # Try alternative method
            js_script = "document.querySelector('#xaxisVar_label').click(); setTimeout(function() { document.querySelector(\"li[data-label='Month Wise']\").click(); }, 800);"
            driver.execute_script(js_script)
            time.sleep(1.5)
            print("Tried alternative method for X-axis selection")
        
        # Find all elements with j_idt in their IDs
        print("Scanning for j_idt elements...")
        time.sleep(1)  # Wait for all elements to be loaded
        
        # Process for state dropdown
        state_dropdown_j_idt = None
        refresh_button_j_idt = None
        excel_img_j_idt = None
        
        # Look for state dropdown
        print("Searching for state dropdown...")
        state_dropdowns = driver.find_elements(By.XPATH, "//label[contains(@id, 'j_idt') and contains(@class, 'ui-selectonemenu-label') and contains(text(), 'All Vahan4 Running States')]")
        if state_dropdowns:
            state_dropdown_id = state_dropdowns[0].get_attribute("id")
            state_dropdown_j_idt = extract_j_idt_from_id(state_dropdown_id)
            print(f"Found state dropdown: {state_dropdown_id} -> {state_dropdown_j_idt}")
        else:
            print("State dropdown not found by label text, searching by position...")
            # Try finding by looking at all select elements
            selects = driver.find_elements(By.XPATH, "//div[contains(@class, 'ui-selectonemenu')]")
            if len(selects) >= 3:  # Assuming the 3rd dropdown is the state
                state_dropdown_id = selects[2].get_attribute("id")
                state_dropdown_j_idt = extract_j_idt_from_id(state_dropdown_id)
                print(f"Found state dropdown by position: {state_dropdown_id} -> {state_dropdown_j_idt}")
            else:
                print("Could not locate state dropdown reliably")
        
        # Look for refresh button
        print("Searching for refresh button...")
        refresh_buttons = driver.find_elements(By.XPATH, "//button[contains(@id, 'j_idt') and .//span[text()='Refresh']]")
        if refresh_buttons:
            refresh_button_id = refresh_buttons[0].get_attribute("id")
            refresh_button_j_idt = extract_j_idt_from_id(refresh_button_id)
            print(f"Found refresh button: {refresh_button_id} -> {refresh_button_j_idt}")
            
            # Click the refresh button
            print("Clicking refresh button...")
            refresh_buttons[0].click()
            time.sleep(3)  # Longer wait for refresh to complete
        else:
            print("Refresh button not found by text, searching by icon...")
            # Try finding by refresh icon
            refresh_icons = driver.find_elements(By.XPATH, "//button[contains(@id, 'j_idt')]/span[contains(@class, 'ui-icon-refresh')]/..")
            if refresh_icons:
                refresh_button_id = refresh_icons[0].get_attribute("id")
                refresh_button_j_idt = extract_j_idt_from_id(refresh_button_id)
                print(f"Found refresh button by icon: {refresh_button_id} -> {refresh_button_j_idt}")
                
                # Click the refresh button
                print("Clicking refresh button...")
                refresh_icons[0].click()
                time.sleep(3)  # Longer wait for refresh to complete
            else:
                print("Could not locate refresh button reliably")
        
        # Wait for data to load after refresh
        print("Waiting for data to load after refresh...")
        time.sleep(5)  # Increased wait time to ensure content loads
        
        # Look for the specific Excel image with the ID you provided
        print("Searching for Excel image with specific ID pattern...")
        
        # Try direct approach with the pattern you mentioned
        excel_img = None
        try:
            # Look specifically for the groupingTable:j_idt pattern you mentioned
            excel_img = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//img[contains(@id, 'groupingTable:j_idt')]"))
            )
            excel_img_id = excel_img.get_attribute("id")
            excel_img_j_idt = extract_j_idt_from_id(excel_img_id)
            print(f"Found Excel image with ID: {excel_img_id}")
        except Exception as e:
            print(f"Could not find Excel image with specific pattern: {e}")
            
            # Fallback approach - look for any images with j_idt in their ID
            print("Trying fallback approaches for Excel image...")
            
            # Approach 1: Fix the syntax in the XPath query
            excel_imgs = driver.find_elements(By.XPATH, "//img[contains(@id, 'j_idt') and (contains(@src, 'csv.png') or contains(@title, 'Excel') or contains(@title, 'EXCEL'))]")
            if excel_imgs:
                excel_img_id = excel_imgs[0].get_attribute("id")
                excel_img_j_idt = extract_j_idt_from_id(excel_img_id)
                print(f"Found Excel image by attributes: {excel_img_id} -> {excel_img_j_idt}")
            else:
                # Approach 2: Try a simpler approach to find all images
                all_imgs = driver.find_elements(By.TAG_NAME, "img")
                print(f"Found {len(all_imgs)} total images on page")
                
                for img in all_imgs:
                    try:
                        img_id = img.get_attribute("id")
                        img_src = img.get_attribute("src") or ""
                        img_title = img.get_attribute("title") or ""
                        
                        # Print info for debugging
                        if img_id and "j_idt" in img_id:
                            print(f"Potential image: {img_id}")
                            print(f"  Src: {img_src}")
                            print(f"  Title: {img_title}")
                            
                            # If it looks like an Excel/CSV image
                            if "csv" in img_src.lower() or "excel" in img_src.lower() or "excel" in img_title.lower() or "csv" in img_title.lower() or "download" in img_title.lower():
                                excel_img_j_idt = extract_j_idt_from_id(img_id)
                                print(f"Found Excel image by scanning all images: {img_id} -> {excel_img_j_idt}")
                                excel_img = img
                                break
                    except Exception as e:
                        print(f"Error processing an image: {e}")
        
        # If we found the Excel image, try to click it
        if excel_img:
            try:
                print(f"Attempting to click Excel image with ID: {excel_img.get_attribute('id')}")
                # Scroll the element into view
                driver.execute_script("arguments[0].scrollIntoView(true);", excel_img)
                time.sleep(1)
                
                # Click the element
                excel_img.click()
                print("Clicked on Excel image successfully")
                time.sleep(3)  # Wait for download to start
            except Exception as e:
                print(f"Error clicking Excel image: {e}")
                # Try using JavaScript click as a fallback
                try:
                    driver.execute_script("arguments[0].click();", excel_img)
                    print("Clicked Excel image using JavaScript")
                    time.sleep(3)
                except Exception as js_e:
                    print(f"JavaScript click also failed: {js_e}")
        
        # Print final results
        print("\nExtracted J_IDT Labels:")
        print(f"State Dropdown: {state_dropdown_j_idt}")
        print(f"Refresh Button: {refresh_button_j_idt}")
        print(f"Excel Image: {excel_img_j_idt}")
        
        # Save screenshots for debugging
        driver.save_screenshot("parivahan_screenshot.png")
        print("Saved screenshot to parivahan_screenshot.png")
        
        # Take HTML snapshot for analysis
        page_source = driver.page_source
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("Saved page source to page_source.html")
        
        # Return the extracted labels
        return {
            "state_dropdown_j_idt": state_dropdown_j_idt,
            "refresh_button_j_idt": refresh_button_j_idt,
            "excel_img_j_idt": excel_img_j_idt
        }
        
    except TimeoutException as e:
        print(f"Timeout error: {str(e)}")
        driver.save_screenshot("error_screenshot.png")
        print("Saved error screenshot to error_screenshot.png")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        driver.save_screenshot("error_screenshot.png")
        print("Saved error screenshot to error_screenshot.png")
    finally:
        # Close the browser
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    j_idt_labels = main()
    
    # Example of how to use these variables in another script
    if j_idt_labels:
        print("\nExample usage in another script:")
        print(f"state_dropdown_j_idt = '{j_idt_labels['state_dropdown_j_idt']}'")
        print(f"refresh_button_j_idt = '{j_idt_labels['refresh_button_j_idt']}'")
        print(f"excel_img_j_idt = '{j_idt_labels['excel_img_j_idt']}'")
