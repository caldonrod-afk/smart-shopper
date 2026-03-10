# Implementation Plan: Real-Time Price Tracking

## Overview

This implementation plan breaks down the real-time price tracking feature into discrete, incremental coding tasks. Each task builds on previous work and includes testing to validate functionality early. The plan integrates with the existing Smart Shopper infrastructure (Flask dashboards, APIScraper, Mailer) while adding new real-time capabilities.

## Tasks

- [ ] 1. Set up database schema and migrations
  - Create SQLite migration script for new tables (price_history, monitoring_config, alerts)
  - Add database indexes for performance (product_id, timestamp)
  - Create database manager utility functions for common operations
  - _Requirements: 2.4, 7.5, 8.1_

- [ ] 1.1 Write property test for database schema
  - **Property 7: Price History Persistence**
  - **Validates: Requirements 2.4, 8.1**

- [ ] 2. Implement Rate Limiter component
  - [ ] 2.1 Create RateLimiter class with token bucket algorithm
    - Implement per-domain token buckets
    - Add request timing randomization (±20%)
    - _Requirements: 3.1, 3.4_
  
  - [ ] 2.2 Write property test for per-domain rate limiting
    - **Property 9: Per-Domain Rate Limiting**
    - **Validates: Requirements 3.1**
  
  - [ ] 2.3 Write property test for request timing randomization
    - **Property 10: Request Timing Randomization**
    - **Validates: Requirements 3.4**
  
  - [ ] 2.4 Implement exponential backoff logic
    - Add backoff state tracking per domain
    - Implement 2^n minute backoff calculation (max 60 min)
    - Handle 429/503 status codes
    - _Requirements: 1.4, 3.2, 3.3_
  
  - [ ] 2.5 Write property test for exponential backoff
    - **Property 4: Exponential Backoff on Failures**
    - **Validates: Requirements 1.4, 3.2**
  
  - [ ] 2.6 Add request caching with 30-second TTL
    - Implement in-memory cache with expiration
    - Add cache hit/miss tracking
    - _Requirements: 4.3_
  
  - [ ] 2.7 Write property test for cache TTL enforcement
    - **Property 11: Cache TTL Enforcement**
    - **Validates: Requirements 4.3**

- [ ] 3. Implement PriceHistoryManager component
  - [ ] 3.1 Create PriceHistoryManager class
    - Implement record_price_check() method
    - Implement get_price_history() with date range filtering
    - Add database connection pooling
    - _Requirements: 2.4, 8.1_
  
  - [ ] 3.2 Add data compression for old records
    - Implement compression for data older than 30 days
    - Use gzip compression for JSON serialized data
    - _Requirements: 8.2_
  
  - [ ] 3.3 Write property test for data compression
    - **Property 23: Data Compression After Threshold**
    - **Validates: Requirements 8.2**
  
  - [ ] 3.4 Implement retention policy enforcement
    - Add configurable retention policies
    - Implement automatic cleanup of old data
    - _Requirements: 8.3_
  
  - [ ] 3.5 Write property test for retention policy
    - **Property 24: Retention Policy Enforcement**
    - **Validates: Requirements 8.3**
  
  - [ ] 3.6 Add CSV export functionality
    - Implement export_to_csv() method
    - Include columns: timestamp, price, source
    - _Requirements: 8.5_
  
  - [ ] 3.7 Write property test for CSV export
    - **Property 25: CSV Export Completeness**
    - **Validates: Requirements 8.5**
  
  - [ ] 3.8 Implement price trend calculation
    - Add get_price_trend() for 24h, 7d, 30d periods
    - Calculate min, max, avg, trend direction
    - _Requirements: 8.4_

- [ ] 4. Checkpoint - Ensure data layer tests pass
  - Run all database and price history tests
  - Verify database schema is correct
  - Ensure all tests pass, ask the user if questions arise

