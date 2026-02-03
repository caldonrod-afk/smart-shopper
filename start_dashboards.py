#!/usr/bin/env python3
"""
Smart Shopper Dashboard Launcher
Starts both Customer and Admin dashboards
"""
import subprocess
import time
import sys
from pathlib import Path

def start_dashboards():
    """Start both customer and admin dashboards"""
    print("🚀 Smart Shopper - Dashboard Launcher")
    print("=" * 50)
    
    try:
        # Start customer dashboard
        print("📱 Starting Customer Dashboard...")
        customer_process = subprocess.Popen([
            sys.executable, 'web_monitor.py'
        ], cwd=Path.cwd())
        
        # Wait a moment
        time.sleep(2)
        
        # Start admin dashboard
        print("🛡️ Starting Admin Dashboard...")
        admin_process = subprocess.Popen([
            sys.executable, 'admin_monitor.py'
        ], cwd=Path.cwd())
        
        # Wait a moment for both to start
        time.sleep(3)
        
        print("\n✅ Both dashboards started successfully!")
        print("=" * 50)
        print("📱 Customer Dashboard: http://127.0.0.1:5052")
        print("🛡️ Admin Dashboard:    http://127.0.0.1:5053/admin")
        print("=" * 50)
        print("\n🎯 Usage:")
        print("• Customer Dashboard - For end users to monitor prices")
        print("• Admin Dashboard - For system administration and management")
        print("\n⚠️ Press Ctrl+C to stop both dashboards")
        
        # Keep the script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping dashboards...")
            customer_process.terminate()
            admin_process.terminate()
            print("✅ Dashboards stopped successfully!")
            
    except Exception as e:
        print(f"❌ Error starting dashboards: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_dashboards()