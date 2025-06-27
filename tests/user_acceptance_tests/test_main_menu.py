#!/usr/bin/env python3
"""
Automated Testing Script for IReS Main Menu
Tests core functionality of the main menu using PyAutoGUI
"""

import pyautogui
import time
import sys
import os
import subprocess
from typing import Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_main_menu.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MainMenuTester:
    def __init__(self):
        self.app_process = None
        self.window_title = "IReS - Designed by Studio i Martinez"
        self.test_results = []
        
        # Configure PyAutoGUI settings
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
        pyautogui.PAUSE = 0.5  # Pause between actions
        
    def start_application(self) -> bool:
        """Start the IReS application"""
        try:
            logger.info("Starting IReS application...")
            self.app_process = subprocess.Popen([sys.executable, "main.py"])
            time.sleep(3)  # Wait for application to start
            
            # Check if window is visible
            if self.find_window():
                logger.info("Application started successfully")
                return True
            else:
                logger.error("Application window not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            return False
    
    def find_window(self) -> bool:
        """Find and focus the application window"""
        try:
            # Try to find the window by title
            window = pyautogui.getWindowsWithTitle(self.window_title)
            if window:
                window[0].activate()
                window[0].maximize()
                time.sleep(1)
                return True
            
            # Fallback: try to find any window with "IReS" in the title
            windows = pyautogui.getAllWindows()
            for window in windows:
                if "IReS" in window.title:
                    window.activate()
                    window.maximize()
                    time.sleep(1)
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error finding window: {e}")
            return False
    
    def take_screenshot(self, name: str):
        """Take a screenshot for debugging"""
        try:
            screenshot = pyautogui.screenshot()
            filename = f"screenshot_{name}_{int(time.time())}.png"
            screenshot.save(filename)
            logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
    
    def click_button_by_text(self, button_text: str, timeout: int = 10) -> bool:
        """Click a button by its text content"""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Try to find the button by text
                button_location = pyautogui.locateOnScreen(
                    f"button_images/{button_text.lower().replace(' ', '_')}.png",
                    confidence=0.8
                )
                
                if button_location:
                    center = pyautogui.center(button_location)
                    pyautogui.click(center)
                    logger.info(f"Clicked button: {button_text}")
                    time.sleep(1)
                    return True
                
                time.sleep(0.5)
            
            logger.warning(f"Button not found: {button_text}")
            return False
            
        except Exception as e:
            logger.error(f"Error clicking button {button_text}: {e}")
            return False
    
    def verify_page_title(self, expected_title: str, timeout: int = 5) -> bool:
        """Verify that we're on the expected page by checking for title text"""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Look for the title text on screen
                title_location = pyautogui.locateOnScreen(
                    f"page_images/{expected_title.lower().replace(' ', '_')}.png",
                    confidence=0.8
                )
                
                if title_location:
                    logger.info(f"Verified page: {expected_title}")
                    return True
                
                time.sleep(0.5)
            
            logger.warning(f"Page title not found: {expected_title}")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying page {expected_title}: {e}")
            return False
    
    def test_create_new_invoice_button(self) -> bool:
        """Test the 'Create New Invoice' button"""
        logger.info("Testing 'Create New Invoice' button...")
        
        # Click the Create New Invoice button
        if not self.click_button_by_text("Create New Invoice"):
            self.take_screenshot("create_invoice_button_not_found")
            return False
        
        # Verify we're on the client type selection page
        if self.verify_page_title("Select Client Type"):
            self.test_results.append(("Create New Invoice", "PASS"))
            return True
        else:
            self.take_screenshot("create_invoice_navigation_failed")
            self.test_results.append(("Create New Invoice", "FAIL"))
            return False
    
    def test_manage_invoices_button(self) -> bool:
        """Test the 'Manage Invoices' button"""
        logger.info("Testing 'Manage Invoices' button...")
        
        # First, go back to main menu
        self.go_back_to_main_menu()
        
        # Click the Manage Invoices button
        if not self.click_button_by_text("Manage Invoices"):
            self.take_screenshot("manage_invoices_button_not_found")
            return False
        
        # Verify we're on the manage invoices page
        if self.verify_page_title("Manage Invoices"):
            self.test_results.append(("Manage Invoices", "PASS"))
            return True
        else:
            self.take_screenshot("manage_invoices_navigation_failed")
            self.test_results.append(("Manage Invoices", "FAIL"))
            return False
    
    def test_manage_clients_button(self) -> bool:
        """Test the 'Manage Clients' button"""
        logger.info("Testing 'Manage Clients' button...")
        
        # First, go back to main menu
        self.go_back_to_main_menu()
        
        # Click the Manage Clients button
        if not self.click_button_by_text("Manage Clients"):
            self.take_screenshot("manage_clients_button_not_found")
            return False
        
        # Verify we're on the manage clients page
        if self.verify_page_title("Manage Clients"):
            self.test_results.append(("Manage Clients", "PASS"))
            return True
        else:
            self.take_screenshot("manage_clients_navigation_failed")
            self.test_results.append(("Manage Clients", "FAIL"))
            return False
    
    def test_settings_button(self) -> bool:
        """Test the 'Settings' button"""
        logger.info("Testing 'Settings' button...")
        
        # First, go back to main menu
        self.go_back_to_main_menu()
        
        # Click the Settings button
        if not self.click_button_by_text("Settings"):
            self.take_screenshot("settings_button_not_found")
            return False
        
        # Wait for settings dialog to appear
        time.sleep(1)
        
        # Try to find and close the settings dialog
        try:
            # Look for a close button or press Escape
            pyautogui.press('escape')
            time.sleep(0.5)
            
            # Verify we're back on main menu
            if self.verify_page_title("Main Menu"):
                self.test_results.append(("Settings", "PASS"))
                return True
            else:
                self.take_screenshot("settings_navigation_failed")
                self.test_results.append(("Settings", "FAIL"))
                return False
                
        except Exception as e:
            logger.error(f"Error testing settings: {e}")
            self.test_results.append(("Settings", "FAIL"))
            return False
    
    def go_back_to_main_menu(self):
        """Navigate back to the main menu"""
        logger.info("Navigating back to main menu...")
        
        # Try multiple ways to get back to main menu
        try:
            # Method 1: Press Escape key
            pyautogui.press('escape')
            time.sleep(1)
            
            # Method 2: Look for a back button
            back_button = pyautogui.locateOnScreen("button_images/back.png", confidence=0.8)
            if back_button:
                pyautogui.click(pyautogui.center(back_button))
                time.sleep(1)
            
            # Method 3: Look for "Back to Main Menu" button
            main_menu_button = pyautogui.locateOnScreen("button_images/back_to_main_menu.png", confidence=0.8)
            if main_menu_button:
                pyautogui.click(pyautogui.center(main_menu_button))
                time.sleep(1)
            
            # Verify we're on main menu
            if self.verify_page_title("Main Menu"):
                logger.info("Successfully returned to main menu")
            else:
                logger.warning("Could not verify return to main menu")
                
        except Exception as e:
            logger.error(f"Error navigating back to main menu: {e}")
    
    def test_main_menu_ui_elements(self) -> bool:
        """Test that all main menu UI elements are present"""
        logger.info("Testing main menu UI elements...")
        
        # Go back to main menu first
        self.go_back_to_main_menu()
        
        # Check for main menu title
        if not self.verify_page_title("Main Menu"):
            self.take_screenshot("main_menu_title_not_found")
            return False
        
        # Check for all main menu buttons
        expected_buttons = [
            "Create New Invoice",
            "Manage Invoices", 
            "Manage Clients",
            "Settings"
        ]
        
        all_buttons_found = True
        for button in expected_buttons:
            if not self.click_button_by_text(button):
                logger.warning(f"Button not found: {button}")
                all_buttons_found = False
                # Go back to main menu for next test
                self.go_back_to_main_menu()
        
        if all_buttons_found:
            self.test_results.append(("UI Elements", "PASS"))
            return True
        else:
            self.test_results.append(("UI Elements", "FAIL"))
            return False
    
    def run_all_tests(self):
        """Run all main menu tests"""
        logger.info("Starting main menu automated tests...")
        
        # Create directories for screenshots if they don't exist
        os.makedirs("button_images", exist_ok=True)
        os.makedirs("page_images", exist_ok=True)
        
        # Start the application
        if not self.start_application():
            logger.error("Failed to start application. Exiting tests.")
            return False
        
        # Wait for application to fully load
        time.sleep(2)
        
        # Take initial screenshot
        self.take_screenshot("initial_main_menu")
        
        # Run individual tests
        tests = [
            self.test_main_menu_ui_elements,
            self.test_create_new_invoice_button,
            self.test_manage_invoices_button,
            self.test_manage_clients_button,
            self.test_settings_button
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Test failed with exception: {e}")
                self.take_screenshot(f"test_exception_{test.__name__}")
        
        # Print test results
        self.print_test_results()
        
        # Clean up
        self.cleanup()
        
        return True
    
    def print_test_results(self):
        """Print the test results summary"""
        logger.info("\n" + "="*50)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*50)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results:
            logger.info(f"{test_name}: {result}")
            if result == "PASS":
                passed += 1
            else:
                failed += 1
        
        logger.info(f"\nTotal Tests: {len(self.test_results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed == 0:
            logger.info("🎉 All tests passed!")
        else:
            logger.warning(f"❌ {failed} test(s) failed")
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up...")
        
        # Close the application
        if self.app_process:
            try:
                self.app_process.terminate()
                self.app_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.app_process.kill()
            except Exception as e:
                logger.error(f"Error closing application: {e}")

def main():
    """Main function to run the tests"""
    print("IReS Main Menu Automated Testing")
    print("="*40)
    
    # Check if PyAutoGUI is installed
    try:
        import pyautogui
    except ImportError:
        print("PyAutoGUI is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
        import pyautogui
    
    # Create and run the tester
    tester = MainMenuTester()
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n✅ Testing completed successfully!")
        else:
            print("\n❌ Testing failed!")
            
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        tester.cleanup()
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        tester.cleanup()

if __name__ == "__main__":
    main() 