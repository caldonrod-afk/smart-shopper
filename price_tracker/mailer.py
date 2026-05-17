import json
import os
import re
import smtplib
from datetime import datetime
from pathlib import Path

from price_tracker.constants import BASE_DIR, CONFIG_PATH


ENV_PATH = Path(BASE_DIR) / '.env'


def _load_env_file():
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip().lstrip('\ufeff')
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ[key] = value


def _normalize_emails(value):
    if isinstance(value, str):
        candidates = re.split(r'[\n,;]+', value)
    elif isinstance(value, list):
        candidates = value
    else:
        candidates = []

    emails = []
    seen = set()
    for item in candidates:
        email = str(item).strip().lower()
        if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            continue
        if email not in seen:
            emails.append(email)
            seen.add(email)
    return emails


class Mailer:
    def __init__(self):
        self.load_config()
        self.server = None
        self.alerts_file = Path.home() / 'price-tracker' / 'price_alerts.log'
        self.email_works = False

    def load_config(self):
        """Load mail settings from .env and config.json."""
        _load_env_file()
        config = {}
        try:
            with open(CONFIG_PATH) as json_file:
                config = json.load(json_file)
        except FileNotFoundError:
            config = {}
        except ValueError:
            print('Config file is broken.')
            exit(3)

        self.sender_gmail = os.environ.get('SENDER_GMAIL') or config.get('sender_gmail', 'No Sender')
        self.gmail_password = os.environ.get('GMAIL_PASSWORD') or config.get('gmail_password', '')
        receivers = config.get('receiver_emails') or config.get('receiver_email') or os.environ.get('RECEIVER_EMAIL', '')
        self.receiver_emails = _normalize_emails(receivers)
        self.receiver_email = self.receiver_emails[0] if self.receiver_emails else 'No Receiver'

        self.server = None
        self.alerts_file = Path.home() / 'price-tracker' / 'price_alerts.log'
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
        self.email_works = False

    def log_in(self):
        """Test email authentication to verify credentials work."""
        try:
            print('Testing email authentication...')
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender_gmail, self.gmail_password)
            server.quit()

            self.email_works = True
            print('Email authentication successful.')
            print(f'Sender: {self.sender_gmail}')
            print(f'Receivers: {", ".join(self.receiver_emails) or self.receiver_email}')

        except Exception as e:
            print(f'Email authentication failed: {e}')
            print('Price alerts will be saved to file instead: ~/price-tracker/price_alerts.log')
            self.email_works = False

    def send_mail(self, url, product_name, price, receiver_email=None):
        """Send price alert email to all configured receivers."""
        if receiver_email is None:
            self.load_config()
            receiver_emails = self.receiver_emails
        else:
            receiver_emails = _normalize_emails(receiver_email)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not receiver_emails:
            print('Email sending skipped: no receiver emails configured')
            self._save_alert_to_file(timestamp, product_name, price, url, None)
            return

        try:
            print(f'Attempting to send email for {product_name} at price Rs.{price}')
            print(f'Sending to: {", ".join(receiver_emails)}')

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender_gmail, self.gmail_password)

            clean_product_name = ''.join(char for char in product_name if ord(char) < 128).strip()

            subject = f'Price Alert - {clean_product_name}!'
            body = f"""Great news! The price has dropped!

Product: {clean_product_name}
Current Price: Rs.{price}
Product URL: {url}

This is an automated alert from your Smart Shopper price tracker.

Happy shopping!
            """.strip()

            msg = f'Subject: {subject}\n\n{body}'
            server.sendmail(self.sender_gmail, receiver_emails, msg)
            server.quit()

            print(f'Email sent successfully for {product_name} at price Rs.{price} to {", ".join(receiver_emails)}')

        except Exception as e:
            print(f'Email sending failed: {e}')
            print('Saving price alert to file instead')
            self._save_alert_to_file(timestamp, product_name, price, url, ', '.join(receiver_emails))

    def _save_alert_to_file(self, timestamp, product_name, price, url, receiver_email=None):
        """Save price alert to a local file."""
        try:
            with open(self.alerts_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*70}\n")
                f.write(f'[{timestamp}] PRICE ALERT\n')
                f.write(f'Product: {product_name}\n')
                f.write(f'Current Price: Rs.{price}\n')
                f.write(f'URL: {url}\n')
                if receiver_email:
                    f.write(f'Intended Receiver: {receiver_email}\n')
                f.write(f"{'='*70}\n")

            print(f'Alert saved for {product_name} at price Rs.{price}')
        except Exception as e:
            print(f'Error saving alert: {e}')

    def log_out(self):
        """No longer needed since we use fresh connections for each email."""
        pass
