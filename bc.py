from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import requests


def download_sogc_data(uid="CHE-236.101.881", output_format="csv", download_dir=None):
    """
    Download data from Swiss Official Gazette of Commerce (SOGC) for a specific UID

    Args:
        uid (str): UID number to search for (default: CHE-236.101.881)
        output_format (str): Format to download - "pdf", "word", "xml", or "csv"
        download_dir (str): Directory to save downloaded files
    """
    # Set up download directory
    if download_dir is None:
        download_dir = os.path.join(os.getcwd(), "sogc_downloads")

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")

    # Enable performance logging to capture network requests
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,  # Don't open PDFs in browser
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Initialize the WebDriver with WebDriverManager for automatic driver management
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )

    # Create ActionChains instance
    actions = ActionChains(driver)

    try:
        print(f"Searching for UID: {uid}")

        # Navigate to SOGC search page
        driver.get("https://www.shab.ch/#!/search/publications")

        # Take screenshot for debugging
        driver.save_screenshot(os.path.join(download_dir, "initial_page.png"))

        # Wait for page to fully load
        print("Waiting for page to load completely...")
        time.sleep(15)  # Longer wait for Angular to initialize

        # Take screenshot after initial wait
        driver.save_screenshot(os.path.join(download_dir, "after_initial_wait.png"))

        # Using JavaScript to interact with the page
        try:
            # Ensure "No restrictions" is selected for period
            print("Setting 'No restrictions' for period...")
            driver.execute_script("""
                // Find all radio inputs for period
                var radioButtons = document.querySelectorAll('input[type="radio"][name="period"]');
                // Select the "No restrictions" option (usually the first one)
                if (radioButtons.length > 0) {
                    radioButtons[0].checked = true;
                    // Trigger change event
                    var event = new Event('change', { bubbles: true });
                    radioButtons[0].dispatchEvent(event);
                }
            """)

            # Attempt to enter and submit UID using multiple approaches
            uid_entered = False

            # Approach 1: Try with Selenium and ActionChains for reliable keyboard events
            print("Attempting to enter UID with ActionChains...")
            try:
                # Find UID input field
                uid_input = None
                selectors_to_try = [
                    "//input[@name='uid' or contains(@placeholder, 'UID')]",
                    "//label[contains(text(), 'UID')]/following-sibling::input",
                    "//div[contains(text(), 'UID')]/following::input",
                ]

                for selector in selectors_to_try:
                    try:
                        uid_input = driver.find_element(By.XPATH, selector)
                        print(f"Found UID input field with selector: {selector}")
                        break
                    except NoSuchElementException:
                        continue

                if uid_input:
                    # Clear the field
                    uid_input.clear()

                    # Click into the field to ensure it's focused
                    uid_input.click()
                    time.sleep(1)

                    # Type the UID character by character (slower and more reliable)
                    for char in uid:
                        actions.send_keys(char)
                        actions.pause(0.1)  # Short pause between characters
                    actions.perform()
                    print(f"Entered UID: {uid}")

                    # Take screenshot after entering UID
                    driver.save_screenshot(
                        os.path.join(download_dir, "after_uid_entry_1.png")
                    )

                    # Try multiple methods to trigger the search (since Enter key seems problematic)
                    search_triggered = False

                    # Method 1: Direct Enter key on the input field itself
                    try:
                        print(
                            "Method 1: Sending Enter key directly to input element..."
                        )
                        uid_input.send_keys(Keys.ENTER)
                        time.sleep(2)
                        driver.save_screenshot(
                            os.path.join(download_dir, "after_direct_enter.png")
                        )
                        search_triggered = True
                    except Exception as e:
                        print(f"Method 1 failed: {e}")

                    # Method 2: ActionChains Enter key
                    if not search_triggered:
                        try:
                            print("Method 2: Pressing Enter with ActionChains...")
                            # Focus the input field again to be sure
                            uid_input.click()
                            time.sleep(0.5)

                            # Try with a new ActionChains instance
                            new_actions = ActionChains(driver)
                            new_actions.send_keys(Keys.ENTER)
                            new_actions.perform()
                            time.sleep(2)
                            driver.save_screenshot(
                                os.path.join(
                                    download_dir, "after_action_chains_enter.png"
                                )
                            )
                            search_triggered = True
                        except Exception as e:
                            print(f"Method 2 failed: {e}")

                    # Method 3: Try to find and click a search button
                    if not search_triggered:
                        try:
                            print("Method 3: Looking for search button...")
                            search_button_selectors = [
                                "//button[contains(@class, 'search') or contains(@class, 'btn-primary')]",
                                "//button[contains(text(), 'Search') or contains(text(), 'Suche') or contains(text(), 'Recherche')]",
                                "//input[@type='submit']",
                                "//button[@type='submit']",
                            ]

                            for selector in search_button_selectors:
                                try:
                                    search_buttons = driver.find_elements(
                                        By.XPATH, selector
                                    )
                                    if search_buttons:
                                        print(
                                            f"Found search button with selector: {selector}"
                                        )
                                        search_buttons[0].click()
                                        time.sleep(2)
                                        driver.save_screenshot(
                                            os.path.join(
                                                download_dir,
                                                "after_search_button_click.png",
                                            )
                                        )
                                        search_triggered = True
                                        break
                                except:
                                    continue
                        except Exception as e:
                            print(f"Method 3 failed: {e}")

                    # Method 4: Use JavaScript to submit the form or click search
                    if not search_triggered:
                        try:
                            print(
                                "Method 4: Using JavaScript to submit form or click search..."
                            )
                            js_search_result = driver.execute_script("""
                                // Get the active element (which should be our input)
                                var input = document.activeElement;
                                
                                // Try to find the closest form and submit it
                                var form = input.closest('form');
                                if (form) {
                                    form.submit();
                                    return "Form submitted";
                                }
                                
                                // If no form, try to find and click a search button
                                var searchBtn = document.querySelector('button[type="submit"]') || 
                                                document.querySelector('input[type="submit"]') ||
                                                document.querySelector('button.search-btn') || 
                                                document.querySelector('button.btn-primary');
                                                
                                if (searchBtn) {
                                    searchBtn.click();
                                    return "Search button clicked";
                                }
                                
                                // Last resort: trigger Enter key event on the input
                                var enterEvent = new KeyboardEvent('keydown', {
                                    'key': 'Enter',
                                    'code': 'Enter',
                                    'keyCode': 13,
                                    'which': 13,
                                    'bubbles': true,
                                    'cancelable': true
                                });
                                input.dispatchEvent(enterEvent);
                                
                                return "Enter key simulated with JavaScript";
                            """)
                            print(f"JavaScript search result: {js_search_result}")
                            time.sleep(2)
                            driver.save_screenshot(
                                os.path.join(download_dir, "after_js_search.png")
                            )
                            search_triggered = True
                        except Exception as e:
                            print(f"Method 4 failed: {e}")

                    uid_entered = search_triggered

                    if search_triggered:
                        print("Search successfully triggered using one of the methods")
                    else:
                        print("WARNING: All search trigger methods failed")

                    # Take screenshot after pressing Enter
                    driver.save_screenshot(
                        os.path.join(download_dir, "after_enter_attempts.png")
                    )
            except Exception as e:
                print(f"Error with ActionChains approach: {e}")

            # Approach 2: Use JavaScript to enter UID and trigger form submission if first approach failed
            if not uid_entered:
                print("Attempting to enter UID and submit with JavaScript...")
                uid_script_result = driver.execute_script(
                    """
                    // Try to find the UID input
                    var uidInput = document.querySelector('input[name="uid"]');
                    if (!uidInput) {
                        var inputs = document.querySelectorAll('input');
                        for (var i = 0; i < inputs.length; i++) {
                            if (inputs[i].name && inputs[i].name.toLowerCase().includes('uid') || 
                                inputs[i].placeholder && inputs[i].placeholder.toLowerCase().includes('uid')) {
                                uidInput = inputs[i];
                                break;
                            }
                        }
                    }
                    
                    if (uidInput) {
                        // Set the value
                        uidInput.value = arguments[0];
                        
                        // Trigger input event
                        var inputEvent = new Event('input', { bubbles: true });
                        uidInput.dispatchEvent(inputEvent);
                        
                        // Trigger change event
                        var changeEvent = new Event('change', { bubbles: true });
                        uidInput.dispatchEvent(changeEvent);
                        
                        // Find the closest form and submit it
                        var form = uidInput.closest('form');
                        if (form) {
                            form.submit();
                            return "Form submitted";
                        }
                        
                        // If no form, try to find and click a search button
                        var searchBtn = document.querySelector('button.search-btn') || 
                                        document.querySelector('button.btn-primary') ||
                                        document.querySelector('button[type="submit"]');
                        if (searchBtn) {
                            searchBtn.click();
                            return "Search button clicked";
                        }
                        
                        // If no search button, try to simulate Enter key
                        var keyEvent = new KeyboardEvent('keydown', {
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true
                        });
                        uidInput.dispatchEvent(keyEvent);
                        
                        return "Entered UID and simulated Enter key";
                    }
                    
                    return "UID input not found";
                """,
                    uid,
                )

                print(f"JavaScript result: {uid_script_result}")

                # Take screenshot after JavaScript approach
                driver.save_screenshot(
                    os.path.join(download_dir, "after_js_approach.png")
                )

            # Wait for search results to load
            print("Waiting for search results to load...")
            time.sleep(10)

            # Take screenshot of search results
            driver.save_screenshot(os.path.join(download_dir, "search_results.png"))

            # Get the cookies from the current session to use with requests later
            selenium_cookies = driver.get_cookies()
            cookies_dict = {
                cookie["name"]: cookie["value"] for cookie in selenium_cookies
            }

            # Look for the "Actions" dropdown button and click it
            print("Looking for 'Actions' dropdown button...")
            actions_button_found = False

            # Method 1: Try with Selenium
            try:
                # Try multiple selectors for the Actions button
                actions_selectors = [
                    "//button[contains(text(), 'Actions')]",
                    "//button[@id='actionsDropdown']",
                    "//button[contains(@class, 'actions')]",
                    "//div[contains(@class, 'actions')]/button",
                ]

                for selector in actions_selectors:
                    try:
                        actions_button = driver.find_element(By.XPATH, selector)
                        print(f"Found Actions button with selector: {selector}")
                        actions_button.click()
                        print("Clicked Actions button")
                        actions_button_found = True
                        time.sleep(2)  # Wait for dropdown to appear
                        break
                    except NoSuchElementException:
                        continue
            except Exception as e:
                print(f"Error finding Actions button with Selenium: {e}")

            # If Selenium approach failed, try JavaScript
            if not actions_button_found:
                print("Using JavaScript to find and click Actions button...")
                actions_button_script_result = driver.execute_script("""
                    // Try to find the Actions button
                    var actionsButton = null;
                    
                    // Check button text
                    var buttons = Array.from(document.querySelectorAll('button'));
                    for (var i = 0; i < buttons.length; i++) {
                        if (buttons[i].textContent.includes('Actions')) {
                            actionsButton = buttons[i];
                            break;
                        }
                    }
                    
                    // Check by class name if not found by text
                    if (!actionsButton) {
                        actionsButton = document.querySelector('.actions button') || 
                                       document.querySelector('button.actions') ||
                                       document.querySelector('[id*="action"]');
                    }
                    
                    if (actionsButton) {
                        actionsButton.click();
                        return true;
                    } else {
                        return false;
                    }
                """)

                if actions_button_script_result:
                    print("Successfully clicked Actions button using JavaScript")
                    actions_button_found = True
                    time.sleep(2)  # Wait for dropdown to appear
                else:
                    print("Failed to find Actions button with JavaScript")

            # Take screenshot after clicking Actions button
            driver.save_screenshot(
                os.path.join(download_dir, "after_actions_click.png")
            )

            # Capture all visible links in the dropdown
            print("Capturing all visible links after clicking Actions...")
            all_visible_links = driver.find_elements(By.TAG_NAME, "a")

            for i, link in enumerate(all_visible_links):
                try:
                    text = link.text.strip()
                    href = link.get_attribute("href") or "No href"
                    print(f"Link {i + 1}: Text='{text}', href='{href}'")
                except:
                    print(f"Link {i + 1}: [Error reading properties]")

            # Look specifically for CSV download link
            csv_link_url = None
            csv_link_element = None

            for link in all_visible_links:
                try:
                    text = link.text.strip()
                    href = link.get_attribute("href") or ""

                    if "csv" in text.lower() or "csv" in href.lower():
                        print(f"Found CSV link: Text='{text}', href='{href}'")
                        csv_link_url = href
                        csv_link_element = link
                        break
                except:
                    continue

            # If CSV link found, try to download it
            if csv_link_url and csv_link_element:
                print(f"Found CSV download link: {csv_link_url}")

                # Method 1: Try clicking the link with Selenium
                try:
                    print("Clicking CSV link with Selenium...")
                    # Use ActionChains for more reliable clicking
                    actions.move_to_element(csv_link_element)
                    actions.click()
                    actions.perform()
                    print("Clicked CSV link, waiting for download...")
                    time.sleep(10)
                except Exception as e:
                    print(f"Error clicking CSV link: {e}")

                # Method 2: Try direct download with requests using the link URL
                try:
                    print(
                        f"Attempting direct download with requests from URL: {csv_link_url}"
                    )

                    # Set up headers to mimic the browser
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0.4430.212 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Referer": driver.current_url,
                    }

                    # Get cookies from current session
                    response = requests.get(
                        csv_link_url,
                        headers=headers,
                        cookies=cookies_dict,
                        allow_redirects=True,
                    )

                    if response.status_code == 200:
                        filename = os.path.join(
                            download_dir, f"sogc_uid_{uid}_{int(time.time())}.csv"
                        )
                        with open(filename, "wb") as f:
                            f.write(response.content)
                        print(f"Successfully downloaded CSV to {filename}")
                    else:
                        print(
                            f"Failed to download directly. Status code: {response.status_code}"
                        )
                except Exception as e:
                    print(f"Error during direct download: {e}")
            else:
                print("No CSV download link found")

                # If no CSV link found, try clicking on "Hits as csv file" by text
                try:
                    print("Looking for 'Hits as csv file' option by text content...")
                    csv_selectors = [
                        "//a[contains(text(), 'Hits as csv file')]",
                        "//a[contains(text(), 'csv')]",
                        "//a[contains(@title, 'CSV')]",
                    ]

                    for selector in csv_selectors:
                        try:
                            csv_option = driver.find_element(By.XPATH, selector)
                            print(f"Found CSV option with selector: {selector}")

                            # Use ActionChains for more reliable clicking
                            actions.move_to_element(csv_option)
                            actions.click()
                            actions.perform()

                            print("Clicked CSV option, waiting for download...")
                            time.sleep(10)
                            break
                        except NoSuchElementException:
                            continue
                except Exception as e:
                    print(f"Error clicking CSV option: {e}")

            # Take a screenshot after all download attempts
            driver.save_screenshot(
                os.path.join(download_dir, "after_download_attempts.png")
            )

        except Exception as e:
            print(f"Error during page interaction: {e}")
            driver.save_screenshot(os.path.join(download_dir, "error.png"))

        # Check if any files were downloaded
        all_files = os.listdir(download_dir)

        # Filter by file type
        if output_format.lower() == "pdf":
            target_files = [f for f in all_files if f.endswith(".pdf")]
        elif output_format.lower() == "word" or output_format.lower() == "docx":
            target_files = [
                f for f in all_files if f.endswith(".docx") or f.endswith(".doc")
            ]
        elif output_format.lower() == "csv":
            target_files = [f for f in all_files if f.endswith(".csv")]
        elif output_format.lower() == "xml":
            target_files = [f for f in all_files if f.endswith(".xml")]
        else:
            target_files = [
                f
                for f in all_files
                if f.endswith(".pdf")
                or f.endswith(".docx")
                or f.endswith(".csv")
                or f.endswith(".xml")
            ]

        # Filter for files created during this run (last 2 minutes)
        current_time = time.time()
        recent_files = []
        for file in target_files:
            file_path = os.path.join(download_dir, file)
            if os.path.getctime(file_path) > current_time - 120:  # 2 minutes
                recent_files.append(file)

        if recent_files:
            print(
                f"\nSuccessfully downloaded {len(recent_files)} {output_format.upper()} files:"
            )
            for file in recent_files:
                print(f"- {os.path.join(download_dir, file)}")
        else:
            print(
                f"\nNo new {output_format.upper()} files were downloaded during this run."
            )

    finally:
        # Close the browser
        print("Closing browser...")
        time.sleep(5)  # Extra time for any downloads to complete
        driver.quit()

        print(f"Process completed. Check {download_dir} for downloaded files.")


if __name__ == "__main__":
    # Download data for the hardcoded UID: CHE-236.101.881
    download_sogc_data(uid="CHE-236.101.881", output_format="csv")
