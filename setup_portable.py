"""
Portable ChromeDriver Setup Script
This script ensures the project works on different machines by setting up ChromeDriver
"""
import os
import platform
import sys
import requests
import zipfile
import shutil

def get_chrome_version():
    """Get installed Chrome version"""
    try:
        if platform.system() == "Windows":
            import winreg
            # Try different registry paths
            paths = [
                r"SOFTWARE\Google\Chrome\BLBeacon",
                r"SOFTWARE\Wow6432Node\Google\Chrome\BLBeacon",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
            ]
            
            for path in paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                        version = winreg.QueryValueEx(key, "version")[0]
                        return version.split('.')[0]  # Return major version
                except:
                    continue
        
        elif platform.system() == "Darwin":  # macOS
            import subprocess
            result = subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"], 
                                  capture_output=True, text=True)
            version = result.stdout.split()[-1]
            return version.split('.')[0]
        
        elif platform.system() == "Linux":
            import subprocess
            result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
            version = result.stdout.split()[-1]
            return version.split('.')[0]
            
    except Exception as e:
        print(f"Could not detect Chrome version: {e}")
        return "120"  # Default to a stable version

def download_chromedriver(version="120"):
    """Download appropriate ChromeDriver for the system"""
    
    system = platform.system()
    machine = platform.machine()
    
    # Determine platform string
    if system == "Windows":
        if machine.endswith("64"):
            platform_str = "win64"
        else:
            platform_str = "win32"
        executable_name = "chromedriver.exe"
    elif system == "Darwin":  # macOS
        if machine == "arm64":
            platform_str = "mac-arm64"
        else:
            platform_str = "mac-x64"
        executable_name = "chromedriver"
    elif system == "Linux":
        platform_str = "linux64"
        executable_name = "chromedriver"
    else:
        raise Exception(f"Unsupported platform: {system}")
    
    # ChromeDriver download URL (Chrome for Testing)
    url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}.0.0.0/{platform_str}/chromedriver-{platform_str}.zip"
    
    print(f"🔽 Downloading ChromeDriver for {system} {machine} (Chrome {version})...")
    print(f"📥 URL: {url}")
    
    try:
        # Download the zip file
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Create directory for the specific platform
        driver_dir = f"chromedriver-{platform_str}"
        os.makedirs(driver_dir, exist_ok=True)
        
        # Save and extract
        zip_path = f"{driver_dir}.zip"
        with open(zip_path, "wb") as f:
            f.write(response.content)
        
        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("temp_extract")
        
        # Move the executable to the correct location
        extracted_driver = os.path.join("temp_extract", f"chromedriver-{platform_str}", executable_name)
        target_driver = os.path.join(driver_dir, executable_name)
        
        shutil.move(extracted_driver, target_driver)
        
        # Make executable on Unix systems
        if system != "Windows":
            os.chmod(target_driver, 0o755)
        
        # Cleanup
        os.remove(zip_path)
        shutil.rmtree("temp_extract")
        
        print(f"✅ ChromeDriver installed successfully: {target_driver}")
        return target_driver
        
    except Exception as e:
        print(f"❌ Failed to download ChromeDriver: {e}")
        return None

def setup_portable_chromedriver():
    """Setup portable ChromeDriver for the current system"""
    
    print("🚀 Setting up portable ChromeDriver...")
    print(f"💻 System: {platform.system()} {platform.machine()}")
    
    # Detect Chrome version
    chrome_version = get_chrome_version()
    print(f"🌐 Detected Chrome version: {chrome_version}")
    
    # Check if we already have a driver for this platform
    system = platform.system()
    machine = platform.machine()
    
    if system == "Windows":
        platform_str = "win64" if machine.endswith("64") else "win32"
        executable_name = "chromedriver.exe"
    elif system == "Darwin":
        platform_str = "mac-arm64" if machine == "arm64" else "mac-x64"
        executable_name = "chromedriver"
    else:
        platform_str = "linux64"
        executable_name = "chromedriver"
    
    driver_dir = f"chromedriver-{platform_str}"
    driver_path = os.path.join(driver_dir, executable_name)
    
    if os.path.exists(driver_path):
        print(f"✅ ChromeDriver already exists: {driver_path}")
        return driver_path
    
    # Download ChromeDriver
    return download_chromedriver(chrome_version)

if __name__ == "__main__":
    print("=" * 50)
    print("   PORTABLE CHROMEDRIVER SETUP")
    print("=" * 50)
    
    driver_path = setup_portable_chromedriver()
    
    if driver_path:
        print(f"\n🎉 Setup complete! ChromeDriver is ready at: {driver_path}")
        print("\n📝 To use in your project, the code will automatically detect this driver.")
        print("📦 You can now copy this entire folder to other machines!")
    else:
        print("\n❌ Setup failed. Please check your internet connection and try again.")
        sys.exit(1)