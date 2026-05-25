#!/usr/bin/env python3
"""
Standalone Gmail SMTP verification for Smart Shopper.

Reads credentials from .env and sends one test email.
Required .env values:
  SENDER_GMAIL=your@gmail.com
  GMAIL_PASSWORD=your_16_character_gmail_app_password
  RECEIVER_EMAIL=recipient@example.com
"""
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


def load_env_file(path: Path = ENV_PATH) -> None:
    if not path.exists():
        print(f"Missing .env file at {path}")
        return

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Missing {name} in .env")
    return value


def send_test_email() -> None:
    load_env_file()

    sender = require_env("SENDER_GMAIL")
    password = require_env("GMAIL_PASSWORD")
    receiver = require_env("RECEIVER_EMAIL")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "Smart Shopper Gmail test"
    msg.set_content(
        "\n".join(
            [
                "Gmail SMTP verification succeeded.",
                "",
                f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "Your Smart Shopper email credentials are working.",
            ]
        )
    )

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender, password)
        server.send_message(msg)

    print("Gmail test email sent successfully.")
    print(f"From: {sender}")
    print(f"To:   {receiver}")


if __name__ == "__main__":
    try:
        send_test_email()
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        print("Fill SENDER_GMAIL, GMAIL_PASSWORD, and RECEIVER_EMAIL in .env, then rerun.")
    except smtplib.SMTPAuthenticationError:
        print("Gmail authentication failed.")
        print("Use a Gmail App Password, not your normal Gmail password.")
    except Exception as exc:
        print(f"Gmail test failed: {exc}")
