# Smart Shopper - Dual Dashboard System

## Overview
Smart Shopper now features two separate dashboards designed for different user types:

### 📱 Customer Dashboard
- **URL**: http://127.0.0.1:5052
- **Purpose**: End-user interface for price monitoring
- **Features**:
  - Add products to monitor
  - Set price alerts
  - Configure receiver email
  - View monitored products
  - Simple, user-friendly interface

### 🛡️ Admin Dashboard
- **URL**: http://127.0.0.1:5053/admin
- **Purpose**: System administration and management
- **Features**:
  - System statistics and monitoring
  - Advanced product management
  - System configuration
  - User management
  - System logs and diagnostics
  - Email system testing
  - Bulk operations

## Quick Start

### Option 1: Use Launcher Scripts
```bash
# Windows Batch
START_DASHBOARDS.bat

# Windows PowerShell
START_DASHBOARDS.ps1

# Python (Cross-platform)
python start_dashboards.py
```

### Option 2: Manual Start
```bash
# Terminal 1 - Customer Dashboard
python web_monitor.py

# Terminal 2 - Admin Dashboard  
python admin_monitor.py
```

## Dashboard Features Comparison

| Feature | Customer Dashboard | Admin Dashboard |
|---------|-------------------|-----------------|
| Add Products | ✅ Basic | ✅ Advanced (with categories) |
| View Products | ✅ Simple list | ✅ Detailed table with actions |
| Email Config | ✅ Receiver only | ✅ Full email settings |
| System Stats | ❌ | ✅ Comprehensive |
| User Management | ❌ | ✅ |
| System Logs | ❌ | ✅ |
| Bulk Operations | ❌ | ✅ |
| System Control | ❌ | ✅ Start/Stop monitoring |

## Admin Dashboard Sections

### 1. System Statistics
- Total products being monitored
- Active price alerts
- System uptime
- Last check timestamp
- Real-time monitoring status

### 2. Product Management
- View all products in detailed table
- Add products with categories
- Edit existing products
- Delete products
- Bulk import (coming soon)

### 3. System Configuration
- Email settings (sender, password, receiver)
- Monitoring intervals
- Notification preferences
- System preferences

### 4. System Logs
- View recent system activities
- Price alert history
- Error logs
- System events

### 5. User Management
- Manage user accounts (placeholder)
- User roles and permissions
- Access control

## API Endpoints

### Customer Dashboard APIs
- `GET /api/products` - Get products
- `POST /api/add_product` - Add product
- `GET /api/receiver_email` - Get receiver email
- `POST /api/update_receiver_email` - Update receiver email
- `GET /api/status` - Get monitoring status

### Admin Dashboard APIs
- `GET /api/admin/stats` - System statistics
- `GET /api/admin/products` - Detailed product info
- `POST /api/admin/add_product` - Add product (admin)
- `POST /api/admin/delete_product` - Delete product
- `GET /api/admin/config` - System configuration
- `POST /api/admin/update_config` - Update configuration
- `GET /api/admin/logs` - System logs
- `POST /api/admin/start_monitoring` - Start monitoring
- `POST /api/admin/stop_monitoring` - Stop monitoring
- `POST /api/admin/test_email` - Test email system

## Security Notes

⚠️ **Important**: The current implementation is for development/demo purposes.

For production use, implement:
- Proper authentication for admin dashboard
- HTTPS encryption
- Input validation and sanitization
- Rate limiting
- Session management
- CSRF protection

## Configuration Files

Both dashboards use the same configuration files:
- `config.json` (current directory)
- `~/price-tracker/config.json` (home directory)

Changes made in either dashboard are synchronized across both.

## Monitoring Integration

The admin dashboard provides controls to:
- Start/stop the monitoring system
- View monitoring status
- Test email functionality
- Monitor system health

## Customization

### Adding New Features
1. **Customer Dashboard**: Edit `price_tracker/web/templates/monitor_dashboard.html` and `web_monitor.py`
2. **Admin Dashboard**: Edit `price_tracker/web/templates/admin_dashboard.html` and `admin_monitor.py`

### Styling
Both dashboards use embedded CSS for easy customization. Modify the `<style>` sections in the HTML templates.

## Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure ports 5052 and 5053 are available
2. **Config file errors**: Check JSON syntax in config files
3. **Email issues**: Verify Gmail app password and settings

### Logs Location
- Price alerts: `~/price-tracker/price_alerts.log`
- System logs: Available through admin dashboard

## Future Enhancements

- [ ] User authentication system
- [ ] Database integration
- [ ] Real-time notifications
- [ ] Mobile responsive design
- [ ] API rate limiting
- [ ] Backup/restore functionality
- [ ] Advanced analytics
- [ ] Multi-language support

## Support

For issues or questions:
1. Check the logs in admin dashboard
2. Verify configuration files
3. Test email system through admin dashboard
4. Review console output from both dashboard processes