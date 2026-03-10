#!/usr/bin/env python3
"""
Admin Web Interface for Smart Shopper Price Monitoring System
Advanced administration dashboard with system management features
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import threading
import os
from pathlib import Path
from datetime import datetime, timedelta
from price_tracker.mailer import Mailer

app = Flask(__name__, template_folder='price_tracker/web/templates')
monitor = None
monitor_thread = None

# Admin authentication (simple token-based for demo)
ADMIN_TOKEN = "admin123"  # In production, use proper authentication

def require_admin():
    """Simple admin authentication check"""
    # In production, implement proper authentication
    return True

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    if not require_admin():
        return redirect('/admin/login')
    return render_template('admin_dashboard.html')

@app.route('/admin/login')
def admin_login():
    """Admin login page (placeholder)"""
    return redirect('/admin')  # Skip login for demo

@app.route('/')
def customer_redirect():
    """Redirect to customer dashboard"""
    return redirect('http://127.0.0.1:5052')

@app.route('/api/admin/stats')
def get_admin_stats():
    """Get comprehensive system statistics"""
    try:
        # Load products
        products_file = Path.home() / 'price-tracker' / 'products.json'
        total_products = 0
        active_alerts = 0
        
        if products_file.exists():
            with open(products_file, 'r') as f:
                products = json.load(f)
                total_products = len(products)
                # Count products with prices below alert threshold (simulated)
                active_alerts = len([p for p in products if p.get('warn_price', 0) > 30000])
        
        # System uptime (simulated)
        uptime_hours = 24  # Placeholder
        
        # Last check time (simulated)
        last_check = datetime.now().strftime("%H:%M:%S")
        
        # Monitoring status
        monitoring = monitor_thread and monitor_thread.is_alive() if monitor_thread else False
        
        stats = {
            'totalProducts': total_products,
            'activeAlerts': active_alerts,
            'systemUptime': f"{uptime_hours}h",
            'lastCheck': last_check,
            'monitoring': monitoring
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/products')
def get_admin_products():
    """Get all products with additional admin info"""
    try:
        products_file = Path.home() / 'price-tracker' / 'products.json'
        
        if products_file.exists():
            with open(products_file, 'r') as f:
                products = json.load(f)
            
            # Add admin-specific fields
            for i, product in enumerate(products):
                product['id'] = i
                product['status'] = 'active'  # Placeholder
                product['current_price'] = product.get('warn_price', 0) + 5000  # Simulated current price
                product['category'] = product.get('category', 'Electronics')
                product['added_date'] = product.get('added_date', datetime.now().isoformat())
            
            return jsonify({'success': True, 'products': products})
        else:
            return jsonify({'success': True, 'products': []})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/add_product', methods=['POST'])
def admin_add_product():
    """Add a new product with admin features"""
    try:
        data = request.json
        url = data.get('url')
        warn_price = float(data.get('warn_price'))
        name = data.get('name', 'Unknown Product')
        category = data.get('category', 'Electronics')
        
        if not url or not warn_price:
            return jsonify({'success': False, 'error': 'URL and price are required'})
        
        # Load existing products
        products_file = Path.home() / 'price-tracker' / 'products.json'
        products_file.parent.mkdir(exist_ok=True)
        
        try:
            if products_file.exists():
                with open(products_file, 'r') as f:
                    products = json.load(f)
            else:
                products = []
        except:
            products = []
        
        # Add new product with admin fields
        new_product = {
            'url': url,
            'warn_price': warn_price,
            'name': name,
            'category': category,
            'added_date': datetime.now().isoformat(),
            'added_by': 'admin',
            'status': 'active'
        }
        
        products.append(new_product)
        
        # Save updated products
        with open(products_file, 'w') as f:
            json.dump(products, f, indent=2)
        
        return jsonify({'success': True, 'product': new_product})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/delete_product', methods=['POST'])
def admin_delete_product():
    """Delete a product"""
    try:
        data = request.json
        index = data.get('index')
        
        if index is None:
            return jsonify({'success': False, 'error': 'Product index is required'})
        
        # Load existing products
        products_file = Path.home() / 'price-tracker' / 'products.json'
        
        if not products_file.exists():
            return jsonify({'success': False, 'error': 'Products file not found'})
        
        with open(products_file, 'r') as f:
            products = json.load(f)
        
        if 0 <= index < len(products):
            deleted_product = products.pop(index)
            
            # Save updated products
            with open(products_file, 'w') as f:
                json.dump(products, f, indent=2)
            
            return jsonify({'success': True, 'deleted_product': deleted_product})
        else:
            return jsonify({'success': False, 'error': 'Invalid product index'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/config')
def get_admin_config():
    """Get system configuration"""
    try:
        config_file = Path.home() / 'price-tracker' / 'config.json'
        if not config_file.exists():
            config_file = Path('config.json')
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            return jsonify({'success': True, 'config': config})
        else:
            return jsonify({'success': False, 'error': 'Config file not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/update_config', methods=['POST'])
def update_admin_config():
    """Update system configuration"""
    try:
        data = request.json
        
        # Update both config files
        config_files = [
            Path('config.json'),
            Path.home() / 'price-tracker' / 'config.json'
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    # Update configuration
                    for key, value in data.items():
                        if key in ['sender_gmail', 'gmail_password', 'receiver_email', 'check_interval_hours', 'enable_notifications']:
                            config[key] = value
                    
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    print(f"Updated config in {config_file}")
                except Exception as e:
                    print(f"Error updating {config_file}: {e}")
        
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/logs')
def get_admin_logs():
    """Get system logs"""
    try:
        # Read from price alerts log file
        logs_file = Path.home() / 'price-tracker' / 'price_alerts.log'
        logs = []
        
        if logs_file.exists():
            try:
                with open(logs_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse log entries
                entries = content.split('=' * 70)
                for entry in entries[-10:]:  # Last 10 entries
                    if entry.strip():
                        lines = entry.strip().split('\n')
                        if len(lines) >= 2:
                            timestamp_line = lines[0]
                            message_lines = lines[1:]
                            
                            logs.append({
                                'timestamp': timestamp_line.replace('[', '').replace(']', '').strip(),
                                'message': ' | '.join(message_lines)
                            })
            except Exception as e:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'message': f'Error reading logs: {e}'
                })
        
        # Add some system logs
        logs.extend([
            {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'message': 'Admin dashboard accessed'
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                'message': 'System monitoring active'
            }
        ])
        
        return jsonify({'success': True, 'logs': logs})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/start_monitoring', methods=['POST'])
def admin_start_monitoring():
    """Start monitoring system with live demo data"""
    try:
        # This would integrate with the actual monitoring system
        global monitor_thread
        
        # For demo purposes, we'll simulate starting monitoring
        print("🚀 Admin: Starting live monitoring system...")
        
        # Simulate some immediate activity
        import threading
        import time
        
        def demo_monitoring():
            """Demo monitoring function that shows immediate activity"""
            time.sleep(1)
            print("📡 Demo: Fetching product prices...")
            time.sleep(2)
            print("💰 Demo: PlayStation 5 - ₹47,500 (Price check complete)")
            time.sleep(1)
            print("💰 Demo: iPhone 15 Pro - ₹82,300 (Price check complete)")
            time.sleep(1)
            print("💰 Demo: MacBook Air M1 - ₹68,900 (Price check complete)")
        
        # Start demo monitoring in background
        demo_thread = threading.Thread(target=demo_monitoring, daemon=True)
        demo_thread.start()
        
        return jsonify({
            'success': True, 
            'message': 'Live monitoring started successfully',
            'demo_mode': True,
            'products_monitored': 3,
            'check_interval': '15 seconds'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/stop_monitoring', methods=['POST'])
def admin_stop_monitoring():
    """Stop monitoring system"""
    try:
        # This would integrate with the actual monitoring system
        global monitor_thread
        
        # For demo purposes, we'll simulate stopping monitoring
        print("🛑 Admin: Stopping monitoring system...")
        
        return jsonify({'success': True, 'message': 'Monitoring stopped successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/test_email', methods=['POST'])
def admin_test_email():
    """Test email system"""
    try:
        mailer = Mailer()
        mailer.log_in()
        
        if mailer.email_works:
            # Send test email
            test_url = "https://example.com/test-product"
            test_name = "Test Product - Admin Dashboard"
            test_price = 999.99
            
            mailer.send_mail(test_url, test_name, test_price)
            
            return jsonify({'success': True, 'message': 'Test email sent successfully'})
        else:
            return jsonify({'success': False, 'error': 'Email authentication failed'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/monitoring_activity')
def get_monitoring_activity():
    """Get live monitoring activity data"""
    try:
        import random
        from datetime import datetime, timedelta
        
        # Generate sample monitoring activity
        activities = []
        products = [
            {'name': 'PlayStation 5 Console', 'price': 47500, 'alert': 45000},
            {'name': 'iPhone 15 Pro 256GB', 'price': 82300, 'alert': 80000},
            {'name': 'MacBook Air M1', 'price': 68900, 'alert': 70000}
        ]
        
        for i, product in enumerate(products):
            time_offset = datetime.now() - timedelta(seconds=i*30)
            activities.append({
                'timestamp': time_offset.strftime('%H:%M:%S'),
                'message': f"🔍 Checking {product['name']}...",
                'type': 'info'
            })
            
            activities.append({
                'timestamp': (time_offset + timedelta(seconds=5)).strftime('%H:%M:%S'),
                'message': f"💰 {product['name']}: ₹{product['price']:,}",
                'type': 'success' if product['price'] < product['alert'] else 'info'
            })
            
            if product['price'] < product['alert']:
                activities.append({
                    'timestamp': (time_offset + timedelta(seconds=10)).strftime('%H:%M:%S'),
                    'message': f"🚨 PRICE ALERT: {product['name']} below threshold!",
                    'type': 'alert'
                })
        
        return jsonify({
            'success': True,
            'activities': activities,
            'monitoring_active': True
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/system_info')
def get_system_info():
    """Get detailed system information"""
    try:
        import psutil
        import platform
        
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:').percent
        }
        
        return jsonify({'success': True, 'system_info': system_info})
        
    except ImportError:
        return jsonify({'success': True, 'system_info': {'message': 'System monitoring not available (psutil not installed)'}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🛡️ Starting Smart Shopper Admin Dashboard...")
    print("🔐 Admin Dashboard: http://127.0.0.1:5053/admin")
    print("👥 Customer Dashboard: http://127.0.0.1:5052")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5053, debug=True)