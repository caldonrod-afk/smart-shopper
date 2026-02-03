# Smart Shopper Dashboard Launcher - PowerShell Version
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Smart Shopper Dashboard Launcher" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Start Customer Dashboard
Write-Host "📱 Starting Customer Dashboard..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python web_monitor.py" -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Admin Dashboard
Write-Host "🛡️ Starting Admin Dashboard..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python admin_monitor.py" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Dashboards Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Customer Dashboard: http://127.0.0.1:5052" -ForegroundColor White
Write-Host "🛡️ Admin Dashboard:    http://127.0.0.1:5053/admin" -ForegroundColor White
Write-Host ""

# Ask user if they want to open browsers
$openBrowser = Read-Host "Open dashboards in browser? (y/n)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Write-Host "🌐 Opening dashboards in browser..." -ForegroundColor Green
    Start-Process "http://127.0.0.1:5052"
    Start-Process "http://127.0.0.1:5053/admin"
}

Write-Host ""
Write-Host "✅ Both dashboards are now running!" -ForegroundColor Green
Write-Host "💡 Close the dashboard windows to stop them." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this launcher..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")