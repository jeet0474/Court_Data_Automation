"""
Court Data Fetcher - Browser Automation
Educational Assignment Project
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import uvicorn
import time
import os
import base64
import requests
import requests
from urllib.parse import urljoin
from captcha_recognizer import recognize_captcha

app = FastAPI(title="Court Data Fetcher", description="eCourts Browser Automation")

# Templates setup
templates = Jinja2Templates(directory="templates")

# Global browser instance
browser = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with start session button"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/start-session")
async def start_session():
    """Start browser session and click Case Status button"""
    global browser
    
    try:
        print("🚀 Starting browser session...")
        
        # Setup Chrome options with download preferences
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")  # Required for headless
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")  # Real user agent
        chrome_options.add_argument("--disable-web-security")  # For CORS issues
        chrome_options.add_argument("--allow-running-insecure-content")  # For mixed content
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Hide automation
        chrome_options.add_experimental_option('useAutomationExtension', False)  # Disable automation extension
        
        # Configure downloads to go to our local downloads folder
        downloads_path = os.path.join(os.getcwd(), "downloads")
        os.makedirs(downloads_path, exist_ok=True)
        
        prefs = {
            "download.default_directory": downloads_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": False,  # Keep PDFs in Chrome viewer
            "plugins.plugins_disabled": [],
            "profile.default_content_settings.popups": 0
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Get correct ChromeDriver path - prioritize local driver for portability
        def get_correct_chromedriver_path():
            try:
                # Determine the correct platform-specific driver path
                import platform
                system = platform.system()
                machine = platform.machine()
                
                if system == "Windows":
                    platform_str = "win64" if machine.endswith("64") else "win32"
                    executable_name = "chromedriver.exe"
                elif system == "Darwin":  # macOS
                    platform_str = "mac-arm64" if machine == "arm64" else "mac-x64"
                    executable_name = "chromedriver"
                else:  # Linux
                    platform_str = "linux64"
                    executable_name = "chromedriver"
                
                # Try platform-specific local driver first
                local_driver_path = os.path.join(os.getcwd(), f"chromedriver-{platform_str}", executable_name)
                if os.path.exists(local_driver_path):
                    print(f"✅ Using platform-specific ChromeDriver: {local_driver_path}")
                    return local_driver_path
                
                # Fallback to win64 driver if on Windows (legacy support)
                if system == "Windows":
                    legacy_driver_path = os.path.join(os.getcwd(), "chromedriver-win64", "chromedriver.exe")
                    if os.path.exists(legacy_driver_path):
                        print(f"✅ Using legacy ChromeDriver: {legacy_driver_path}")
                        return legacy_driver_path
                
                print("⚠️ Local ChromeDriver not found!")
                print("📋 Please run: python setup_portable.py")
                raise Exception("No ChromeDriver found. Run setup_portable.py to download one.")
            except Exception as e:
                print(f"Error getting ChromeDriver path: {e}")
                return None
        
        # Create browser instance with correct path
        correct_driver_path = get_correct_chromedriver_path()
        if not correct_driver_path:
            raise Exception("Could not find ChromeDriver executable")
        
        print(f"Using ChromeDriver: {correct_driver_path}")
        service = Service(correct_driver_path)
        browser = webdriver.Chrome(service=service, options=chrome_options)
        
        # Hide automation indicators for headless compatibility
        browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("📱 Navigating to eCourts portal...")
        browser.get("https://services.ecourts.gov.in/ecourtindia_v6/")
        
        # Wait for page to load
        time.sleep(5)
        
        print("🔍 Looking for Case Status button...")
        print(f"📄 Current page title: {browser.title}")
        print(f"🌐 Current URL: {browser.current_url}")
        
        # Debug: Check if page has loaded properly
        try:
            body_text = browser.find_element(By.TAG_NAME, "body").text[:200]
            print(f"📝 Page content preview: {body_text}...")
        except:
            print("⚠️ Could not read page content")
        
        # Try multiple selectors for Case Status button based on actual HTML
        case_status_selectors = [
            "//a[@id='leftPaneMenuCS']",  # Specific ID from your HTML
            "//a[contains(@href, 'casestatus/index')]",  # Based on href
            "//a[contains(text(), 'Case Status')]",  # Text content
            "//li[@class='nav-item']//a[contains(text(), 'Case Status')]",  # Within nav-item
            "#leftPaneMenuCS",  # CSS selector for ID
            "a[href*='casestatus']",  # CSS selector for href
            "//a[contains(@class, 'nav-link') and contains(text(), 'Case Status')]"  # Class + text
        ]
        
        case_status_button = None
        for selector in case_status_selectors:
            try:
                # Check if it's a CSS selector (starts with # or doesn't start with //)
                if selector.startswith('#') or (not selector.startswith('//')):
                    case_status_button = browser.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Found Case Status button with CSS selector: {selector}")
                else:
                    case_status_button = browser.find_element(By.XPATH, selector)
                    print(f"✅ Found Case Status button with XPath selector: {selector}")
                break
            except Exception as e:
                print(f"❌ Selector failed: {selector} - {str(e)}")
                continue
        
        if case_status_button:
            print("🖱️ Clicking Case Status button...")
            browser.execute_script("arguments[0].click();", case_status_button)
            time.sleep(3)
            print("✅ Case Status button clicked successfully!")
            
            # Handle modal popup that appears after clicking Case Status
            print("🔍 Looking for modal popup to close...")
            
            # Wait a bit for modal to appear
            time.sleep(2)
            
            # Try multiple selectors for the close button in modal
            close_button_selectors = [
                "//button[@class='btn-close']",  # Based on your HTML
                "//button[@data-bs-dismiss='modal']",  # Bootstrap modal close
                "//button[contains(@onclick, 'closeModel')]",  # Based on onclick function
                "//button[@aria-label='Close']",  # Accessibility label
                ".btn-close",  # CSS selector
                "button[data-bs-dismiss='modal']",  # CSS selector
                "//div[@class='modal-header']//button",  # Any button in modal header
                "//button[contains(@class, 'btn-close')]"  # Partial class match
            ]
            
            modal_closed = False
            for selector in close_button_selectors:
                try:
                    # Check if it's a CSS selector
                    if selector.startswith('.') or (not selector.startswith('//')):
                        close_button = browser.find_element(By.CSS_SELECTOR, selector)
                        print(f"✅ Found close button with CSS selector: {selector}")
                    else:
                        close_button = browser.find_element(By.XPATH, selector)
                        print(f"✅ Found close button with XPath selector: {selector}")
                    
                    print("🖱️ Clicking modal close button...")
                    browser.execute_script("arguments[0].click();", close_button)
                    time.sleep(2)
                    print("✅ Modal closed successfully!")
                    modal_closed = True
                    break
                except Exception as e:
                    print(f"❌ Close button selector failed: {selector} - {str(e)}")
                    continue
            
            if not modal_closed:
                print("⚠️ Could not find modal close button, trying ESC key...")
                try:
                    from selenium.webdriver.common.keys import Keys
                    browser.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(1)
                    print("✅ Modal closed with ESC key")
                    modal_closed = True
                except Exception as e:
                    print(f"❌ ESC key failed: {str(e)}")
            
            current_url = browser.current_url
            page_title = browser.title
            
            return JSONResponse({
                "success": True,
                "message": f"Case Status clicked and modal {'closed' if modal_closed else 'handling attempted'}!",
                "current_url": current_url,
                "page_title": page_title
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Could not find Case Status button on the page",
                "page_title": browser.title,
                "current_url": browser.current_url
            })
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Failed to start session: {str(e)}"
        })

@app.post("/get-states")
async def get_states():
    """Get all available states from the form"""
    global browser
    
    if not browser:
        return JSONResponse({
            "success": False,
            "error": "No active browser session. Please start session first."
        })
    
    try:
        print("🔍 Extracting states from dropdown...")
        
        # Find the state dropdown
        state_selectors = [
            "//select[@id='sess_state_code']",
            "//select[@name='sess_state_code']",
            "#sess_state_code",
            "select[name='sess_state_code']"
        ]
        
        state_dropdown = None
        for selector in state_selectors:
            try:
                if selector.startswith('#') or (not selector.startswith('//')):
                    state_dropdown = browser.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Found state dropdown with CSS: {selector}")
                else:
                    state_dropdown = browser.find_element(By.XPATH, selector)
                    print(f"✅ Found state dropdown with XPath: {selector}")
                break
            except Exception as e:
                print(f"❌ State selector failed: {selector} - {str(e)}")
                continue
        
        if not state_dropdown:
            return JSONResponse({
                "success": False,
                "error": "Could not find state dropdown"
            })
        
        # Extract all state options
        from selenium.webdriver.support.ui import Select
        select = Select(state_dropdown)
        options = select.options
        
        states = []
        for option in options:
            value = option.get_attribute("value")
            text = option.text.strip()
            if value and value != "0":  # Skip "Select state" option
                states.append({
                    "value": value,
                    "text": text
                })
        
        print(f"✅ Found {len(states)} states")
        return JSONResponse({
            "success": True,
            "states": states,
            "message": f"Found {len(states)} states available"
        })
        
    except Exception as e:
        print(f"❌ Error getting states: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Failed to get states: {str(e)}"
        })

@app.post("/select-state")
async def select_state(request: Request):
    """Select a state and get districts"""
    global browser
    
    if not browser:
        return JSONResponse({
            "success": False,
            "error": "No active browser session"
        })
    
    try:
        # Get state value from request
        form_data = await request.form()
        state_value = form_data.get("state_value")
        
        if not state_value:
            return JSONResponse({
                "success": False,
                "error": "State value is required"
            })
        
        print(f"🔽 Selecting state: {state_value}")
        
        # Find and select state
        state_dropdown = browser.find_element(By.ID, "sess_state_code")
        from selenium.webdriver.support.ui import Select
        select = Select(state_dropdown)
        select.select_by_value(state_value)
        
        # Wait for districts to load
        time.sleep(3)
        
        # Get districts
        districts = await get_districts_internal()
        
        return JSONResponse({
            "success": True,
            "message": f"State selected: {state_value}",
            "districts": districts
        })
        
    except Exception as e:
        print(f"❌ Error selecting state: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Failed to select state: {str(e)}"
        })

@app.post("/select-district")
async def select_district(request: Request):
    """Select a district and get court complexes"""
    global browser
    
    if not browser:
        return JSONResponse({
            "success": False,
            "error": "No active browser session"
        })
    
    try:
        # Get district value from request
        form_data = await request.form()
        district_value = form_data.get("district_value")
        
        if not district_value:
            return JSONResponse({
                "success": False,
                "error": "District value is required"
            })
        
        print(f"🔽 Selecting district: {district_value}")
        
        # Find and select district
        district_dropdown = browser.find_element(By.ID, "sess_dist_code")
        from selenium.webdriver.support.ui import Select
        select = Select(district_dropdown)
        select.select_by_value(district_value)
        
        # Wait for court complexes to load
        time.sleep(3)
        
        # Get court complexes
        courts = await get_courts_internal()
        
        return JSONResponse({
            "success": True,
            "message": f"District selected: {district_value}",
            "courts": courts
        })
        
    except Exception as e:
        print(f"❌ Error selecting district: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Failed to select district: {str(e)}"
        })

@app.post("/select-court")
async def select_court(request: Request):
    """Select a court complex"""
    global browser
    
    if not browser:
        return JSONResponse({
            "success": False,
            "error": "No active browser session"
        })
    
    try:
        # Get court value from request
        form_data = await request.form()
        court_value = form_data.get("court_value")
        
        if not court_value:
            return JSONResponse({
                "success": False,
                "error": "Court value is required"
            })
        
        print(f"🔽 Selecting court complex: {court_value}")
        
        # Find and select court complex
        court_dropdown = browser.find_element(By.ID, "court_complex_code")
        from selenium.webdriver.support.ui import Select
        select = Select(court_dropdown)
        select.select_by_value(court_value)
        
        # Wait for selection to process
        time.sleep(2)
        
        return JSONResponse({
            "success": True,
            "message": f"Court complex selected: {court_value}",
            "ready_for_search": True
        })
        
    except Exception as e:
        print(f"❌ Error selecting court: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Failed to select court: {str(e)}"
        })

@app.post("/click-case-number")
async def click_case_number():
    """Click the Case Number tab button"""
    global browser
    
    if not browser:
        return JSONResponse({
            "success": False,
            "error": "No active browser session"
        })
    
    try:
        print("🔢 Clicking Case Number tab...")
        
        # Wait for and click the Case Number tab button
        case_number_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.ID, "casenumber-tabMenu"))
        )
        
        # Click the Case Number button
        case_number_button.click()
        print("✅ Case Number tab clicked successfully")
        
        # Wait a moment for the tab to load
        time.sleep(2)
        
        return JSONResponse({
            "success": True,
            "message": "Case Number tab clicked successfully"
        })
        
    except Exception as e:
        print(f"❌ Error clicking Case Number tab: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Failed to click Case Number tab: {str(e)}"
        })

@app.post("/get-case-types")
async def get_case_types():
    """Get case types from the dropdown"""
    global browser
    
    if not browser:
        return JSONResponse({
            "success": False,
            "error": "No active browser session"
        })
    
    try:
        print("📋 Fetching case types from dropdown...")
        
        # Wait for case type dropdown to be present
        case_type_dropdown = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "case_type"))
        )
        
        # Extract all case type options
        from selenium.webdriver.support.ui import Select
        select = Select(case_type_dropdown)
        options = select.options
        
        case_types = []
        for option in options:
            value = option.get_attribute("value")
            text = option.text.strip()
            if value and value != "":  # Skip "Select Case Type" option
                case_types.append({
                    "value": value,
                    "text": text
                })
        
        print(f"✅ Found {len(case_types)} case types")
        
        return JSONResponse({
            "success": True,
            "case_types": case_types,
            "count": len(case_types)
        })
        
    except Exception as e:
        print(f"❌ Error fetching case types: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Failed to fetch case types: {str(e)}"
        })

@app.post("/fetch-captcha")
async def fetch_captcha():
    """Fetch the captcha image by taking a screenshot of the captcha element"""
    global browser
    
    if not browser:
        return JSONResponse({
            "success": False,
            "error": "No active browser session"
        })
    
    try:
        print("🖼️ Fetching captcha image from eCourts page via screenshot...")
        
        # For headless mode: ensure page is fully rendered
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        browser.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Wait for captcha image to be present and visible
        captcha_img = WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.ID, "captcha_image"))
        )
        
        # Scroll to captcha for better capture
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", captcha_img)
        time.sleep(2)  # Extra wait for image loading
        
        # Get the captcha image source URL for debugging
        captcha_src = captcha_img.get_attribute("src")
        print(f"📷 Captcha image URL: {captcha_src}")
        
        # Take a screenshot of just the captcha element
        captcha_screenshot = captcha_img.screenshot_as_base64
        captcha_data_url = f"data:image/png;base64,{captcha_screenshot}"
        
        print("✅ Captcha image captured via screenshot")
        
        return JSONResponse({
            "success": True,
            "captcha_url": captcha_data_url,
            "original_url": captcha_src,
            "message": "Captcha image captured successfully"
        })
        
    except Exception as e:
        print(f"❌ Error fetching captcha: {str(e)}")
        
        # Fallback: Try the old method with session cookies
        try:
            print("� Trying fallback method with session cookies...")
            
            captcha_img = browser.find_element(By.ID, "captcha_image")
            captcha_src = captcha_img.get_attribute("src")
            
            # Convert relative URL to absolute URL if needed
            if captcha_src.startswith("/"):
                current_url = browser.current_url
                captcha_src = urljoin(current_url, captcha_src)
            
            # Get cookies from selenium browser
            selenium_cookies = browser.get_cookies()
            requests_cookies = {}
            for cookie in selenium_cookies:
                requests_cookies[cookie['name']] = cookie['value']
            
            # Add headers to mimic the browser
            headers = {
                'User-Agent': browser.execute_script("return navigator.userAgent;"),
                'Referer': browser.current_url,
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(captcha_src, cookies=requests_cookies, headers=headers, timeout=10)
            
            if response.status_code == 200:
                captcha_base64 = base64.b64encode(response.content).decode('utf-8')
                captcha_data_url = f"data:image/png;base64,{captcha_base64}"
                
                print("✅ Captcha image fetched via fallback method")
                
                return JSONResponse({
                    "success": True,
                    "captcha_url": captcha_data_url,
                    "original_url": captcha_src,
                    "message": "Captcha image fetched via fallback method"
                })
            else:
                return JSONResponse({
                    "success": False,
                    "error": f"Failed to fetch captcha: HTTP {response.status_code}"
                })
                
        except Exception as fallback_error:
            print(f"❌ Fallback method also failed: {str(fallback_error)}")
            return JSONResponse({
                "success": False,
                "error": f"Failed to fetch captcha: {str(e)} | Fallback: {str(fallback_error)}"
            })

@app.post("/refresh-captcha")
async def refresh_captcha():
    """Refresh the captcha image on the eCourts page and capture via screenshot"""
    global browser
    
    if not browser:
        return JSONResponse({
            "success": False,
            "error": "No active browser session"
        })
    
    try:
        print("🔄 Refreshing captcha image...")
        
        # Find and click the refresh button
        refresh_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@onclick='refreshCaptcha()']"))
        )
        
        # Click the refresh button
        refresh_button.click()
        print("✅ Captcha refresh button clicked")
        
        # Wait a moment for the new captcha to load
        time.sleep(3)
        
        # Now capture the new captcha image via screenshot
        captcha_img = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "captcha_image"))
        )
        
        # Get the new captcha image source URL for debugging
        captcha_src = captcha_img.get_attribute("src")
        print(f"📷 New captcha image URL: {captcha_src}")
        
        # Take screenshot of the captcha element
        captcha_screenshot = captcha_img.screenshot_as_base64
        captcha_data_url = f"data:image/png;base64,{captcha_screenshot}"
        
        print("✅ New captcha image captured via screenshot")
        
        return JSONResponse({
            "success": True,
            "captcha_url": captcha_data_url,
            "original_url": captcha_src,
            "message": "Captcha refreshed and captured successfully"
        })
        
    except Exception as e:
        print(f"❌ Error refreshing captcha: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Failed to refresh captcha: {str(e)}"
        })

@app.post("/submit-case-search")
async def submit_case_search(request: Request):
    """Submit the case search form with case type, case number, year and captcha"""
    global browser
    
    if not browser:
        return JSONResponse({
            "success": False,
            "error": "No active browser session"
        })
    
    try:
        # Get form data
        form_data = await request.form()
        case_type = form_data.get("case_type")
        case_number = form_data.get("case_number")
        case_year = form_data.get("case_year")
        captcha_code = form_data.get("captcha_code")
        
        if not all([case_type, case_number, case_year, captcha_code]):
            return JSONResponse({
                "success": False,
                "error": "Case type, case number, year and captcha are required"
            })
        
        print(f"📝 Submitting case search: Type={case_type}, Number={case_number}, Year={case_year}, Captcha={captcha_code}")
        
        # Select case type
        case_type_dropdown = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "case_type"))
        )
        from selenium.webdriver.support.ui import Select
        select = Select(case_type_dropdown)
        select.select_by_value(case_type)
        
        # Fill case number
        case_number_input = browser.find_element(By.ID, "search_case_no")
        case_number_input.clear()
        case_number_input.send_keys(case_number)
        
        # Fill year
        year_input = browser.find_element(By.ID, "rgyear")
        year_input.clear()
        year_input.send_keys(case_year)
        
        # Fill captcha
        captcha_input = browser.find_element(By.ID, "case_captcha_code")
        captcha_input.clear()
        captcha_input.send_keys(captcha_code)
        
        # Click Go button with improved headless compatibility
        try:
            go_button = browser.find_element(By.XPATH, "//button[@onclick='submitCaseNo();']")
            
            # Scroll to button to ensure it's visible
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", go_button)
            time.sleep(1)
            
            # Wait for button to be clickable
            go_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@onclick='submitCaseNo();']"))
            )
            
            # Use JavaScript click for headless reliability
            browser.execute_script("arguments[0].click();", go_button)
            print("✅ Go button clicked using JavaScript")
            
        except Exception as click_error:
            print(f"⚠️ JavaScript click failed, trying direct click: {click_error}")
            # Fallback to direct click
            go_button = browser.find_element(By.XPATH, "//button[@onclick='submitCaseNo();']")
            go_button.click()
        
        print("✅ Form submitted successfully")
        
        # Wait for response
        time.sleep(3)
        
        # Check for invalid captcha modal
        try:
            # Look for the invalid captcha modal
            invalid_captcha_selectors = [
                "//div[contains(@class, 'alert-danger-cust') and contains(text(), 'Invalid Captcha')]",
                "//div[@class='modal-content']//div[contains(text(), 'Invalid Captcha')]",
                "//div[contains(text(), 'Invalid Captcha')]"
            ]
            
            invalid_captcha_found = False
            for selector in invalid_captcha_selectors:
                try:
                    captcha_error = browser.find_elements(By.XPATH, selector)
                    if captcha_error and captcha_error[0].is_displayed():
                        print("❌ Invalid captcha detected")
                        invalid_captcha_found = True
                        break
                except:
                    continue
            
            if invalid_captcha_found:
                # Close the error modal if it exists
                try:
                    close_selectors = [
                        "//button[@class='btn-close']",
                        "//button[@data-bs-dismiss='modal']",
                        "//button[contains(@onclick, 'closeModel')]"
                    ]
                    
                    for close_selector in close_selectors:
                        try:
                            close_button = browser.find_element(By.XPATH, close_selector)
                            if close_button.is_displayed():
                                browser.execute_script("arguments[0].click();", close_button)
                                print("🚪 Closed invalid captcha modal")
                                time.sleep(1)
                                break
                        except:
                            continue
                except:
                    print("ℹ️ Could not close modal, continuing...")
                
                return JSONResponse({
                    "success": False,
                    "error": "Invalid captcha. Please try again.",
                    "error_type": "invalid_captcha"
                })
        
        except Exception as e:
            print(f"⚠️ Error checking for captcha validation: {str(e)}")
        
        return JSONResponse({
            "success": True,
            "message": "Case search form submitted successfully"
        })
        
    except Exception as e:
        print(f"❌ Error submitting form: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Failed to submit form: {str(e)}"
        })

@app.post("/get-search-results")
async def get_search_results():
    """Get case search results preview from the current page"""
    global browser
    
    try:
        if not browser:
            return JSONResponse({
                "success": False,
                "error": "Browser session not active"
            })
        
        print("🔍 Extracting case search results from current page...")
        
        # Wait a moment for page to fully load
        time.sleep(2)
        
        # Check if results are available
        page_source = browser.page_source
        
        # Look for the results table or error messages
        if "Total number of cases" not in page_source and "dispTable" not in page_source:
            return JSONResponse({
                "success": False,
                "error": "No case search results found on current page"
            })
        
        results = {
            "court_info": "",
            "total_cases": 0,
            "cases": []
        }
        
        # Extract court information and total cases
        try:
            court_info_element = browser.find_element(By.XPATH, "//h3[@class='h2class']")
            results["court_info"] = court_info_element.text.strip()
            print(f"✅ Court Info: {results['court_info']}")
        except:
            results["court_info"] = "Court information not found"
        
        try:
            total_cases_element = browser.find_element(By.XPATH, "//h4[@class='h2class']")
            total_cases_text = total_cases_element.text.strip()
            # Extract number from text like "Total number of cases : 1"
            import re
            match = re.search(r'Total number of cases\s*:\s*(\d+)', total_cases_text)
            if match:
                results["total_cases"] = int(match.group(1))
            print(f"✅ Total Cases: {results['total_cases']}")
        except:
            results["total_cases"] = 0
        
        # Extract case details from table
        try:
            # Look for table rows with case data
            case_rows = browser.find_elements(By.XPATH, "//table[@id='dispTable']//tbody//tr[td[2]]")
            
            for i, row in enumerate(case_rows):
                try:
                    # Skip header rows or court name rows
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        # Check if this is a data row (has sr number)
                        sr_no_text = cells[0].text.strip()
                        if sr_no_text.isdigit():
                            case_data = {
                                "sr_no": int(sr_no_text),
                                "case_type_number": cells[1].text.strip(),
                                "parties": cells[2].text.strip().replace('\n', ' ')
                            }
                            results["cases"].append(case_data)
                            print(f"✅ Case {case_data['sr_no']}: {case_data['case_type_number']}")
                except Exception as e:
                    print(f"⚠️ Error processing row {i}: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"❌ Error extracting case table: {str(e)}")
        
        if results["cases"]:
            print(f"✅ Successfully extracted {len(results['cases'])} case(s)")
            return JSONResponse({
                "success": True,
                "results": results
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "No cases found in search results"
            })
        
    except Exception as e:
        print(f"❌ Error getting search results: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Failed to get search results: {str(e)}"
        })

@app.post("/recognize-captcha")
async def recognize_captcha_endpoint(request: Request):
    """
    Recognize text from captcha image using OCR
    Accepts base64 image data and returns recognized text
    """
    try:
        # Get form data
        form_data = await request.form()
        image_data = form_data.get("image_data")
        
        if not image_data:
            return JSONResponse({
                "success": False,
                "error": "Image data is required"
            })
        
        print("🔍 Starting OCR recognition on captcha image...")
        
        # Debug: Check image data format
        print(f"📊 Image data length: {len(image_data)}")
        print(f"📊 Image data prefix: {image_data[:50] if len(image_data) > 50 else image_data}")
        
        # Call the OCR recognition function
        result = recognize_captcha(image_data, method='base64')
        
        if result["success"]:
            print(f"✅ OCR Recognition successful: '{result['text']}' (confidence: {result['confidence']}%)")
            return JSONResponse({
                "success": True,
                "text": result["text"],
                "confidence": result["confidence"],
                "length": result["length"],
                "message": f"Text recognized with {result['confidence']}% confidence"
            })
        else:
            print(f"❌ OCR Recognition failed: {result.get('error', 'Unknown error')}")
            return JSONResponse({
                "success": False,
                "error": result.get('error', 'OCR recognition failed'),
                "text": "",
                "confidence": 0
            })
            
    except Exception as e:
        print(f"❌ Error in OCR endpoint: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"OCR recognition failed: {str(e)}",
            "text": "",
            "confidence": 0
        })

# Internal helper functions
async def get_districts_internal():
    """Internal function to get districts"""
    global browser
    try:
        district_dropdown = browser.find_element(By.ID, "sess_dist_code")
        from selenium.webdriver.support.ui import Select
        select = Select(district_dropdown)
        options = select.options
        
        districts = []
        for option in options:
            value = option.get_attribute("value")
            text = option.text.strip()
            if value and value != "0":
                districts.append({
                    "value": value,
                    "text": text
                })
        
        return districts
    except Exception as e:
        print(f"❌ Error getting districts: {str(e)}")
        return []

async def get_courts_internal():
    """Internal function to get court complexes"""
    global browser
    try:
        court_dropdown = browser.find_element(By.ID, "court_complex_code")
        from selenium.webdriver.support.ui import Select
        select = Select(court_dropdown)
        options = select.options
        
        courts = []
        for option in options:
            value = option.get_attribute("value")
            text = option.text.strip()
            if value and value != "0":
                courts.append({
                    "value": value,
                    "text": text
                })
        
        return courts
    except Exception as e:
        print(f"❌ Error getting courts: {str(e)}")
        return []

@app.post("/process-case-results")
async def process_case_results():
    global browser
    if not browser:
        return {"success": False, "error": "No active browser session"}
    
    try:
        # Wait for the results table to load
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )
        
        # Find all View buttons/links in the results table - trying multiple selectors
        view_buttons = []
        
        # Try different selectors for View buttons/links
        selectors = [
            "//a[contains(text(), 'View')]",  # Anchor tags with "View" text
            "//a[contains(@onclick, 'viewHistory')]",  # Anchor tags with viewHistory onclick
            "//input[@value='View' and @type='button']",  # Original input buttons
            "//button[contains(text(), 'View')]",  # Button elements with "View" text
            "//td//a[contains(@class, 'someclass')]"  # Anchor tags with someclass
        ]
        
        for selector in selectors:
            try:
                view_buttons = browser.find_elements(By.XPATH, selector)
                if view_buttons:
                    print(f"✅ Found {len(view_buttons)} View elements using selector: {selector}")
                    break
                else:
                    print(f"❌ No elements found with selector: {selector}")
            except Exception as e:
                print(f"❌ Error with selector {selector}: {str(e)}")
                continue
        
        if not view_buttons:
            # Try to get page source for debugging
            try:
                page_source = browser.page_source
                if "View" in page_source:
                    print("⚠️ 'View' text found in page source but no clickable elements found")
                    # Try a more general approach
                    view_buttons = browser.find_elements(By.XPATH, "//*[contains(text(), 'View')]")
                    print(f"🔍 Found {len(view_buttons)} elements containing 'View' text")
            except:
                pass
            
            if not view_buttons:
                return {"success": False, "error": "No case results found. Could not locate View buttons/links."}
        
        all_cases = []
        
        for i, button in enumerate(view_buttons):
            try:
                print(f"🔍 Processing case {i+1} of {len(view_buttons)}")
                
                # Click the View button/link
                browser.execute_script("arguments[0].click();", button)
                print(f"✅ Clicked View button for case {i+1}")
                
                # Wait longer for the detailed page to load completely
                print("⏳ Waiting for case details page to load...")
                time.sleep(5)  # Increased from 3 to 5 seconds
                
                # Wait for specific elements to ensure page is fully loaded
                try:
                    WebDriverWait(browser, 20).until(  # Increased from 15 to 20 seconds
                        EC.any_of(
                            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Case Type')]")),
                            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Filing Number')]")),
                            EC.presence_of_element_located((By.CLASS_NAME, "case_status_table")),
                            EC.presence_of_element_located((By.ID, "main_back_caseNo")),
                            EC.presence_of_element_located((By.XPATH, "//h3[contains(@class, 'h2class')]"))
                        )
                    )
                    print("✅ Case details page loaded successfully")
                except:
                    print("⚠️ Timeout waiting for case details, proceeding anyway...")
                
                # Additional wait to ensure all content is rendered
                time.sleep(3)  # Increased from 2 to 3 seconds
                
                # Debug: Print page title and some content
                try:
                    page_title = browser.title
                    print(f"📄 Current page title: {page_title}")
                    
                    # Try to find some key elements to confirm we're on the right page
                    case_elements = browser.find_elements(By.XPATH, "//h3[contains(@class, 'h2class')]")
                    if case_elements:
                        print(f"🔍 Found {len(case_elements)} section headers")
                        for i, elem in enumerate(case_elements[:3]):  # Show first 3
                            print(f"   {i+1}. {elem.text[:50]}...")
                    
                    # Check for tables
                    tables = browser.find_elements(By.TAG_NAME, "table")
                    print(f"📊 Found {len(tables)} tables on the page")
                    
                except Exception as debug_error:
                    print(f"⚠️ Debug info extraction failed: {str(debug_error)}")
                
                # Extract case data from the detailed view
                print("📊 Extracting case data...")
                case_data = extract_case_details()
                case_data["case_index"] = i + 1
                all_cases.append(case_data)
                print(f"✅ Extracted data for case {i+1}")
                
                # Log extracted data summary
                non_empty_fields = [k for k, v in case_data.items() if v and v != "Not found" and v != []]
                print(f"📈 Successfully extracted {len(non_empty_fields)} fields with data")
                
                # Use the specific back button instead of browser.back()
                try:
                    print("🔙 Looking for Back button...")
                    back_button = browser.find_element(By.ID, "main_back_caseNo")
                    browser.execute_script("arguments[0].click();", back_button)
                    print("✅ Clicked Back button")
                except Exception as back_error:
                    print(f"⚠️ Back button not found, using browser.back(): {str(back_error)}")
                    browser.back()
                
                # Wait for results page to reload
                time.sleep(3)
                
                # Wait for results table to be present again
                try:
                    WebDriverWait(browser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
                    )
                    print("✅ Back to results page")
                except:
                    print("⚠️ Timeout waiting for results page")
                
                # Re-find the view buttons as the page has reloaded
                # Use the same selector that worked initially
                for selector in selectors:
                    try:
                        view_buttons = browser.find_elements(By.XPATH, selector)
                        if view_buttons:
                            print(f"✅ Re-found {len(view_buttons)} View buttons")
                            break
                    except:
                        continue
                
            except Exception as e:
                print(f"❌ Error processing case {i+1}: {str(e)}")
                # Try to go back if we're stuck
                try:
                    print("🔄 Attempting recovery...")
                    # Try the specific back button first
                    try:
                        back_button = browser.find_element(By.ID, "main_back_caseNo")
                        browser.execute_script("arguments[0].click();", back_button)
                        print("✅ Used Back button for recovery")
                    except:
                        browser.back()
                        print("✅ Used browser.back() for recovery")
                    
                    time.sleep(3)
                    
                    # Re-find view buttons
                    for selector in selectors:
                        try:
                            view_buttons = browser.find_elements(By.XPATH, selector)
                            if view_buttons:
                                break
                        except:
                            continue
                except Exception as recovery_error:
                    print(f"❌ Recovery failed: {str(recovery_error)}")
                continue
        
        return {
            "success": True,
            "message": f"Processed {len(all_cases)} cases successfully",
            "cases": all_cases
        }
        
    except Exception as e:
        return {"success": False, "error": f"Error processing case results: {str(e)}"}

def extract_case_details():
    """Extract detailed case information from the current page"""
    try:
        case_data = {}
        print("📋 Starting case data extraction...")
        
        # Extract basic case information with multiple fallback selectors
        try:
            # Try multiple ways to find case type
            case_type_selectors = [
                "//td[contains(text(), 'Case Type')]/following-sibling::td",
                "//td[text()='Case Type']/following-sibling::td",
                "//label[contains(text(), 'Case Type')]/following-sibling::td",
                "//td[contains(@class, 'fw-bold') and contains(text(), 'HINDU MARRIAGE ACT')]"
            ]
            case_type = None
            for selector in case_type_selectors:
                try:
                    element = browser.find_element(By.XPATH, selector)
                    case_type = element.text.strip()
                    if case_type:
                        break
                except:
                    continue
            case_data["case_type"] = case_type or "Not found"
            print(f"✅ Case Type: {case_data['case_type']}")
        except Exception as e:
            case_data["case_type"] = "Not found"
            print(f"❌ Case Type extraction failed: {str(e)}")
        
        # Extract filing number
        try:
            filing_selectors = [
                "//td[contains(text(), 'Filing Number')]/following-sibling::td",
                "//label[contains(text(), 'Filing Number')]/following-sibling::td",
                "//td[contains(@class, 'fw-bold') and contains(text(), '/2025')]"
            ]
            filing_number = None
            for selector in filing_selectors:
                try:
                    element = browser.find_element(By.XPATH, selector)
                    filing_number = element.text.strip()
                    if filing_number and filing_number != "Not found":
                        break
                except:
                    continue
            case_data["filing_number"] = filing_number or "Not found"
            print(f"✅ Filing Number: {case_data['filing_number']}")
        except:
            case_data["filing_number"] = "Not found"
        
        # Extract filing date (it's in the same row as filing number but different column)
        try:
            filing_date_selectors = [
                "//td[contains(text(), 'Filing Date')]/following-sibling::td",
                "//label[contains(text(), 'Filing Date')]/parent::td/following-sibling::td",
                "//tr[td[contains(text(), 'Filing Number')]]//td[contains(text(), '07-07-2025') or contains(text(), '-07-2025') or contains(text(), '2025')]",
                "//tr[td[label[contains(text(), 'Filing Number')]]]//td[4]"  # 4th column in the same row
            ]
            filing_date = None
            for selector in filing_date_selectors:
                try:
                    element = browser.find_element(By.XPATH, selector)
                    filing_date = element.text.strip()
                    if filing_date and filing_date != "Not found" and "2025" in filing_date:
                        break
                except:
                    continue
            case_data["filing_date"] = filing_date or "Not found"
            print(f"✅ Filing Date: {case_data['filing_date']}")
        except:
            case_data["filing_date"] = "Not found"
        
        # Extract registration number
        try:
            reg_selectors = [
                "//td[contains(text(), 'Registration Number')]/following-sibling::td",
                "//label[contains(text(), 'Registration Number')]/parent::td/following-sibling::td",
                "//tr[td[contains(text(), 'Registration Number')]]//td[2]",  # 2nd column
                "//label[contains(text(), '133/2025')]/parent::td"
            ]
            reg_number = None
            for selector in reg_selectors:
                try:
                    element = browser.find_element(By.XPATH, selector)
                    reg_number = element.text.strip()
                    if reg_number and reg_number != "Not found" and "/" in reg_number:
                        break
                except:
                    continue
            case_data["registration_number"] = reg_number or "Not found"
            print(f"✅ Registration Number: {case_data['registration_number']}")
        except:
            case_data["registration_number"] = "Not found"
        
        # Extract registration date
        try:
            reg_date_selectors = [
                "//td[contains(text(), 'Registration Date')]/following-sibling::td",
                "//label[contains(text(), 'Registration Date')]/parent::td/following-sibling::td",
                "//tr[td[contains(text(), 'Registration Number')]]//td[4]",  # 4th column in same row
                "//label[contains(text(), 'Registration Date:')]/parent::td/following-sibling::td"
            ]
            reg_date = None
            for selector in reg_date_selectors:
                try:
                    element = browser.find_element(By.XPATH, selector)
                    reg_date = element.text.strip()
                    if reg_date and reg_date != "Not found" and "2025" in reg_date:
                        break
                except:
                    continue
            case_data["registration_date"] = reg_date or "Not found"
            print(f"✅ Registration Date: {case_data['registration_date']}")
        except:
            case_data["registration_date"] = "Not found"
        
        # Extract CNR number
        try:
            cnr_selectors = [
                "//td[contains(text(), 'CNR Number')]/following-sibling::td//span",
                "//label[contains(text(), 'CNR Number')]/following-sibling::td//span",
                "//span[contains(@class, 'fw-bold') and contains(@class, 'text-danger')]"
            ]
            cnr_number = None
            for selector in cnr_selectors:
                try:
                    element = browser.find_element(By.XPATH, selector)
                    cnr_number = element.text.strip()
                    if cnr_number and cnr_number != "Not found":
                        break
                except:
                    continue
            case_data["cnr_number"] = cnr_number or "Not found"
            print(f"✅ CNR Number: {case_data['cnr_number']}")
        except:
            case_data["cnr_number"] = "Not found"
        
        # Extract case status information from case_status_table
        try:
            first_hearing_selectors = [
                "//table[contains(@class, 'case_status_table')]//td[contains(text(), 'First Hearing Date')]/following-sibling::td",
                "//td[contains(text(), 'First Hearing Date')]/following-sibling::td",
                "//label[contains(text(), 'First Hearing Date')]/parent::td/following-sibling::td",
                "//table[contains(@class, 'case_status_table')]//td[contains(text(), '18th July') or contains(text(), 'July 2025')]"
            ]
            first_hearing = None
            for selector in first_hearing_selectors:
                try:
                    element = browser.find_element(By.XPATH, selector)
                    first_hearing = element.text.strip()
                    if first_hearing and first_hearing != "Not found":
                        break
                except:
                    continue
            case_data["first_hearing_date"] = first_hearing or "Not found"
            print(f"✅ First Hearing Date: {case_data['first_hearing_date']}")
        except:
            case_data["first_hearing_date"] = "Not found"
        
        try:
            next_hearing_selectors = [
                "//table[contains(@class, 'case_status_table')]//td[contains(text(), 'Next Hearing Date')]/following-sibling::td",
                "//strong[contains(text(), 'Next Hearing Date')]/parent::label/parent::td/following-sibling::td",
                "//label[strong[contains(text(), 'Next Hearing Date')]]/parent::td/following-sibling::td",
                "//table[contains(@class, 'case_status_table')]//strong[contains(text(), '10th November') or contains(text(), 'November 2025')]/parent::td"
            ]
            next_hearing = None
            for selector in next_hearing_selectors:
                try:
                    element = browser.find_element(By.XPATH, selector)
                    next_hearing = element.text.strip()
                    if next_hearing and next_hearing != "Not found":
                        break
                except:
                    continue
            case_data["next_hearing_date"] = next_hearing or "Not found"
            print(f"✅ Next Hearing Date: {case_data['next_hearing_date']}")
        except:
            case_data["next_hearing_date"] = "Not found"
        
        try:
            stage_selectors = [
                "//table[contains(@class, 'case_status_table')]//td[contains(text(), 'Case Stage')]/following-sibling::td",
                "//strong[contains(text(), 'Case Stage')]/parent::label/parent::td/following-sibling::td",
                "//label[strong[contains(text(), 'Case Stage')]]/parent::td/following-sibling::td",
                "//table[contains(@class, 'case_status_table')]//strong[contains(text(), 'Service')]/parent::label/parent::td"
            ]
            case_stage = None
            for selector in stage_selectors:
                try:
                    element = browser.find_element(By.XPATH, selector)
                    case_stage = element.text.strip()
                    if case_stage and case_stage != "Not found":
                        break
                except:
                    continue
            case_data["case_stage"] = case_stage or "Not found"
            print(f"✅ Case Stage: {case_data['case_stage']}")
        except:
            case_data["case_stage"] = "Not found"
        
        try:
            court_selectors = [
                "//table[contains(@class, 'case_status_table')]//td[contains(text(), 'Court Number and Judge')]/following-sibling::td",
                "//strong[contains(text(), 'Court Number and Judge')]/parent::label/parent::td/following-sibling::td",
                "//label[strong[contains(text(), 'Court Number and Judge')]]/parent::td/following-sibling::td",
                "//table[contains(@class, 'case_status_table')]//strong[contains(text(), 'District And Sessions Judge')]/parent::label/parent::td"
            ]
            court_judge = None
            for selector in court_selectors:
                try:
                    element = browser.find_element(By.XPATH, selector)
                    court_judge = element.text.strip()
                    if court_judge and court_judge != "Not found":
                        break
                except:
                    continue
            case_data["court_and_judge"] = court_judge or "Not found"
            print(f"✅ Court and Judge: {case_data['court_and_judge']}")
        except:
            case_data["court_and_judge"] = "Not found"
        
        # Extract petitioner information
        try:
            petitioner_selectors = [
                "table.Petitioner_Advocate_table",
                "//h3[contains(text(), 'Petitioner')]/following-sibling::table",
                "//table[contains(@class, 'table-bordered')]//td[contains(text(), 'Ramesh Kumar')]/.."
            ]
            petitioner_text = None
            for selector in petitioner_selectors:
                try:
                    if selector.startswith("//"):
                        element = browser.find_element(By.XPATH, selector)
                    else:
                        element = browser.find_element(By.CSS_SELECTOR, selector)
                    petitioner_text = element.text.strip()
                    if petitioner_text:
                        break
                except:
                    continue
            case_data["petitioner"] = petitioner_text or "Not found"
            print(f"✅ Petitioner: {case_data['petitioner'][:50]}...")
        except:
            case_data["petitioner"] = "Not found"
        
        # Extract respondent information
        try:
            respondent_selectors = [
                "table.Respondent_Advocate_table",
                "//h3[contains(text(), 'Respondent')]/following-sibling::table",
                "//table[contains(@class, 'table-bordered')]//td[contains(text(), 'Sapna')]/.."
            ]
            respondent_text = None
            for selector in respondent_selectors:
                try:
                    if selector.startswith("//"):
                        element = browser.find_element(By.XPATH, selector)
                    else:
                        element = browser.find_element(By.CSS_SELECTOR, selector)
                    respondent_text = element.text.strip()
                    if respondent_text:
                        break
                except:
                    continue
            case_data["respondent"] = respondent_text or "Not found"
            print(f"✅ Respondent: {case_data['respondent']}")
        except:
            case_data["respondent"] = "Not found"
        
        # Extract acts information
        try:
            acts_selectors = [
                "table.acts_table",
                "//h3[contains(text(), 'Acts')]/following-sibling::table",
                "//table[@id='act_table']"
            ]
            acts = []
            for selector in acts_selectors:
                try:
                    if selector.startswith("//"):
                        acts_table = browser.find_element(By.XPATH, selector)
                    else:
                        acts_table = browser.find_element(By.CSS_SELECTOR, selector)
                    
                    acts_rows = acts_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                    for row in acts_rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            acts.append({
                                "act": cells[0].text.strip(),
                                "section": cells[1].text.strip()
                            })
                    if acts:
                        break
                except:
                    continue
            case_data["acts"] = acts
            print(f"✅ Acts: Found {len(acts)} acts")
        except:
            case_data["acts"] = []
        
        # Extract orders and PDF links
        try:
            order_selectors = [
                "table.order_table",
                "//h3[contains(text(), 'Interim Orders')]/following-sibling::table",
                "//table[contains(@class, 'table')]//td[contains(text(), 'Order Number')]/../.."
            ]
            orders = []
            for selector in order_selectors:
                try:
                    if selector.startswith("//"):
                        order_table = browser.find_element(By.XPATH, selector)
                    else:
                        order_table = browser.find_element(By.CSS_SELECTOR, selector)
                    
                    order_rows = order_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                    for row in order_rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            # Look for PDF link in the row
                            pdf_link = None
                            try:
                                pdf_element = row.find_element(By.XPATH, ".//a[contains(@onclick, 'displayPdf')]")
                                onclick_attr = pdf_element.get_attribute("onclick")
                                # Extract the filename from onclick attribute
                                if "filename=" in onclick_attr:
                                    filename_start = onclick_attr.find("filename=") + 9
                                    filename_end = onclick_attr.find("&", filename_start)
                                    if filename_end == -1:
                                        filename_end = onclick_attr.find("'", filename_start)
                                    pdf_link = onclick_attr[filename_start:filename_end]
                            except:
                                pass
                            
                            orders.append({
                                "order_number": cells[0].text.strip(),
                                "order_date": cells[1].text.strip(),
                                "order_details": cells[2].text.strip(),
                                "pdf_link": pdf_link
                            })
                    if orders:
                        break
                except:
                    continue
            case_data["orders"] = orders
            print(f"✅ Orders: Found {len(orders)} orders")
        except:
            case_data["orders"] = []
        
        # Extract case history
        try:
            history_selectors = [
                "table.history_table",
                "//h2[contains(text(), 'Case History')]/following-sibling::table",
                "//table[contains(@class, 'history_table')]"
            ]
            history = []
            for selector in history_selectors:
                try:
                    if selector.startswith("//"):
                        history_table = browser.find_element(By.XPATH, selector)
                    else:
                        history_table = browser.find_element(By.CSS_SELECTOR, selector)
                    
                    history_rows = history_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                    for row in history_rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 4:
                            history.append({
                                "judge": cells[0].text.strip(),
                                "business_date": cells[1].text.strip(),
                                "hearing_date": cells[2].text.strip(),
                                "purpose": cells[3].text.strip()
                            })
                    if history:
                        break
                except:
                    continue
            case_data["case_history"] = history
            print(f"✅ Case History: Found {len(history)} entries")
        except:
            case_data["case_history"] = []
        
        print(f"📊 Case data extraction completed. Found {len(case_data)} fields")
        return case_data
        
    except Exception as e:
        print(f"❌ Error extracting case details: {str(e)}")
        return {"error": f"Error extracting case details: {str(e)}"}

@app.get("/debug-page")
async def debug_page():
    global browser
    if not browser:
        return {"success": False, "error": "No active browser session"}
    
    try:
        # Get current page info
        current_url = browser.current_url
        page_title = browser.title
        
        # Look for View elements
        view_elements = []
        selectors_to_try = [
            ("Anchor with 'View' text", "//a[contains(text(), 'View')]"),
            ("Anchor with viewHistory", "//a[contains(@onclick, 'viewHistory')]"),
            ("Input buttons", "//input[@value='View' and @type='button']"),
            ("Button with 'View'", "//button[contains(text(), 'View')]"),
            ("Links with someclass", "//td//a[contains(@class, 'someclass')]"),
            ("Any element with 'View'", "//*[contains(text(), 'View')]")
        ]
        
        for desc, selector in selectors_to_try:
            try:
                elements = browser.find_elements(By.XPATH, selector)
                view_elements.append({
                    "description": desc,
                    "selector": selector,
                    "count": len(elements),
                    "elements": [{"tag": elem.tag_name, "text": elem.text[:50], "onclick": elem.get_attribute("onclick")} for elem in elements[:3]]
                })
            except Exception as e:
                view_elements.append({
                    "description": desc,
                    "selector": selector,
                    "count": 0,
                    "error": str(e)
                })
        
        # Check if we can find the case results table
        tables = browser.find_elements(By.TAG_NAME, "table")
        table_info = []
        for i, table in enumerate(tables):
            try:
                table_info.append({
                    "index": i,
                    "id": table.get_attribute("id"),
                    "class": table.get_attribute("class"),
                    "text_preview": table.text[:200] if table.text else "No text"
                })
            except:
                table_info.append({"index": i, "error": "Could not get table info"})
        
        return {
            "success": True,
            "current_url": current_url,
            "page_title": page_title,
            "view_elements": view_elements,
            "tables_found": len(tables),
            "table_info": table_info
        }
        
    except Exception as e:
        return {"success": False, "error": f"Debug error: {str(e)}"}

@app.get("/download-pdf/{case_index}/{order_number}")
async def download_pdf(case_index: int, order_number: str):
    global browser
    if not browser:
        return {"success": False, "error": "No active browser session"}
    
    try:
        print(f"🔍 Looking for PDF link for order {order_number}")
        
        # Find the PDF link
        pdf_selectors = [
            f"//tr[td[text()='{order_number}' or contains(text(), '{order_number}')]]//a[contains(@onclick, 'displayPdf')]",
            f"//td[text()='{order_number}' or contains(text(), '{order_number}')]/following-sibling::td//a[contains(@onclick, 'displayPdf')]",
            "//a[contains(@onclick, 'displayPdf')]"  # Fallback to get any PDF link
        ]
        
        pdf_link = None
        onclick_attr = None
        
        for selector in pdf_selectors:
            try:
                elements = browser.find_elements(By.XPATH, selector)
                if elements:
                    # For the order number provided, try to get the nth element
                    try:
                        order_index = int(order_number) - 1
                        if 0 <= order_index < len(elements):
                            pdf_link = elements[order_index]
                            onclick_attr = pdf_link.get_attribute("onclick")
                        else:
                            pdf_link = elements[0]
                            onclick_attr = pdf_link.get_attribute("onclick")
                    except:
                        pdf_link = elements[0]
                        onclick_attr = pdf_link.get_attribute("onclick")
                    
                    if pdf_link and onclick_attr:
                        break
            except Exception as e:
                continue
        
        if not pdf_link or not onclick_attr:
            return {"success": False, "error": f"PDF link not found for order {order_number}"}
        
        print(f"✅ Found PDF link with onclick: {onclick_attr}")
        
        # Click the PDF link to open the modal
        browser.execute_script("arguments[0].click();", pdf_link)
        print("🖱️ Clicked PDF link, waiting for modal...")
        
        # Wait for modal to appear
        time.sleep(3)
        
        # Look for the modal with PDF viewer
        modal_selectors = [
            "//div[@class='modal-body']//object[@data]",
            "//div[@id='modal_order_body']//object[@data]",
            "//object[@data and contains(@data, '.pdf')]",
            "//object[@data]"
        ]
        
        pdf_object = None
        pdf_url = None
        
        for selector in modal_selectors:
            try:
                elements = browser.find_elements(By.XPATH, selector)
                if elements:
                    pdf_object = elements[0]
                    pdf_url = pdf_object.get_attribute("data")
                    if pdf_url:
                        print(f"✅ Found PDF object with data: {pdf_url}")
                        break
            except Exception as e:
                continue
        
        if not pdf_url:
            print("❌ Could not find PDF object in modal, trying original approach...")
            # Fall back to original Chrome PDF viewer approach
        else:
            # Close the modal if there's a close button
            try:
                close_selectors = [
                    "//button[@class='btn-close']",
                    "//button[@data-bs-dismiss='modal']",
                    "//button[@aria-label='Close']",
                    "//div[@class='modal-header']//button"
                ]
                
                for close_selector in close_selectors:
                    try:
                        close_button = browser.find_element(By.XPATH, close_selector)
                        if close_button:
                            browser.execute_script("arguments[0].click();", close_button)
                            print("🚪 Closed PDF modal")
                            time.sleep(1)
                            break
                    except:
                        continue
            except:
                print("ℹ️ No close button found or already closed")
            
            # Construct full URL if it's relative
            if pdf_url.startswith('reports/') or not pdf_url.startswith('http'):
                current_url = browser.current_url
                if '?' in current_url:
                    base_url = current_url.split('?')[0]
                else:
                    base_url = current_url
                
                if not base_url.endswith('/'):
                    parts = base_url.split('/')
                    if '.' in parts[-1]:
                        base_url = '/'.join(parts[:-1]) + '/'
                    else:
                        base_url += '/'
                
                pdf_url = base_url + pdf_url.lstrip('/')
            
            print(f"🔗 Full PDF URL: {pdf_url}")
            
            # Try to download directly from modal URL
            import requests
            from pathlib import Path
            
            cookies = browser.get_cookies()
            session_cookies = {}
            for cookie in cookies:
                session_cookies[cookie['name']] = cookie['value']
            
            headers = {
                'User-Agent': browser.execute_script("return navigator.userAgent;"),
                'Accept': 'application/pdf,application/octet-stream,*/*',
                'Referer': browser.current_url,
            }
            
            print("📥 Downloading PDF from modal...")
            response = requests.get(pdf_url, cookies=session_cookies, headers=headers, stream=True, timeout=30)
            
            if response.status_code == 200:
                downloads_dir = Path(os.getcwd()) / "downloads"
                downloads_dir.mkdir(exist_ok=True)
                
                url_filename = pdf_url.split('/')[-1]
                if '.pdf' not in url_filename:
                    url_filename = f"{url_filename}.pdf"
                
                case_info = f"Case_{case_index}_Order_{order_number}"
                safe_filename = f"{case_info}_{url_filename}"
                file_path = downloads_dir / safe_filename
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✅ PDF saved to: {file_path}")
                
                # Check if it's a valid PDF
                with open(file_path, 'rb') as f:
                    first_bytes = f.read(4)
                    if first_bytes == b'%PDF':
                        print("✅ Confirmed: File is a valid PDF")
                        download_url = f"/serve-pdf/{safe_filename}"
                        return {
                            "success": True,
                            "message": f"PDF downloaded successfully from modal",
                            "filename": safe_filename,
                            "download_url": download_url,
                            "local_path": str(file_path),
                            "action": "ready_for_download"
                        }
                    else:
                        print(f"⚠️ File doesn't appear to be a PDF. First bytes: {first_bytes}")
        
        # Store current window and get initial downloads count
        original_window = browser.current_window_handle
        downloads_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Get initial file count in downloads directory
        initial_files = set(os.listdir(downloads_dir))
        
        # Click the PDF link to open it in Chrome's PDF viewer
        print("🖱️ Clicking PDF link to open in Chrome PDF viewer...")
        browser.execute_script("arguments[0].click();", pdf_link)
        
        # Wait for PDF to load (either new tab or navigation)
        time.sleep(3)
        
        # Check if new window/tab opened
        all_windows = browser.window_handles
        pdf_window = None
        
        if len(all_windows) > 1:
            # New tab opened, switch to it
            for window in all_windows:
                if window != original_window:
                    browser.switch_to.window(window)
                    pdf_window = window
                    break
        else:
            # PDF opened in same tab
            pdf_window = original_window
        
        current_url = browser.current_url
        print(f"� PDF opened at: {current_url}")
        
        # Wait for PDF viewer to fully load
        time.sleep(2)
        
        # Try to find and click the download button in Chrome's PDF viewer
        print("🔍 Looking for download button in Chrome PDF viewer...")
        
        # Multiple strategies to find the download button
        download_button_selectors = [
            "//cr-icon-button[@id='download']",  # Chrome PDF viewer download button
            "//button[@id='download']",
            "//cr-icon-button[@aria-label='Download']",
            "//button[@aria-label='Download']",
            "//cr-icon-button[contains(@class, 'download')]",
            "//button[contains(@class, 'download')]",
            "//*[@role='button' and contains(@aria-label, 'Download')]",
            "//*[contains(@id, 'download')]",
            "//cr-toolbar//cr-icon-button[4]",  # Often the 4th button in toolbar
        ]
        
        download_clicked = False
        
        for selector in download_button_selectors:
            try:
                print(f"Trying selector: {selector}")
                download_elements = browser.find_elements(By.XPATH, selector)
                
                if download_elements:
                    for element in download_elements:
                        try:
                            # Check if element is visible and clickable
                            if element.is_displayed() and element.is_enabled():
                                print(f"✅ Found download button, clicking...")
                                browser.execute_script("arguments[0].click();", element)
                                download_clicked = True
                                break
                        except Exception as e:
                            print(f"Failed to click element: {e}")
                            continue
                
                if download_clicked:
                    break
                    
            except Exception as e:
                print(f"Selector failed: {selector} - {e}")
                continue
        
        if not download_clicked:
            # Fallback: try keyboard shortcut Ctrl+S
            print("📥 Trying keyboard shortcut Ctrl+S to download PDF...")
            try:
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.common.action_chains import ActionChains
                
                actions = ActionChains(browser)
                actions.key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL).perform()
                download_clicked = True
                print("✅ Pressed Ctrl+S")
            except Exception as e:
                print(f"❌ Keyboard shortcut failed: {e}")
        
        if download_clicked:
            print("⏳ Waiting for download to complete...")
            
            # Wait for download to complete (check for new files)
            max_wait = 15  # Wait up to 15 seconds
            wait_count = 0
            
            while wait_count < max_wait:
                time.sleep(1)
                wait_count += 1
                
                current_files = set(os.listdir(downloads_dir))
                new_files = current_files - initial_files
                
                if new_files:
                    # Found new file(s)
                    downloaded_file = list(new_files)[0]  # Get first new file
                    print(f"✅ PDF downloaded: {downloaded_file}")
                    
                    # Close PDF tab and return to original window
                    if pdf_window != original_window:
                        browser.close()
                        browser.switch_to.window(original_window)
                    else:
                        browser.back()  # Go back if same window
                    
                    # Create web-accessible URL for download
                    download_url = f"/serve-pdf/{downloaded_file}"
                    
                    return {
                        "success": True,
                        "message": f"PDF downloaded successfully via Chrome PDF viewer",
                        "filename": downloaded_file,
                        "download_url": download_url,
                        "local_path": os.path.join(downloads_dir, downloaded_file),
                        "action": "downloaded_via_chrome"
                    }
            
            # Download timeout
            print("⏰ Download timeout - file may still be downloading")
            
            # Close PDF tab and return to original window
            if pdf_window != original_window:
                browser.close()
                browser.switch_to.window(original_window)
            else:
                browser.back()
            
            return {
                "success": True,
                "message": f"Download initiated for order {order_number}, but file not detected yet",
                "note": "Check your downloads folder manually",
                "action": "download_initiated"
            }
        else:
            # Could not find download button
            print("❌ Could not find download button in PDF viewer")
            
            # Close PDF tab and return to original window
            if pdf_window != original_window:
                browser.close()
                browser.switch_to.window(original_window)
            else:
                browser.back()
            
            return {
                "success": False,
                "error": f"Could not find download button in Chrome PDF viewer for order {order_number}",
                "note": "PDF opened but automatic download failed"
            }
        
    except Exception as e:
        print(f"❌ PDF processing error: {str(e)}")
        
        # Try to return to original window in case of error
        try:
            browser.switch_to.window(original_window)
        except:
            pass
        
        return {"success": False, "error": f"Error processing PDF request: {str(e)}"}

# Endpoint to serve downloaded PDFs
@app.get("/serve-pdf/{filename}")
async def serve_pdf(filename: str):
    """Serve PDF files from local downloads directory"""
    import os
    from fastapi.responses import FileResponse
    
    # Security check - only allow PDF files and prevent directory traversal
    if not filename.endswith('.pdf') or '..' in filename or '/' in filename or '\\' in filename:
        return {"error": "Invalid filename"}
    
    downloads_dir = os.path.join(os.getcwd(), "downloads")
    file_path = os.path.join(downloads_dir, filename)
    
    if os.path.exists(file_path):
        print(f"📤 Serving PDF: {filename}")
        return FileResponse(
            path=file_path,
            media_type='application/pdf',
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )
    else:
        print(f"❌ PDF file not found: {filename}")
        return {"error": "PDF file not found"}

# Endpoint to list available PDFs
@app.get("/list-pdfs")
async def list_pdfs():
    """List all available PDF files in downloads directory"""
    import os
    from pathlib import Path
    
    downloads_dir = Path(os.getcwd()) / "downloads"
    
    if not downloads_dir.exists():
        return {"pdfs": []}
    
    pdf_files = []
    for file_path in downloads_dir.glob("*.pdf"):
        stat = file_path.stat()
        pdf_files.append({
            "filename": file_path.name,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "download_url": f"/serve-pdf/{file_path.name}"
        })
    
    # Sort by creation time (newest first)
    pdf_files.sort(key=lambda x: x['created'], reverse=True)
    
    return {"pdfs": pdf_files}

@app.post("/stop-session")
async def stop_session():
    """Stop browser session"""
    global browser
    
    try:
        if browser:
            browser.quit()
            browser = None
            print("🛑 Browser session stopped")
            return JSONResponse({"success": True, "message": "Session stopped"})
        else:
            return JSONResponse({"success": False, "error": "No active session"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.get("/cleanup-session")
async def cleanup_session():
    """Cleanup browser session (can be called on page unload)"""
    global browser
    
    try:
        if browser:
            print("🧹 Cleaning up browser session due to page unload...")
            browser.quit()
            browser = None
            print("✅ Browser session cleaned up successfully")
            return JSONResponse({"success": True, "message": "Session cleaned up"})
        else:
            return JSONResponse({"success": True, "message": "No active session to cleanup"})
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        return JSONResponse({"success": True, "message": f"Cleanup attempted: {str(e)}"})

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when FastAPI application shuts down"""
    global browser
    
    try:
        if browser:
            print("🔄 Application shutdown - cleaning up browser...")
            browser.quit()
            browser = None
            print("✅ Browser cleaned up on application shutdown")
    except Exception as e:
        print(f"⚠️ Error during application shutdown cleanup: {str(e)}")

if __name__ == "__main__":
    print("🏛️ Starting eCourts Browser Automation...")
    print("📍 Application will be available at: http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)