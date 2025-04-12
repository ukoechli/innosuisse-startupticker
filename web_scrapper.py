from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import requests
from selenium.webdriver.common.action_chains import ActionChains


def download_sogc_data(uid="CHE-236.101.881", output_format="pdf", download_dir=None):
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

    # Define wait
    wait = WebDriverWait(
        driver,
        20,
        poll_frequency=1,
        ignored_exceptions=[StaleElementReferenceException],
    )

    try:
        print(f"Searching for UID: {uid}")

        # Navigate to SOGC search page - this initial load is necessary
        driver.get("https://www.shab.ch/#!/search/publications")

        # Wait for page to load by checking for a common element
        print("Waiting for page to load...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//body")))
        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Wait for the search interface to be visible
        try:
            wait.until(
                EC.visibility_of_any_elements_located(
                    (
                        By.XPATH,
                        "//input[@type='text'] | //input[@type='search'] | //form",
                    )
                )
            )
        except TimeoutException:
            print("Search interface didn't load completely, continuing anyway...")

        # Select "No restrictions" for period using JavaScript
        print("Setting 'No restrictions' for period...")
        driver.execute_script("""
            var radioButtons = document.querySelectorAll('input[type="radio"][name="period"]');
            if (radioButtons.length > 0) {
                radioButtons[0].checked = true;
                radioButtons[0].dispatchEvent(new Event('change', { bubbles: true }));
            }
        """)

        # Find the UID input field
        print("Looking for UID input field...")
        uid_input = None

        # Try different methods to find the UID field
        selectors = [
            "//input[@name='uid']",
            "//input[contains(@placeholder, 'UID')]",
            "//input[contains(@id, 'uid')]",
            "//label[contains(text(), 'UID')]/following-sibling::input",
            "//label[contains(., 'UID')]/following-sibling::input",
            "//div[contains(., 'UID')]/descendant::input",
            "//input[contains(@ng-model, 'uid')]",
        ]

        for selector in selectors:
            try:
                print(f"  Trying selector: {selector}")
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"  Found {len(elements)} elements with selector: {selector}")
                    uid_input = elements[0]
                    break
                else:
                    print("  No elements found")
            except Exception as e:
                print(f"  Error with selector {selector}: {e}")

        if not uid_input:
            # Try JavaScript as a last resort to find the field
            print("Trying JavaScript to find UID field...")
            input_found = driver.execute_script("""
                var input = document.querySelector('input[name="uid"]');
                if (!input) {
                    var inputs = document.querySelectorAll('input');
                    console.log("Total inputs found: " + inputs.length);
                    
                    for (var i = 0; i < inputs.length; i++) {
                        var currentInput = inputs[i];
                        var name = currentInput.name || '';
                        var placeholder = currentInput.placeholder || '';
                        var id = currentInput.id || '';
                        
                        console.log("Input #" + (i+1) + ": " + name + ", " + placeholder + ", " + id);
                        
                        if (name.toLowerCase().includes('uid') || 
                            placeholder.toLowerCase().includes('uid') ||
                            id.toLowerCase().includes('uid')) {
                            return { 
                                found: true,
                                index: i,
                                name: name,
                                placeholder: placeholder,
                                id: id
                            };
                        }
                    }
                } else {
                    return { 
                        found: true,
                        index: -1, 
                        name: input.name,
                        placeholder: input.placeholder || '',
                        id: input.id || ''
                    };
                }
                
                // If we get here, nothing was found
                return { found: false };
            """)

            if not input_found:
                print("ERROR: Could not find the UID input field")
                return

        # Clear the UID field and enter the UID
        if uid_input:
            uid_input.clear()
            print(f"Entering UID: {uid}")
            uid_input.send_keys(uid)

            # Press Enter key to trigger search WITHOUT reloading page
            print("Pressing Enter to search...")
            uid_input.send_keys(Keys.ENTER)  # Send Enter directly to input field

            # Wait for search results to appear
            print("Waiting for search results...")
            try:
                # Wait for any indication that results have loaded
                wait.until(
                    lambda d: uid in d.page_source
                    or len(
                        d.find_elements(
                            By.XPATH,
                            "//div[contains(@class, 'hits') or contains(@class, 'result')]",
                        )
                    )
                    > 0
                    or "No hits found" in d.page_source
                )
            except TimeoutException:
                print(
                    "Timed out waiting for search results, trying alternative methods..."
                )

            # Verify that search results are displayed
            try:
                # Look for result indicators
                result_count = driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class, 'hits') or contains(@class, 'result')]",
                )
                if result_count:
                    print("Search results found")
                else:
                    # Try an alternative method to trigger search if direct Enter didn't work
                    print("No results found, trying search button...")
                    search_buttons = driver.find_elements(
                        By.XPATH,
                        "//button[contains(@class, 'search') or contains(text(), 'Search') or contains(text(), 'Suche')]",
                    )

                    if search_buttons:
                        print("Clicking search button...")
                        search_buttons[0].click()
                        # Wait for results after clicking search button
                        try:
                            wait.until(
                                lambda d: uid in d.page_source
                                or len(
                                    d.find_elements(
                                        By.XPATH,
                                        "//div[contains(@class, 'hits') or contains(@class, 'result')]",
                                    )
                                )
                                > 0
                                or "No hits found" in d.page_source
                            )
                        except TimeoutException:
                            print(
                                "Timed out waiting for results after clicking search button"
                            )
                    else:
                        # Try JavaScript approach as last resort
                        print("Using JavaScript to trigger search...")
                        driver.execute_script(
                            """
                            // Try to trigger search via form submission
                            var inputs = document.querySelectorAll('input');
                            for (var i = 0; i < inputs.length; i++) {
                                if (inputs[i].value === arguments[0]) {
                                    var form = inputs[i].closest('form');
                                    if (form) {
                                        form.dispatchEvent(new Event('submit', { bubbles: true }));
                                        return;
                                    }
                                }
                            }
                            
                            // If no form, try to click any search button
                            var buttons = document.querySelectorAll('button');
                            for (var i = 0; i < buttons.length; i++) {
                                if (buttons[i].textContent.includes('Search') || 
                                    buttons[i].textContent.includes('Suche') ||
                                    buttons[i].className.includes('search')) {
                                    buttons[i].click();
                                    return;
                                }
                            }
                        """,
                            uid,
                        )
                        # Wait again after JavaScript search trigger
                        try:
                            wait.until(
                                lambda d: uid in d.page_source
                                or len(
                                    d.find_elements(
                                        By.XPATH,
                                        "//div[contains(@class, 'hits') or contains(@class, 'result')]",
                                    )
                                )
                                > 0
                                or "No hits found" in d.page_source
                            )
                        except TimeoutException:
                            print(
                                "Timed out waiting for results after JavaScript search"
                            )
            except Exception as e:
                print(f"Error checking search results: {e}")

            # Verify UID is in page content or URL
            if uid in driver.current_url or uid in driver.page_source:
                print(f"Page contains search results for UID: {uid}")
            else:
                print("Warning: Page may not contain specific UID search results")

            # Directly look for "Hits as PDF" button
            print("Looking for 'Hits as PDF' button...")
            pdf_found = False

            # Try direct button selection
            try:
                pdf_button_selectors = [
                    "//button[normalize-space(.)='Hits as PDF']",
                    "//button[contains(text(), 'Hits as PDF')]",
                    "//button[text()='Hits as PDF']",
                    "//button[contains(., 'Hits as PDF')]",
                    "//button[contains(@title, 'PDF')]",
                    "//button[contains(@class, 'pdf')]",
                ]

                for selector in pdf_button_selectors:
                    pdf_buttons = driver.find_elements(By.XPATH, selector)
                    if pdf_buttons:
                        print(f"Found PDF button with selector: {selector}")
                        pdf_buttons[0].click()
                        # Wait for a dialog or response after clicking PDF button
                        try:
                            wait.until(
                                lambda d: len(
                                    d.find_elements(
                                        By.XPATH,
                                        "//input[@type='text'] | //div[contains(@class, 'modal')] | //form",
                                    )
                                )
                                > 0
                            )
                        except TimeoutException:
                            print("No dialog appeared after clicking PDF button")
                        pdf_found = True
                        break
            except Exception as e:
                print(f"Error finding PDF button with selectors: {e}")

            # If direct approach fails, try JavaScript with more detailed debugging
            if not pdf_found:
                print("Using JavaScript to find and click PDF button...")
                js_result = driver.execute_script("""
                    // First log all buttons for debugging
                    var allButtons = document.querySelectorAll('button');
                    console.log("Total buttons found: " + allButtons.length);
                    
                    var buttonTexts = [];
                    for (var i = 0; i < allButtons.length; i++) {
                        var btnText = allButtons[i].textContent.trim();
                        buttonTexts.push(btnText);
                        console.log("Button " + i + ": '" + btnText + "'");
                    }
                    
                    // First look for exact match on button text
                    for (var i = 0; i < allButtons.length; i++) {
                        var btnText = allButtons[i].textContent.trim();
                        if (btnText === "Hits as PDF") {
                            console.log("Found exact match PDF button!");
                            allButtons[i].click();
                            return "PDF button clicked: " + btnText;
                        }
                    }
                    
                    // If not found, try partial match
                    for (var i = 0; i < allButtons.length; i++) {
                        var btn = allButtons[i];
                        if (btn.textContent.indexOf("PDF") >= 0) {
                            console.log("Found button with 'PDF' in text: " + btn.textContent);
                            btn.click();
                            return "Button with PDF text clicked: " + btn.textContent;
                        }
                    }
                    
                    // Log what buttons we found for debugging
                    return "No PDF button found. Available buttons: " + JSON.stringify(buttonTexts);
                """)

                print(f"JavaScript PDF button click result: {js_result}")

                # Wait for dialog to appear after JS button click
                try:
                    wait.until(
                        lambda d: len(
                            d.find_elements(
                                By.XPATH,
                                "//input[@type='text'] | //div[contains(@class, 'modal')] | //form",
                            )
                        )
                        > 0
                    )
                    pdf_found = "clicked" in js_result
                except TimeoutException:
                    print("No dialog appeared after JavaScript PDF button click")

                if not pdf_found:
                    # If we still can't find the button, try clicking anything that might be PDF-related
                    print("Trying to find any PDF-related elements...")
                    pdf_elements_js = driver.execute_script("""
                        // Try to find any element that might be related to PDF
                        var allElements = document.querySelectorAll('*');
                        for (var i = 0; i < allElements.length; i++) {
                            var element = allElements[i];
                            var text = element.textContent.trim();
                            var className = element.className || '';
                            var id = element.id || '';
                            
                            if ((text.indexOf('PDF') >= 0 || 
                                className.indexOf('pdf') >= 0 || 
                                id.indexOf('pdf') >= 0) && 
                                element.offsetParent !== null) { // Check if element is visible
                                console.log("Found PDF element: ", text, className, id);
                                
                                // Try to click it if it's clickable
                                if (element.tagName === 'BUTTON' || 
                                    element.tagName === 'A' || 
                                    element.tagName === 'INPUT' || 
                                    element.onclick) {
                                    element.click();
                                    return "Clicked PDF-related element: " + text;
                                }
                                
                                // Otherwise try to find a parent or nearby element that's clickable
                                var parent = element.parentElement;
                                if (parent && 
                                    (parent.tagName === 'BUTTON' || 
                                     parent.tagName === 'A' || 
                                     parent.onclick)) {
                                    parent.click();
                                    return "Clicked parent of PDF element: " + parent.textContent;
                                }
                            }
                        }
                        return "No PDF-related elements found";
                    """)
                    print(f"PDF elements search result: {pdf_elements_js}")

                    # Wait for dialog after final PDF click attempt
                    try:
                        wait.until(
                            lambda d: len(
                                d.find_elements(
                                    By.XPATH,
                                    "//input[@type='text'] | //div[contains(@class, 'modal')] | //form",
                                )
                            )
                            > 0
                        )
                        pdf_found = "Clicked" in pdf_elements_js
                    except TimeoutException:
                        print(
                            "No dialog appeared after final PDF element click attempt"
                        )

            # Handle PDF save dialog if it appears
            if pdf_found:
                print("Looking for PDF save dialog...")
                try:
                    # Wait for the dialog to appear
                    print("Waiting for PDF dialog to appear...")
                    try:
                        wait.until(
                            EC.presence_of_element_located(
                                (
                                    By.XPATH,
                                    "//input[@type='text' and not(@hidden) and not(@style='display: none;')]",
                                )
                            )
                        )
                    except TimeoutException:
                        print(
                            "Timed out waiting for text input dialog, proceeding anyway..."
                        )

                    # Debugging - print all visible input fields to understand dialog structure
                    print("Analyzing dialog structure...")
                    driver.execute_script("""
                        console.log("=== DIALOG ANALYSIS ===");
                        // Print all input elements
                        var inputs = document.querySelectorAll('input');
                        console.log("Found " + inputs.length + " input elements");
                        for (var i = 0; i < inputs.length; i++) {
                            var input = inputs[i];
                            if (input.offsetParent !== null) {
                                console.log("Input #" + i + ": type=" + input.type + 
                                    ", id=" + input.id + 
                                    ", name=" + input.name + 
                                    ", class=" + input.className);
                            }
                        }
                        
                        // Print all button elements
                        var buttons = document.querySelectorAll('button');
                        console.log("Found " + buttons.length + " button elements");
                        for (var i = 0; i < buttons.length; i++) {
                            var button = buttons[i];
                            if (button.offsetParent !== null) {
                                console.log("Button #" + i + ": text=" + button.textContent.trim() + 
                                    ", id=" + button.id + 
                                    ", class=" + button.className);
                            }
                        }
                        
                        // Print modal structure if exists
                        var modals = document.querySelectorAll('.modal, .modal-dialog, [role="dialog"]');
                        console.log("Found " + modals.length + " modal elements");
                        
                        console.log("=== END ANALYSIS ===");
                    """)

                    # Most direct approach - try to fill the input using JavaScript and simulate user interaction
                    print("Attempting to set document name and click button...")
                    success = driver.execute_script("""
                        try {
                            // First find all visible inputs
                            var visibleInputs = Array.from(document.querySelectorAll('input'))
                                .filter(input => input.offsetParent !== null && input.type === 'text');
                            
                            if (visibleInputs.length === 0) {
                                console.log("No visible text inputs found");
                                return "No visible text inputs found";
                            }
                            
                            // Use the first visible text input - likely our document name field
                            var inputField = visibleInputs[0];
                            console.log("Found text input: " + inputField.outerHTML);
                            
                            // Clear it and set value to "aaa"
                            inputField.value = "";
                            inputField.focus();
                            
                            // Simulate typing
                            var event = new Event('input', { bubbles: true });
                            inputField.value = "aaa";
                            inputField.dispatchEvent(event);
                            inputField.dispatchEvent(new Event('change', { bubbles: true }));
                            console.log("Set input value to 'aaa'");
                            
                            // Find the "Hits as PDF" button in modal footer
                            var footers = document.querySelectorAll('.modal-footer');
                            if (footers.length === 0) {
                                console.log("No modal footers found");
                                
                                // Try to find any buttons with the text
                                var allButtons = Array.from(document.querySelectorAll('button'))
                                    .filter(b => b.offsetParent !== null && 
                                            (b.textContent.trim() === 'Hits as PDF' || 
                                             b.classList.contains('btn-primary')));
                                
                                if (allButtons.length > 0) {
                                    console.log("Found button by text: " + allButtons[0].outerHTML);
                                    
                                    // Click with timeout to ensure input is processed
                                    setTimeout(function() {
                                        allButtons[0].click();
                                        console.log("Clicked button");
                                    }, 500);
                                    
                                    return "Found and clicked button by text";
                                }
                                
                                return "Could not find footer or button";
                            }
                            
                            // Find button in footer
                            var pdfButton = null;
                            var buttons = footers[0].querySelectorAll('button');
                            for (var i = 0; i < buttons.length; i++) {
                                var btn = buttons[i];
                                if (btn.textContent.trim() === 'Hits as PDF') {
                                    pdfButton = btn;
                                    break;
                                }
                            }
                            
                            if (!pdfButton) {
                                console.log("No 'Hits as PDF' button found in footer");
                                // Try primary button
                                var primaryButtons = footers[0].querySelectorAll('.btn-primary');
                                if (primaryButtons.length > 0) {
                                    pdfButton = primaryButtons[0];
                                    console.log("Using primary button instead");
                                }
                            }
                            
                            if (pdfButton) {
                                console.log("Found button: " + pdfButton.outerHTML);
                                
                                // Click with timeout to ensure input is processed
                                setTimeout(function() {
                                    pdfButton.click();
                                    console.log("Clicked button");
                                }, 500);
                                
                                return "Input filled and button clicked";
                            }
                            
                            return "Could not find PDF button";
                        } catch (e) {
                            console.error("Error in JavaScript: " + e);
                            return "Error: " + e.message;
                        }
                    """)

                    print(f"JavaScript result: {success}")

                    # Wait for download to start - check for new PDF files
                    print("Waiting for download to start...")
                    download_started = False
                    max_wait = 30  # Maximum wait time in seconds
                    start_time = time.time()

                    while time.time() - start_time < max_wait and not download_started:
                        # Check if any PDF files appear in the download directory
                        pdf_files = [
                            f for f in os.listdir(download_dir) if f.endswith(".pdf")
                        ]
                        recent_pdfs = [
                            f
                            for f in pdf_files
                            if os.path.getctime(os.path.join(download_dir, f))
                            > start_time
                        ]

                        if recent_pdfs:
                            download_started = True
                            print("Download started!")
                            break

                        # Check if there's a .crdownload or .part file indicating download in progress
                        temp_files = [
                            f
                            for f in os.listdir(download_dir)
                            if f.endswith(".crdownload") or f.endswith(".part")
                        ]
                        if temp_files:
                            print("Download in progress...")

                        # Short pause before checking again
                        time.sleep(1)

                    if not download_started:
                        # Fallback approach - try to use direct selenium WebDriver actions
                        print("Fallback method: Using direct WebDriver actions")
                        try:
                            # Try to find any visible text input
                            inputs = driver.find_elements(
                                By.XPATH,
                                "//input[@type='text' and not(@hidden) and not(@style='display: none;')]",
                            )
                            if inputs:
                                # Focus on the element
                                driver.execute_script(
                                    "arguments[0].focus();", inputs[0]
                                )
                                inputs[0].clear()

                                # Send keys with explicit focus
                                inputs[0].send_keys("aaa")
                                print("Entered 'aaa' using direct WebDriver")

                                # Try to find the button
                                btns = driver.find_elements(
                                    By.XPATH,
                                    "//button[contains(text(), 'Hits as PDF')] | //button[contains(@class, 'btn-primary')]",
                                )
                                if btns:
                                    # Use JavaScript to click to avoid intercepted click
                                    driver.execute_script(
                                        "arguments[0].click();", btns[0]
                                    )
                                    print("Clicked button using direct WebDriver")

                                    # Wait for the download to start
                                    start_time = time.time()
                                    while (
                                        time.time() - start_time < max_wait
                                        and not download_started
                                    ):
                                        pdf_files = [
                                            f
                                            for f in os.listdir(download_dir)
                                            if f.endswith(".pdf")
                                        ]
                                        recent_pdfs = [
                                            f
                                            for f in pdf_files
                                            if os.path.getctime(
                                                os.path.join(download_dir, f)
                                            )
                                            > start_time
                                        ]

                                        if recent_pdfs:
                                            download_started = True
                                            print(
                                                "Download started after fallback method!"
                                            )
                                            break

                                        time.sleep(1)
                        except Exception as e:
                            print(f"Fallback method failed: {e}")

                except Exception as e:
                    print(f"Error handling save dialog: {e}")

                # Wait for download to complete by checking for .part or .crdownload files to disappear
                print("Waiting for PDF download to complete...")
                max_wait_time = 60  # Maximum time to wait for download (seconds)
                start_time = time.time()
                download_complete = False

                while (
                    time.time() - start_time < max_wait_time and not download_complete
                ):
                    # Check for temporary download files
                    temp_files = [
                        f
                        for f in os.listdir(download_dir)
                        if f.endswith(".crdownload") or f.endswith(".part")
                    ]

                    if not temp_files:
                        # No temp files means either download completed or hasn't started
                        # Check if any new PDFs appeared since we started
                        pdf_files = [
                            f for f in os.listdir(download_dir) if f.endswith(".pdf")
                        ]
                        recent_pdfs = [
                            f
                            for f in pdf_files
                            if os.path.getctime(os.path.join(download_dir, f))
                            > start_time - max_wait_time
                        ]  # Check for files created after we started this process

                        if recent_pdfs:
                            download_complete = True
                            break

                    # Short pause before checking again
                    time.sleep(1)

                # Final check for downloaded PDFs
                pdf_files = [f for f in os.listdir(download_dir) if f.endswith(".pdf")]
                recent_pdfs = [
                    f
                    for f in pdf_files
                    if os.path.getctime(os.path.join(download_dir, f))
                    > time.time() - max_wait_time
                ]

                if recent_pdfs:
                    print("Successfully downloaded PDF files:")
                    for file in recent_pdfs:
                        print(f"- {file}")

                    # Rename the last downloaded PDF to UID.pdf if it exists
                    if recent_pdfs:
                        latest_pdf = max(
                            recent_pdfs,
                            key=lambda f: os.path.getctime(
                                os.path.join(download_dir, f)
                            ),
                        )
                        target_filename = f"{uid}.pdf"
                        source_path = os.path.join(download_dir, latest_pdf)
                        target_path = os.path.join(download_dir, target_filename)

                        try:
                            os.rename(source_path, target_path)
                            print(f"Renamed '{latest_pdf}' to '{target_filename}'")
                        except Exception as e:
                            print(f"Error renaming PDF file: {e}")
                else:
                    print("No PDF files were downloaded")
            else:
                print("Failed to find and click PDF button")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing browser...")
        driver.quit()
        print(f"Process completed. Check {download_dir} for downloaded files.")


if __name__ == "__main__":
    # Download data for the hardcoded UID: CHE-236.101.881
    download_sogc_data(uid="CHE-215.350.964", output_format="pdf")
