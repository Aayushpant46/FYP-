from flask import Flask, render_template, request
import RPi.GPIO as GPIO

# Flask app
app = Flask(__name__)

# Relay pin configuration
relay_pin = 23

# Setup GPIO
GPIO.setwarnings(False)  # Disable GPIO warnings
GPIO.setmode(GPIO.BCM)
GPIO.setup(relay_pin, GPIO.OUT)

# Initialize relay state (OFF)
GPIO.output(relay_pin, GPIO.HIGH)

@app.route("/")
def index():
    """Home page with relay control buttons."""
    # Check the current state of the relay
    relay_state = "OFF" if GPIO.input(relay_pin) == GPIO.HIGH else "ON"
    return render_template("index.html", relay_state=relay_state)

@app.route("/control", methods=["POST"])
def control():
    """Control the relay based on user action."""
    action = request.form.get("action")
    if action == "ON":
        GPIO.output(relay_pin, GPIO.LOW)  # Turn ON (active-low)
        relay_state = "ON"
    elif action == "OFF":
        GPIO.output(relay_pin, GPIO.HIGH)  # Turn OFF
        relay_state = "OFF"
    else:
        relay_state = "Invalid action"
    return render_template("index.html", relay_state=relay_state)

@app.route("/cleanup")
def cleanup():
    """Cleanup GPIO and stop the server."""
    GPIO.cleanup()
    return "GPIO cleaned up and server stopped!"

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)  # Bind to all network interfaces
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Server stopped and GPIO cleaned up.")
