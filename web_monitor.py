#!/usr/bin/env python3
"""
Web Interface for Real-Time Price Monitoring
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import threading
from pathlib import Path
from datetime import datetime

app = Flask(__name__, template_folder='price_tracker/web/templates')
monitor = None
monitor_thread = None

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('monitor_dashboard.html')

@app.route('/api/receiver_email')
def get_receiver_email():
    """Get current receiver email from config"""
    try:
        config_file = Path.home() / 'price-tracker' / 'config.json'
        if not config_file.exists():
            config_file = Path('config.json')
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            return jsonify({'success': True, 'receiver_email': config.get('receiver_email', '')})
        else:
            return jsonify({'success': False, 'error': 'Config file not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update_receiver_email', methods=['POST'])
def update_receiver_email():
    """Update receiver email in config"""
    try:
        data = request.json
        new_email = data.get('receiver_email')
        
        if not new_email:
            return jsonify({'success': False, 'error': 'Email is required'})
        
        # Update both config files (current directory and home directory)
        config_files = [
            Path('config.json'),
            Path.home() / 'price-tracker' / 'config.json'
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    config['receiver_email'] = new_email
                    
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    print(f"Updated receiver email in {config_file}")
                except Exception as e:
                    print(f"Error updating {config_file}: {e}")
        
        return jsonify({'success': True, 'receiver_email': new_email})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/products')
def get_products():
    """Get all products being monitored"""
    products_file = Path.home() / 'price-tracker' / 'products.json'
    try:
        if products_file.exists():
            with open(products_file, 'r') as f:
                products = json.load(f)
            return jsonify({'success': True, 'products': products})
        else:
            return jsonify({'success': True, 'products': []})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/add_product', methods=['POST'])
def add_product():
    """Add a new product to monitor"""
    try:
        data = request.json
        url = data.get('url')
        warn_price = float(data.get('warn_price'))
        name = data.get('name', 'Unknown Product')
        
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
        
        # Add new product
        new_product = {
            'url': url,
            'warn_price': warn_price,
            'name': name,
            'added_date': datetime.now().isoformat()
        }
        
        products.append(new_product)
        
        # Save updated products
        with open(products_file, 'w') as f:
            json.dump(products, f, indent=2)
        
        return jsonify({'success': True, 'product': new_product})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/start_monitoring', methods=['POST'])
def start_monitoring():
    """Start real-time monitoring"""
    try:
        return jsonify({'success': False, 'error': 'Use api_monitor.py for monitoring'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop_monitoring', methods=['POST'])
def stop_monitoring():
    """Stop real-time monitoring"""
    try:
        return jsonify({'success': True, 'message': 'Use api_monitor.py for monitoring'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def get_status():
    """Get monitoring status"""
    global monitor, monitor_thread
    
    is_running = monitor_thread and monitor_thread.is_alive() if monitor_thread else False
    
    return jsonify({
        'success': True,
        'monitoring': is_running,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🌐 Starting Web Monitor Interface...")
    print("📱 Open: http://127.0.0.1:5052")
    app.run(host='127.0.0.1', port=5052, debug=True)