- [ ] 5. Implement ConfigurationManager component
  - [ ] 5.1 Create ConfigurationManager class
    - Implement load_config() and save_config() methods
    - Add configuration validation logic
    - Implement automatic backup before changes
    - _Requirements: 6.1, 6.4_
  
  - [ ] 5.2 Write property test for configuration backup
    - **Property 18: Configuration Backup Creation**
    - **Validates: Requirements 6.4**
  
  - [ ] 5.3 Add monitoring profile presets
    - Define Conservative (30min), Balanced (10min), Aggressive (2min) profiles
    - Implement apply_profile() method
    - _Requirements: 6.2_
  
  - [ ] 5.4 Write unit test for profile presets
    - Test that all three profiles exist with correct intervals
    - _Requirements: 6.2_
  
  - [ ] 5.5 Implement hot-reload functionality
    - Add reload_config() method that applies changes without restart
    - Integrate with scheduler to update running jobs
    - _Requirements: 6.1_
  
  - [ ] 5.6 Write property test for hot configuration reload
    - **Property 17: Hot Configuration Reload**
    - **Validates: Requirements 6.1**
  
  - [ ] 5.7 Add interval validation with warnings
    - Validate intervals are in range [1, 60]
    - Display warning for intervals < 5 minutes
    - _Requirements: 1.1, 1.3, 6.3_
  
  - [ ] 5.8 Write property test for interval validation
    - **Property 1: Interval Validation and Configuration**
    - **Validates: Requirements 1.1, 6.3**
  
  - [ ] 5.9 Write property test for low-frequency warning
    - **Property 3: Low-Frequency Warning Display**
    - **Validates: Requirements 1.3**

- [ ] 6. Implement RealTimeScheduler component
  - [ ] 6.1 Create RealTimeScheduler class using APScheduler
    - Initialize BackgroundScheduler
    - Implement add_product_monitor() method
    - Implement remove_product_monitor() method
    - _Requirements: 1.1, 1.2_
  
  - [ ] 6.2 Add per-product interval management
    - Implement update_interval() method
    - Store job references in dictionary
    - Implement get_next_check_time() method
    - _Requirements: 1.2_
  
  - [ ] 6.3 Write property test for per-product scheduling
    - **Property 2: Per-Product Schedule Independence**
    - **Validates: Requirements 1.2**
  
  - [ ] 6.4 Implement pause/resume functionality
    - Add pause_monitoring() method
    - Add resume_monitoring() method
    - Update monitoring_config table status
    - _Requirements: 7.1_
  
  - [ ] 6.5 Add graceful shutdown with state persistence
    - Implement shutdown() method that saves state
    - Save all job schedules to database
    - Restore jobs on startup
    - _Requirements: 4.5, 7.5_
  
  - [ ] 6.6 Write property test for graceful shutdown
    - **Property 13: Graceful Shutdown Data Preservation**
    - **Validates: Requirements 4.5, 7.5**
  
  - [ ] 6.7 Integrate RateLimiter with scheduler
    - Check rate limiter before each scraping job
    - Reschedule job if rate limited
    - _Requirements: 3.1, 3.2_

- [ ] 7. Implement AlertManager component
  - [ ] 7.1 Create AlertManager class
    - Implement create_alert() method
    - Add alert priority logic (high for target_reached)
    - Store alerts in database
    - _Requirements: 2.2_
  
  - [ ] 7.2 Write property test for alert content
    - **Property 6: Alert Content Completeness**
    - **Validates: Requirements 2.2**
  
  - [ ] 7.3 Implement alert batching logic
    - Add 60-second batching window
    - Implement should_batch_alert() method
    - Implement batch_and_send_alerts() method
    - _Requirements: 2.5_
  
  - [ ] 7.4 Write property test for notification batching
    - **Property 8: Notification Batching**
    - **Validates: Requirements 2.5**
  
  - [ ] 7.5 Add alert timing guarantee
    - Ensure alerts are logged within 30 seconds of detection
    - Use threading or async for non-blocking alert creation
    - _Requirements: 2.1_
  
  - [ ] 7.6 Write property test for alert timing
    - **Property 5: Alert Timing Guarantee**
    - **Validates: Requirements 2.1**
  
  - [ ] 7.7 Integrate with existing Mailer
    - Use existing mailer.send_mail() for email alerts
    - Add alert history tracking
    - _Requirements: 2.2_

- [ ] 8. Checkpoint - Ensure core monitoring components work
  - Test scheduler with multiple products
  - Verify rate limiting and backoff work correctly
  - Test alert creation and batching
  - Ensure all tests pass, ask the user if questions arise

- [ ] 9. Implement RealtimeUpdateService for SSE
  - [ ] 9.1 Create RealtimeUpdateService class
    - Implement client registration/unregistration
    - Add message queue for updates
    - Implement broadcast methods
    - _Requirements: 5.1_
  
  - [ ] 9.2 Add Flask SSE endpoint
    - Create /api/stream endpoint
    - Implement event_stream generator
    - Handle client disconnections gracefully
    - _Requirements: 5.1_
  
  - [ ] 9.3 Write property test for real-time update latency
    - **Property 14: Real-Time Update Latency**
    - **Validates: Requirements 5.1**
  
  - [ ] 9.4 Integrate SSE with AlertManager
    - Broadcast price updates to connected clients
    - Broadcast status updates (monitoring, paused, error)
    - _Requirements: 2.3, 5.3_

