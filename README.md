# 🛍️ Smart Shopper - Dual Dashboard Price Tracker

A comprehensive price monitoring system for Indian e-commerce sites with separate customer and admin interfaces.

## 🚀 Quick Start

### Option 1: Use Launcher Scripts (Recommended)
```bash
# Windows Batch
START_DASHBOARDS.bat

# Windows PowerShell  
START_DASHBOARDS.ps1

# Cross-platform Python
python start_dashboards.py
```

### Option 2: Manual Start
```bash
# Terminal 1 - Customer Dashboard
python web_monitor.py

# Terminal 2 - Admin Dashboard
python admin_monitor.py
```

## 🌐 Access URLs

- **📱 Customer Dashboard**: http://127.0.0.1:5052
- **🛡️ Admin Dashboard**: http://127.0.0.1:5053/admin

## 📧 Email Configuration

**Gmail Credentials:**
- Email: `smartshopper202526@gmail.com`
- App Password: `cvayayivdiqunhiv`

## 🎯 Dashboard Features

### 📱 Customer Dashboard
- **Purpose**: End-user price monitoring
- **Features**:
  - Add products to monitor
  - Set price alerts in Indian Rupees (₹)
  - Configure receiver email
  - View monitored products
  - Simple, user-friendly interface

### 🛡️ Admin Dashboard  
- **Purpose**: System administration
- **Features**:
  - System statistics and monitoring
  - Advanced product management
  - Full system configuration
  - User management framework
  - System logs and diagnostics
  - Email system testing
  - Start/stop monitoring controls

## 🔧 System Components

### Core Files
- `web_monitor.py` - Customer dashboard server
- `admin_monitor.py` - Admin dashboard server  
- `api_monitor.py` - Price monitoring engine
- `config.json` - System configuration
- `products.json` - Monitored products

### Configuration
- **Currency**: Indian Rupees (₹)
- **Supported Sites**: Amazon India, Flipkart
- **Check Interval**: Configurable (default: 5 minutes)
- **Email Alerts**: Gmail SMTP

## 📊 Monitoring System

The system uses API-based scraping for better reliability:
1. **Primary**: RapidAPI services
2. **Secondary**: ScrapFly API  
3. **Fallback**: Direct web scraping

## 🛠️ Installation

1. **Clone/Download** the project
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run launcher**:
   ```bash
   START_DASHBOARDS.bat
   ```

## 📁 Project Structure

```
smart-shopper/
├── price_tracker/           # Core monitoring system
│   ├── web/                # Web interface files
│   │   └── templates/      # HTML templates
│   ├── mailer.py          # Email system
│   ├── api_scraper.py     # API-based scraping
│   └── constants.py       # Configuration paths
├── web_monitor.py         # Customer dashboard
├── admin_monitor.py       # Admin dashboard
├── api_monitor.py         # Monitoring engine
├── config.json           # System configuration
├── products.json         # Monitored products
└── START_DASHBOARDS.*    # Launcher scripts
```

## 🔐 Security Notes

⚠️ **Development Mode**: Current implementation is for development/demo.

For production:
- Implement proper authentication
- Use HTTPS encryption
- Add input validation
- Enable rate limiting
- Add session management

## 📖 Documentation

- `DASHBOARD_README.md` - Detailed dashboard documentation
- `requirements.txt` - Python dependencies
- `setup.py` - Package configuration

## 🎯 Usage Examples

### Adding Products
1. Open customer dashboard
2. Enter product URL (Amazon India/Flipkart)
3. Set product name and alert price in ₹
4. Click "Add Product"

### Admin Management
1. Open admin dashboard
2. View system statistics
3. Manage products with advanced options
4. Configure system settings
5. Monitor system logs

## 🚨 Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure ports 5052 and 5053 are available
2. **Email issues**: Verify Gmail app password
3. **Config errors**: Check JSON syntax in config files

### Logs
- **Price alerts**: `~/price-tracker/price_alerts.log`
- **System logs**: Available in admin dashboard

## 🔄 Updates

The system automatically synchronizes configuration between dashboards. Changes made in either interface are reflected across the system.

## 💡 Tips

- Use the admin dashboard for system management
- Customer dashboard is perfect for end users
- Test email system through admin dashboard
- Monitor system health via admin statistics

---

**Happy Shopping! 🛍️**