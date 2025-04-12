import cv2
import numpy as np
import os
import time
import threading
from flask import Flask, Response
import RPi.GPIO as GPIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from twilio.rest import Client
from PIL import Image
from dotenv import load_dotenv

# === GPIO SETUP ===
PIR_PIN = 4
BUZZER_PIN = 5
LOCK_PIN = 17  # GPIO pin connected to the solenoid lock

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(LOCK_PIN, GPIO.OUT)
GPIO.output(LOCK_PIN, GPIO.LOW)

# === TWILIO CONFIG (Replace with environment variables) ===
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')  
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')
TWILIO_TO_NUMBER = os.getenv('TWILIO_TO_NUMBER')

# === EMAIL CONFIG ===
EMAIL_ADDRESS = ''
EMAIL_PASSWORD = ''
TO_EMAIL = ''

# === FACE RECOGNITION SETUP ===
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

# === ID to NAME Mapping ===
names = ['None', 'Aayush']  # Update according to your dataset IDs

# === FLASK APP ===
app = Flask(__name__)
camera = cv2.VideoCapture(0)

# === NOTIFICATION FUNCTIONS ===
def send_email_alert():
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = 'Motion Detected!'
    msg.attach(MIMEText('Motion detected by PIR sensor.', 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.sendmail(EMAIL_ADDRESS, TO_EMAIL, msg.as_string())
    server.quit()

def send_twilio_sms(message_body):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=message_body,
        from_=TWILIO_FROM_NUMBER,
        to=TWILIO_TO_NUMBER
    )
    print("Twilio SMS sent:", message.sid)

# === SOLENOID CONTROL ===
def unlock_door():
    print("🔓 Unlocking door...")
    GPIO.output(LOCK_PIN, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(LOCK_PIN, GPIO.LOW)
    print("🔒 Door locked again.")

# === MOTION DETECTION & FACE RECOGNITION ===
def detect_motion_and_face():
    while True:
        if GPIO.input(PIR_PIN):
            print("Motion detected!")
            GPIO.output(BUZZER_PIN, GPIO.HIGH)
            send_email_alert()
            send_twilio_sms("Motion detected at your home!")

            ret, frame = camera.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                id_, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                if confidence < 60:
                    name = names[id_]
                    print(f"Authorized user detected: {name} ({round(100 - confidence)}%)")
                    unlock_door()
                else:
                    print(f"Intruder detected ({round(100 - confidence)}%)")
                    send_twilio_sms("Unauthorized face detected at your door!")

            GPIO.output(BUZZER_PIN, GPIO.LOW)
            time.sleep(5)
        else:
            GPIO.output(BUZZER_PIN, GPIO.LOW)

# === LIVE STREAM FUNCTION ===
def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# === START THREADS ===
if __name__ == '__main__':
    motion_thread = threading.Thread(target=detect_motion_and_face)
    motion_thread.daemon = True
    motion_thread.start()

    app.run(host='192.168.1.103', port=5000)

load_dotenv()