# Automated Testing for IReS Main Menu

This directory contains automated testing scripts for the IReS (Invoice Reconciliation System) main menu functionality using PyAutoGUI.

## Overview

The automated testing suite includes:

1. **test_main_menu.py** - Comprehensive testing with image recognition
2. **test_main_menu_simple.py** - Simplified testing with coordinate-based navigation
3. **TESTING_README.md** - This documentation file

## Prerequisites

### Required Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

Or install PyAutoGUI manually:

```bash
pip install pyautogui==0.9.54
```

### Optional Dependencies

For enhanced text recognition (OCR), install Tesseract:

**Windows:**
1. Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Add Tesseract to your PATH
3. Install pytesseract: `pip install pytesseract`

**macOS:**
```bash
brew install tesseract
pip install pytesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
pip install pytesseract
```

## Running the Tests

### Quick Start

Run the simple test version (recommended for first-time users):

```bash
python test_main_menu_simple.py
```

### Advanced Testing

Run the comprehensive test version:

```bash
python test_main_menu.py
```

## Test Coverage

The automated tests cover the following main menu functionality:

### 1. UI Elements Test
- ✅ Verifies main menu loads correctly
- ✅ Checks for main menu title
- ✅ Tests window responsiveness

### 2. Create New Invoice Button
- ✅ Clicks "Create New Invoice" button
- ✅ Verifies navigation to client type selection page
- ✅ Tests back navigation

### 3. Manage Invoices Button
- ✅ Clicks "Manage Invoices" button
- ✅ Verifies navigation to manage invoices page
- ✅ Tests back navigation

### 4. Manage Clients Button
- ✅ Clicks "Manage Clients" button
- ✅ Verifies navigation to manage clients page
- ✅ Tests back navigation

### 5. Settings Button
- ✅ Clicks "Settings" button
- ✅ Verifies settings dialog opens
- ✅ Tests dialog closing and return to main menu

## Test Output

### Log Files
- `test_main_menu.log` - Detailed test execution log
- `test_screenshot_*.png` - Screenshots taken during testing for debugging

### Console Output
The test runner provides real-time feedback:
```
IReS Main Menu Automated Testing (Simple Version)
==================================================
2024-01-15 10:30:15 - INFO - Starting IReS application...
2024-01-15 10:30:20 - INFO - Application started and focused successfully
2024-01-15 10:30:20 - INFO - Testing main menu UI elements...
2024-01-15 10:30:22 - INFO - Testing 'Create New Invoice' button...
...
```

### Test Results Summary
```
==================================================
TEST RESULTS SUMMARY
==================================================
UI Elements: PASS
Create New Invoice: PASS
Manage Invoices: PASS
Manage Clients: PASS
Settings: PASS

Total Tests: 5
Passed: 5
Failed: 0
Success Rate: 100.0%
🎉 All tests passed!
```

## Troubleshooting

### Common Issues

#### 1. Application Not Starting
**Problem:** Tests fail to start the application
**Solution:** 
- Ensure `main.py` is in the current directory
- Check that all dependencies are installed
- Verify Python environment is correct

#### 2. Window Not Found
**Problem:** Tests can't find the application window
**Solution:**
- Make sure the application window title matches expected value
- Check if window is minimized or behind other windows
- Try running tests with application already open

#### 3. Button Clicks Not Working
**Problem:** Tests can't click buttons
**Solution:**
- Ensure application window is focused and visible
- Check screen resolution and scaling settings
- Try running tests on a clean desktop (no overlapping windows)

#### 4. Navigation Verification Fails
**Problem:** Tests can't verify page navigation
**Solution:**
- Install Tesseract OCR for better text recognition
- Check if page titles match expected values
- Review screenshots for debugging

### Debug Mode

Enable detailed debugging by modifying the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Manual Testing

If automated tests fail, you can manually verify functionality:

1. Start the application: `python main.py`
2. Test each button manually
3. Verify navigation between screens
4. Check that back buttons work correctly

## Configuration

### Test Settings

Modify test behavior by editing these parameters in the test scripts:

```python
# PyAutoGUI settings
pyautogui.FAILSAFE = True  # Move mouse to corner to stop
pyautogui.PAUSE = 1.0      # Pause between actions

# Timeout settings
timeout = 5  # Seconds to wait for elements
```

### Custom Button Positions

If button positions change, update the coordinate mappings:

```python
button_positions = {
    "Create New Invoice": (0, -150),
    "Manage Invoices": (0, -50),
    "Manage Clients": (0, 50),
    "Settings": (0, 150),
}
```

## Best Practices

### Before Running Tests

1. **Close unnecessary applications** to avoid interference
2. **Ensure consistent screen resolution** across test runs
3. **Disable screen savers** and power management
4. **Run tests on a clean desktop** without overlapping windows

### During Test Execution

1. **Don't move the mouse** during test execution
2. **Don't interact with the application** while tests are running
3. **Monitor the test output** for any issues
4. **Use Ctrl+C** to stop tests if needed

### After Test Execution

1. **Review the log file** for detailed results
2. **Check screenshots** if tests failed
3. **Verify application state** after testing
4. **Clean up any test artifacts** if needed

## Continuous Integration

### GitHub Actions

Add this workflow to your repository:

```yaml
name: Automated Testing
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        sudo apt-get install tesseract-ocr
        pip install pytesseract
    - name: Run tests
      run: python test_main_menu_simple.py
```

## Contributing

### Adding New Tests

1. Create a new test method in the tester class
2. Add the test to the `tests` list in `run_all_tests()`
3. Update this documentation
4. Test your changes thoroughly

### Reporting Issues

When reporting test failures:

1. Include the complete log file
2. Attach relevant screenshots
3. Describe your system configuration
4. Provide steps to reproduce the issue

## Support

For issues with the automated testing:

1. Check the troubleshooting section above
2. Review the log files for detailed error messages
3. Try running tests manually to isolate issues
4. Create an issue with detailed information

---

**Note:** Automated testing is designed to complement manual testing, not replace it. Always perform manual verification of critical functionality. 