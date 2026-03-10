#!/usr/bin/env python3
"""Test email functionality"""

print("📧 Testing Email Alert System")
print("=" * 70)

# Test 1: Load configuration
print("\n1️⃣ Loading email configuration...")
try:
    import json
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    sender = config.get('sender_gmail')
    password = config.get('gmail_password')
    receiver = config.get('receiver_email')
    
    print(f"   ✅ Config loaded")
    print(f"   📧 Sender: {sender}")
    print(f"   📬 Receiver: {receiver}")
    print(f"   🔑 Password: {'*' * len(password) if password else 'NOT SET'}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 2: Test SMTP connection
print("\n2️⃣ Testing SMTP connection...")
try:
    import smtplib
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    
    print("   ✅ Connected to Gmail SMTP server")
    
    # Test login
    print("   🔐 Testing authentication...")
    server.login(sender, password)
    print("   ✅ Authentication successful!")
    
    server.quit()
    
except smtplib.SMTPAuthenticationError as e:
    print(f"   ❌ Authentication failed: {e}")
    print("\n   💡 Possible fixes:")
    print("   1. Check if 2-Step Verification is enabled on your Gmail")
    print("   2. Generate a new App Password at: https://myaccount.google.com/apppasswords")
    print("   3. Update the password in config.json")
    exit(1)
    
except Exception as e:
    print(f"   ❌ Connection error: {e}")
    exit(1)

# Test 3: Send test email
print("\n3️⃣ Sending test email...")
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sender, password)
    
    subject = "Test Alert - Smart Shopper Price Tracker"
    body = """This is a test email from your Smart Shopper price tracker.

If you received this email, your alert system is working correctly!

Test Details:
- Product: Test Product
- Price: Rs. 99,999
- Time: Now

Happy Shopping!
"""
    
    msg = f"Subject: {subject}\n\n{body}"
    
    server.sendmail(sender, receiver, msg)
    server.quit()
    
    print(f"   ✅ Test email sent successfully!")
    print(f"   📬 Check your inbox: {receiver}")
    print("\n   💡 Tips:")
    print("   - Check your spam/junk folder")
    print("   - Wait 1-2 minutes for delivery")
    print("   - Check Gmail filters aren't blocking it")
    
except Exception as e:
    print(f"   ❌ Failed to send email: {e}")
    exit(1)

# Test 4: Check if price is actually dropping
print("\n4️⃣ Checking alert conditions...")
print("   💡 Emails are only sent when:")
print("   - Current price < Alert price (warn_price)")
print("   - Example: If alert price is Rs. 1,39,999")
print("             Email only sent if current price is BELOW Rs. 1,39,999")

print("\n" + "=" * 70)
print("🎉 Email system test complete!")
print("\nIf you received the test email, your system is working!")
print("If not, check the error messages above for fixes.")
print("=" * 70)
