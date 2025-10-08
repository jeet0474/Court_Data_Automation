# Court Data Fetcher & Judgment Downloader

🏛️ **Automated case information retrieval from Indian courts with one-click PDF downloads**

## What it does

- **Search any case** from High Courts & District Courts across India
- **Extract case details** - parties, dates, status, judge info
- **Download PDFs** - judgments and orders automatically
- **Solve captchas** - built-in OCR recognition
- **Works everywhere** - Windows, macOS, Linux

## Quick Start

### Prerequisites
- **Python 3.8+** installed
- **Google Chrome browser** installed
- **Internet connection** (for initial setup)

### Setup & Installation

```bash
# 1. Create virtual environment (recommended)
python -m venv .venv

# 2. Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup ChromeDriver (one-time)
python setup_portable.py

# 5. Run the app
python main.py

# 6. Open browser
# Go to: http://localhost:8000
```

## How to use

1. **Click "Start Session"** → Opens eCourts website
2. **Select location** → State → District → Court
3. **Enter case details** → Case type, number, year
4. **Solve captcha** → OCR helps, manual input available
5. **Get results** → View case data & download PDFs

## Features ✅

### ✅ **Fully Working**
- 🎯 **UI** - Simple form interface
- 🔍 **Data extraction** - All required fields + extras
- 📄 **PDF downloads** - Automated judgment/order retrieval
- 🛡️ **Error handling** - Graceful failure management
- 🤖 **Smart automation** - Captcha solving, retry logic
- 🌐 **Cross-platform** - Portable ChromeDriver system

### ❌ **Missing (Known Limitations)**
- 💾 **Database storage** - No SQLite/Postgres integration
- 📅 **Cause lists** - No daily case list downloading

## Project Structure

```
task1/
├── main.py              # Main app & automation
├── templates/index.html # Web interface  
├── captcha_recognizer.py # OCR for captchas
├── chromedriver-win64/  # Portable browser driver
├── tes_port/           # OCR engine
├── requirements.txt     # Python dependencies
└── downloads/          # PDF storage
```

## Dependencies

The project uses these Python packages (automatically installed via `requirements.txt`):

### **🌐 Web Framework & Server**
- `fastapi` - Modern web framework for APIs
- `uvicorn` - ASGI server for running the app
- `jinja2` - Template engine for HTML rendering
- `python-multipart` - File upload handling

### **🤖 Browser Automation**
- `selenium` - Web browser automation
- `webdriver-manager` - ChromeDriver management (fallback only)

### **🔍 OCR & Image Processing**
- `opencv-python` - Computer vision for image processing
- `pytesseract` - OCR engine wrapper
- `Pillow` - Image manipulation library
- `numpy` - Numerical computing for image arrays

### **📡 Web Scraping & HTTP**
- `beautifulsoup4` - HTML parsing (optional usage)
- `requests` - HTTP requests for downloading PDFs

**Note:** Built-in Python modules (os, sys, time, platform, etc.) are used but don't need installation.

## Technical Details

- **Backend**: FastAPI + Selenium WebDriver
- **Frontend**: HTML + Tailwind CSS + JavaScript  
- **OCR**: Tesseract for captcha recognition
- **Browser**: Chrome with automated control
- **Deployment**: Headless-ready for production

## Troubleshooting

**ChromeDriver issues?**
```bash
python setup_portable.py  # Re-download driver
```

**Captcha not working?**
- Manual entry always available as backup
- OCR assists but doesn't replace human input

**Site not loading?**
- Check internet connection
- eCourts portals may be region-specific

## What You Get

✅ **Case Information**
- Petitioner & Respondent names
- Filing date, hearing dates
- Case status & stage
- Court & judge details
- CNR number, acts, history

✅ **PDF Downloads**
- Judgments & orders
- Automatic detection & download
- Local storage in downloads folder

✅ **Smart Features**
- OCR captcha assistance
- Automatic retry on failures
- Cross-platform compatibility
- Production headless mode

## Assignment Status

| Requirement | Status | Notes |
|-------------|--------|-------|
| UI Form | ✅ Complete | Simple & responsive |
| Data Extraction | ✅ Complete | All fields + extras |
| PDF Downloads | ✅ Complete | Automated system |
| Error Handling | ✅ Complete | Comprehensive coverage |
| Database Storage | ❌ Missing | SQLite/Postgres needed |
| Cause Lists | ❌ Missing | Daily listings feature |

**Overall: ~85% complete** with solid foundation and advanced automation features.

## License

Educational project - use responsibly with eCourts terms of service.