- [ ] 10. Implement error handling and resilience
  - [ ] 10.1 Create ErrorHandler class
    - Implement handle_scraping_error() method
    - Implement handle_network_outage() method
    - Implement handle_database_error() method
    - _Requirements: 7.1, 7.2, 7.4_
  
  - [ ] 10.2 Write property test for fault isolation
    - **Property 19: Fault Isolation**
    - **Validates: Requirements 7.1**
  
  - [ ] 10.3 Implement task queuing for network outages
    - Queue monitoring tasks when network is down
    - Resume queued tasks when connectivity returns
    - _Requirements: 7.2_
  
  - [ ] 10.4 Write property test for task queuing
    - **Property 20: Task Queuing During Network Outage**
    - **Validates: Requirements 7.2**
  
  - [ ] 10.5 Add invalid URL detection
    - Detect 404 and invalid responses
    - Mark products as inactive
    - Send notification to user
    - _Requirements: 7.3_
  
  - [ ] 10.6 Write property test for invalid URL handling
    - **Property 21: Invalid URL Handling**
    - **Validates: Requirements 7.3**
  
  - [ ] 10.7 Implement parsing error fallback
    - Log detailed error information
    - Try alternative parsing strategies
    - _Requirements: 7.4_
  
  - [ ] 10.8 Write property test for parsing error fallback
    - **Property 22: Parsing Error Fallback**
    - **Validates: Requirements 7.4**

- [ ] 11. Implement resource monitoring and optimization
  - [ ] 11.1 Add memory usage monitoring
    - Track current memory usage
    - Trigger cleanup at 500MB threshold
    - _Requirements: 4.2_
  
  - [ ] 11.2 Write property test for memory-based cleanup
    - **Property 12: Memory-Based Cleanup Trigger**
    - **Validates: Requirements 4.2**
  
  - [ ] 11.3 Add CPU usage monitoring
    - Track CPU usage percentage
    - Reduce monitoring frequency when CPU > 80%
    - _Requirements: 4.4_
  
  - [ ] 11.4 Implement connection pooling
    - Use requests.Session for connection reuse
    - Configure pool size and timeout
    - _Requirements: 4.1_

- [ ] 12. Update Customer Dashboard (web_monitor.py)
  - [ ] 12.1 Add SSE client connection in frontend
    - Add JavaScript EventSource for /api/stream
    - Handle incoming price updates
    - Update UI without page refresh
    - _Requirements: 5.1, 5.2_
  
  - [ ] 12.2 Add monitoring frequency configuration UI
    - Add interval input field per product
    - Add profile selector (Conservative/Balanced/Aggressive)
    - Display warning for intervals < 5 minutes
    - _Requirements: 1.1, 1.3, 6.2_
  
  - [ ] 12.3 Add real-time status indicators
    - Display monitoring status (active, paused, error)
    - Show last check time per product
    - Show next check time per product
    - _Requirements: 5.2, 5.3_
  
  - [ ] 12.4 Write property test for UI state display
    - **Property 15: UI State Display Accuracy**
    - **Validates: Requirements 5.2, 5.3**
  
  - [ ] 12.5 Add connection error handling
    - Display error messages on connection failure
    - Implement automatic reconnection
    - _Requirements: 5.4_
  
  - [ ] 12.6 Write property test for connection error recovery
    - **Property 16: Connection Error Recovery**
    - **Validates: Requirements 5.4**
  
  - [ ] 12.7 Add price trend visualization
    - Create chart component for 24h, 7d, 30d trends
    - Use Chart.js or similar library
    - Display min, max, avg prices
    - _Requirements: 8.4_

- [ ] 13. Update Admin Dashboard (admin_monitor.py)
  - [ ] 13.1 Add system monitoring dashboard
    - Display total products, active alerts, system uptime
    - Show API usage statistics
    - Display resource usage (CPU, memory, disk)
    - _Requirements: 3.5, 4.2, 4.4_
  
  - [ ] 13.2 Add rate limiting status display
    - Show per-domain rate limit status
    - Display backoff timers and next retry times
    - _Requirements: 3.5_
  
  - [ ] 13.3 Add configuration management UI
    - Allow editing monitoring profiles
    - Add configuration validation feedback
    - Show configuration backup history
    - _Requirements: 6.1, 6.3, 6.4_
  
  - [ ] 13.4 Add alert history view
    - Display recent alerts with timestamps
    - Filter by product, date range, alert type
    - Show alert priority and notification status
    - _Requirements: 2.2_
  
  - [ ] 13.5 Add CSV export functionality
    - Add export button per product
    - Generate and download CSV files
    - _Requirements: 8.5_

