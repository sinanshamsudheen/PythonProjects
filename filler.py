import random
import time
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to generate a random first and last name
def generate_random_name():
    first_names = ["John", "Emma", "Liam", "Olivia", "Noah"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
    return random.choice(first_names), random.choice(last_names)

# Function to generate a random Gmail email
def generate_random_email(first_name, last_name):
    random_string = ''.join(random.choices(string.digits, k=4))
    return f"{first_name.lower()}.{last_name.lower()}{random_string}@gmail.com"

# Function to close pop-ups
def close_popup(driver):
    try:
        time.sleep(2)  # Wait for pop-up to appear
        popups = driver.find_elements(By.XPATH, "//button[contains(text(),'×') or contains(@aria-label, 'Close')]")
        for popup in popups:
            popup.click()
        print("Pop-up closed.")
    except:
        print("No pop-up detected.")

# Chrome options to disable SSL errors
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--ignore-certificate-errors")  # Fix SSL handshake error
chrome_options.add_argument("--disable-popup-blocking")  # Ensure pop-ups are accessible
chrome_options.add_argument("--incognito")

# Start WebDriver
driver = webdriver.Chrome(options=chrome_options)

try:
    driver.get("https://conceptkart.com/account/register?flits_refer_code=MnY0cXhwZXRt&flits_inviter_name=U2luYW4gU2hhbXN1ZGhlZW4%3D")  # Replace with your URL
    time.sleep(3)  # Allow page to load
    
    # Close the pop-up
    close_popup(driver)

    # Wait for the form fields to be visible
    wait = WebDriverWait(driver, 10)  
    first_name_field = wait.until(EC.presence_of_element_located((By.NAME, "First_Name")))  
    last_name_field = driver.find_element(By.NAME, "Last_Name")  
    email_field = driver.find_element(By.NAME, "Email")  
    password_field = driver.find_element(By.NAME, "Password")  

    # Generate random user details
    first_name, last_name = generate_random_name()
    email = generate_random_email(first_name, last_name)

    # Enter details
    first_name_field.send_keys(first_name)
    last_name_field.send_keys(last_name)
    email_field.send_keys(email)
    password_field.send_keys("RandomPassword123!")  
    password_field.send_keys(Keys.RETURN)

    time.sleep(5)  # Wait to observe results
    print("Signup successful!")

except Exception as e:
    print("Error:", e)

finally:
    driver.quit()
    print("Browser closed.")
