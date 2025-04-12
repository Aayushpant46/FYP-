import RPi.GPIO as GPIO
import smtplib
from email.mime.text import MIMEText
import time

# GPIO mode
GPIO.setmode(GPIO.BCM)

# GPIO pin for reading the DO output
DO_PIN = 7  
GPIO.setup(DO_PIN, GPIO.IN)

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'  # SMTP server for Gmail
SMTP_PORT = 587
EMAIL_ADDRESS = 'aayushpant101@gmail.com'  # Myemail
EMAIL_PASSWORD = ''  # email password
RECIPIENT_EMAIL = 'aayushpant88@gmail.com'  # Recipient's email

# Function to send an email
def send_email(message):
    try:
        # Set up the email
        msg = MIMEText(message)
        msg['Subject'] = 'Gas Detection Alert'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL

        # Send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Enable encryption
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        print("Alert email sent!")
    except Exception as e:
        print(f"Failed to send email: {e}")

try:
    last_state = None  # Track the last gas state

    while True:
        # Read the state of the DO pin
        gas_present = GPIO.input(DO_PIN)

        # Determine the gas state
        if gas_present == GPIO.LOW:
            gas_state = "Detected"  # Gas is present
        else:
            gas_state = "Not Detected"  # No gas

        # Send an alert if gas is detected
        if gas_state == "Detected" and last_state != gas_state:
            print("Gas detected! Sending alert...")
            send_email("Warning: Gas has been detected! Please take immediate action.")

        # Update the last state
        last_state = gas_state

        time.sleep(0.5)  # Wait for a short period before reading again

except KeyboardInterrupt:
    print("Gas detection stopped by user")

finally:
    # Clean up GPIO settings
    GPIO.cleanup()
