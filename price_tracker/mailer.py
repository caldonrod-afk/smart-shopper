import smtplib
import json
import os
from datetime import datetime
from pathlib import Path

from price_tracker.constants import CONFIG_PATH


class Mailer:
    def __init__(self):
        self.load_config()
        self.server = None
        self.alerts_file = Path.home() / 'price-tracker' / 'price_alerts.log'
        self.email_works = False

    def load_config(self):
        """Load configuration from config file"""
        try:
            with open(CONFIG_PATH) as json_file:
                config = json.load(json_file)
                self.sender_gmail = config.get('sender_gmail', 'No Sender')
                self.gmail_password = config.get('gmail_password', '')
                self.receiver_email = config.get('receiver_email', 'No Receiver')
        except FileNotFoundError:
            print("Config file couldn't be found")
            exit(3)
        except ValueError:
            print('Config file is broken.')
            exit(3)

        self.server = None
        self.alerts_file = Path.home() / 'price-tracker' / 'price_alerts.log'
        self.email_works = False

    def log_in(self):
        """Test email authentication to verify credentials work"""
        try:
            print('🔐 Testing email authentication...')
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender_gmail, self.gmail_password)
            server.quit()
            
            self.email_works = True
            print('✅ Email authentication successful!')
            print(f'📧 Sender: {self.sender_gmail}')
            print(f'📬 Receiver: {self.receiver_email}')
            
        except Exception as e:
            print(f'⚠️ Email authentication failed: {e}')
            print('💾 Price alerts will be saved to file instead: ~/price-tracker/price_alerts.log')
            self.email_works = False

    def send_mail(self, url, product_name, price, receiver_email=None):
        """Send price alert email to specified receiver or default from config"""
        # Reload config to get latest receiver email if not specified
        if receiver_email is None:
            self.load_config()
            receiver_email = self.receiver_email
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Try to send email using direct SMTP connection (like the working test script)
        try:
            print(f'📧 Attempting to send email for {product_name} at price ₹{price}')
            print(f'📬 Sending to: {receiver_email}')
            
            # Create fresh SMTP connection for each email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender_gmail, self.gmail_password)
            
            # Clean product name for email (remove emojis and special characters)
            clean_product_name = ''.join(char for char in product_name if ord(char) < 128)
            clean_product_name = clean_product_name.strip()
            
            # Create email message (avoiding emojis for compatibility)
            subject = f'Price Alert - {clean_product_name}!'
            body = f"""Great news! The price has dropped!

Product: {clean_product_name}
Current Price: Rs.{price}
Product URL: {url}

This is an automated alert from your Smart Shopper price tracker.

Happy shopping!
            """.strip()
            
            msg = f"Subject: {subject}\n\n{body}"
            
            # Send the email
            server.sendmail(self.sender_gmail, receiver_email, msg)
            server.quit()
            
            print(f'✅ Email sent successfully for {product_name} at price ₹{price} to {receiver_email}')
            
        except Exception as e:
            print(f'⚠️ Email sending failed: {e}')
            print('💾 Saving price alert to file instead')
            self._save_alert_to_file(timestamp, product_name, price, url, receiver_email)
    
    def _save_alert_to_file(self, timestamp, product_name, price, url, receiver_email=None):
        """Save price alert to a local file"""
        try:
            with open(self.alerts_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"[{timestamp}] ⚠️ PRICE ALERT\n")
                f.write(f"Product: {product_name}\n")
                f.write(f"Current Price: Rs.{price}\n")
                f.write(f"URL: {url}\n")
                if receiver_email:
                    f.write(f"Intended Receiver: {receiver_email}\n")
                f.write(f"{'='*70}\n")
            
            print(f'💾 Alert saved for {product_name} at price ₹{price}')
        except Exception as e:
            print(f'❌ Error saving alert: {e}')

    def log_out(self):
        """No longer needed since we use fresh connections for each email"""
        pass