- [ ] 14. Create API endpoints for new features
  - [ ] 14.1 Add monitoring control endpoints
    - POST /api/monitoring/start - Start monitoring for product
    - POST /api/monitoring/stop - Stop monitoring for product
    - POST /api/monitoring/pause - Pause monitoring for product
    - POST /api/monitoring/resume - Resume monitoring for product
    - _Requirements: 1.2_
  
  - [ ] 14.2 Add configuration endpoints
    - GET /api/config/profiles - Get monitoring profiles
    - POST /api/config/interval - Update product interval
    - POST /api/config/apply_profile - Apply profile to products
    - _Requirements: 6.1, 6.2_
  
  - [ ] 14.3 Add price history endpoints
    - GET /api/price_history/:product_id - Get price history
    - GET /api/price_trend/:product_id/:period - Get trend data
    - GET /api/export_csv/:product_id - Export to CSV
    - _Requirements: 8.1, 8.4, 8.5_
  
  - [ ] 14.4 Add alert endpoints
    - GET /api/alerts - Get recent alerts
    - GET /api/alerts/:product_id - Get alerts for product
    - _Requirements: 2.2_

- [ ] 15. Checkpoint - Integration testing
  - Test complete monitoring workflow end-to-end
  - Verify SSE updates reach browser
  - Test all API endpoints
  - Verify database operations work correctly
  - Ensure all tests pass, ask the user if questions arise

- [ ] 16. Add database migration script
  - [ ] 16.1 Create migration script
    - Check if new tables exist
    - Create tables if missing
    - Add indexes
    - Migrate existing products to new schema
    - _Requirements: 7.5_
  
  - [ ] 16.2 Add rollback capability
    - Create backup before migration
    - Implement rollback function
    - _Requirements: 6.4_

- [ ] 17. Update configuration files
  - [ ] 17.1 Extend config.json schema
    - Add default_monitoring_interval field
    - Add enable_real_time_monitoring field
    - Add resource_limits section (memory, cpu thresholds)
    - Maintain backward compatibility
    - _Requirements: 6.1_
  
  - [ ] 17.2 Update products.json schema
    - Add monitoring_interval field per product
    - Add status field (active, paused, error)
    - Migrate existing products with default values
    - _Requirements: 1.2_

- [ ] 18. Add logging and monitoring
  - [ ] 18.1 Implement structured logging
    - Log all monitoring activities with timestamps
    - Log API usage per provider
    - Log rate limiting events
    - Log errors with full context
    - _Requirements: 7.4_
  
  - [ ] 18.2 Add performance metrics
    - Track scraping latency per API
    - Track database query performance
    - Track memory and CPU usage over time
    - _Requirements: 4.1, 4.2, 4.4_

- [ ] 19. Write integration tests
  - [ ] 19.1 Test complete monitoring workflow
    - Add product → Start monitoring → Detect price change → Send alert
    - _Requirements: 1.1, 1.2, 2.1, 2.2_
  
  - [ ] 19.2 Test rate limiting across multiple products
    - Monitor multiple products from same domain
    - Verify rate limiting is applied correctly
    - _Requirements: 3.1, 3.2_
  
  - [ ] 19.3 Test graceful shutdown and restart
    - Start monitoring → Shutdown → Restart → Verify state restored
    - _Requirements: 4.5, 7.5_
  
  - [ ] 19.4 Test SSE real-time updates
    - Connect client → Trigger price update → Verify client receives update
    - _Requirements: 5.1_

- [ ] 20. Update documentation
  - [ ] 20.1 Update README with new features
    - Document real-time monitoring capabilities
    - Add configuration examples
    - Add API endpoint documentation
    - _Requirements: All_
  
  - [ ] 20.2 Create user guide
    - How to configure monitoring intervals
    - How to use monitoring profiles
    - How to view price trends
    - How to export data
    - _Requirements: 1.1, 6.2, 8.4, 8.5_
  
  - [ ] 20.3 Create admin guide
    - How to monitor system health
    - How to manage rate limiting
    - How to configure retention policies
    - _Requirements: 3.5, 4.2, 8.3_

- [ ] 21. Final checkpoint - Complete system test
  - Run all unit tests and property tests
  - Test with real e-commerce URLs
  - Verify email notifications work
  - Test with multiple concurrent users
  - Verify all dashboards display correctly
  - Ensure all tests pass, ask the user if questions arise

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- The implementation maintains backward compatibility with existing system
- All new features integrate with existing Flask dashboards and APIScraper
