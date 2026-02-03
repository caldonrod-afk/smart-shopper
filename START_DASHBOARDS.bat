@echo off
title Smart Shopper - Dashboard Launcher
color 0A

echo.
echo ========================================
echo    Smart Shopper Dashboard Launcher
echo ========================================
echo.

echo Starting Customer Dashboard...
start "Customer Dashboard" cmd /k "python web_monitor.py"

timeout /t 3 /nobreak >nul

echo Starting Admin Dashboard...
start "Admin Dashboard" cmd /k "python admin_monitor.py"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo    Dashboards Started Successfully!
echo ========================================
echo.
echo Customer Dashboard: http://127.0.0.1:5052
echo Admin Dashboard:    http://127.0.0.1:5053/admin
echo.
echo Press any key to open both dashboards in browser...
pause >nul

start http://127.0.0.1:5052
start http://127.0.0.1:5053/admin

echo.
echo Both dashboards are now running!
echo Close the dashboard windows to stop them.
echo.
pause