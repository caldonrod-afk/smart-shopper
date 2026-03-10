# Design Document: Real-Time Price Tracking

## Overview

This design enhances the existing Smart Shopper price monitoring application with real-time tracking capabilities. The current system monitors products at fixed 60-minute intervals. This enhancement introduces configurable per-product monitoring frequencies (1-60 minutes), intelligent rate management, real-time web interface updates, and comprehensive price history tracking.

The design integrates with the existing dual-dashboard architecture (Customer dashboard on port 5052, Admin dashboard on port 5053), leverages the multi-API fallback system (SerpAPI → RapidAPI → ScrapFly → Free Price API → Fallback scraping), and maintains backward compatibility with the current monitoring infrastructure.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Layer (Flask)                        │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ Customer Dashboard│         │ Admin Dashboard  │         │
│  │   (Port 5052)    │         │   (Port 5053)    │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                             │                    │
│           └──────────┬──────────────────┘                    │
│                      │                                       │
│              ┌───────▼────────┐                             │
│              │  WebSocket/SSE  │                             │
│              │   Push Service  │                             │
│              └───────┬────────┘                             │
└──────────────────────┼──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Monitoring Core                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Real-Time Scheduler (APScheduler)              │ │
│  │  - Per-product configurable intervals (1-60 min)       │ │
│  │  - Dynamic schedule updates                            │ │
│  │  - Job persistence across restarts                     │ │
│  └────────────────────┬───────────────────────────────────┘ │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │         Rate Limiter & Backoff Manager                 │ │
│  │  - Per-domain request throttling                       │ │
│  │  - Exponential backoff (2min base)                     │ │
│  │  - Request timing randomization (±20%)                 │ │
│  └────────────────────┬───────────────────────────────────┘ │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │         Price Scraper (Existing APIScraper)            │ │
│  │  - Multi-API fallback chain                            │ │
│  │  - Connection pooling                                  │ │
│  │  - Request caching (30s TTL)                           │ │
│  └────────────────────┬───────────────────────────────────┘ │
└───────────────────────┼──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                  Data & Storage Layer                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │  SQLite Database │  │  Price History   │  │   Config   │ │
│  │  - Products      │  │  - Timestamps    │  │  - Backup  │ │
│  │  - Price History │  │  - Compression   │  │  - Profiles│ │
│  │  - Alerts        │  │  - Retention     │  │            │ │
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

1. **Scheduler**: Use APScheduler for flexible, per-product scheduling with job persistence
2. **Real-Time Updates**: Implement Server-Sent Events (SSE) for browser push (simpler than WebSocket for one-way updates)
3. **Database**: Extend existing SQLite database for price history and monitoring state
4. **Rate Limiting**: Implement token bucket algorithm per domain with exponential backoff
5. **Caching**: Add Redis-like in-memory cache with TTL for request deduplication
6. **Backward Compatibility**: Maintain existing API interfaces, add new endpoints for real-time features

## Components and Interfaces

### 1. Real-Time Scheduler Component

**Purpose**: Manage per-product monitoring schedules with configurable intervals

**Class**: `RealTimeScheduler`

```python
class RealTimeScheduler:
    def __init__(self, db_manager, rate_limiter, scraper):
        self.scheduler = BackgroundScheduler()
        self.db = db_manager
        self.rate_limiter = rate_limiter
        self.scraper = scraper
        self.jobs = {}  # product_id -> job mapping
    
    def add_product_monitor(self, product_id: str, url: str, 
                           interval_minutes: int, warn_price: float) -> bool:
        """Add or update monitoring job for a product"""
        pass
    
    def remove_product_monitor(self, product_id: str) -> bool:
        """Remove monitoring job for a product"""
        pass
    
    def update_interval(self, product_id: str, new_interval: int) -> bool:
        """Update monitoring interval for a product"""
        pass
    
    def get_next_check_time(self, product_id: str) -> datetime:
        """Get next scheduled check time for a product"""
        pass
    
    def pause_monitoring(self, product_id: str) -> bool:
        """Temporarily pause monitoring for a product"""
        pass
    
    def resume_monitoring(self, product_id: str) -> bool:
        """Resume paused monitoring for a product"""
        pass
    
    def start(self):
        """Start the scheduler"""
        pass
    
    def shutdown(self, wait: bool = True):
        """Gracefully shutdown scheduler"""
        pass
```

**Integration**: Extends existing monitoring system by wrapping APIScraper calls with scheduling logic

### 2. Rate Limiter Component

**Purpose**: Implement intelligent per-domain rate limiting with exponential backoff

**Class**: `RateLimiter`

```python
class RateLimiter:
    def __init__(self):
        self.domain_buckets = {}  # domain -> TokenBucket
        self.backoff_state = {}   # domain -> BackoffState
        self.request_cache = {}   # url -> CachedResponse
    
    def can_make_request(self, url: str) -> Tuple[bool, Optional[float]]:
        """Check if request can be made, return (allowed, retry_after_seconds)"""
        pass
    
    def record_request(self, url: str, success: bool, status_code: int):
        """Record request result and update rate limiting state"""
        pass
    
    def get_backoff_delay(self, domain: str) -> float:
        """Get current backoff delay for domain"""
        pass
    
    def reset_backoff(self, domain: str):
        """Reset backoff state for domain"""
        pass
    
    def get_cached_response(self, url: str) -> Optional[dict]:
        """Get cached response if available and not expired"""
        pass
    
    def cache_response(self, url: str, response: dict, ttl: int = 30):
        """Cache response with TTL"""
        pass
    
    def randomize_delay(self, base_delay: float) -> float:
        """Add ±20% randomization to delay"""
        pass
```

**Token Bucket Algorithm**:
- Each domain gets a token bucket with configurable rate (e.g., 10 requests/minute)
- Tokens refill at constant rate
- Request consumes one token
- If no tokens available, request is delayed

**Exponential Backoff**:
- On 429/503 responses: delay = 2^(failure_count) minutes, starting at 2 minutes
- Max backoff: 60 minutes
- Reset on successful request

### 3. Price History Manager Component

**Purpose**: Store, compress, and retrieve price history data

**Class**: `PriceHistoryManager`

```python
class PriceHistoryManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    def record_price_check(self, product_id: str, price: float, 
                          timestamp: datetime, source: str) -> bool:
        """Record a price check with precise timestamp"""
        pass
    
    def get_price_history(self, product_id: str, 
                         start_date: datetime, 
                         end_date: datetime) -> List[PricePoint]:
        """Retrieve price history for time range"""
        pass
    
    def compress_old_data(self, days_threshold: int = 30):
        """Compress price history older than threshold"""
        pass
    
    def apply_retention_policy(self, policy: RetentionPolicy):
        """Apply data retention policy"""
        pass
    
    def export_to_csv(self, product_id: str, output_path: str) -> bool:
        """Export price history to CSV"""
        pass
    
    def get_price_trend(self, product_id: str, period: str) -> TrendData:
        """Get aggregated trend data for period (24h, 7d, 30d)"""
        pass
```

**Database Schema Extension**:

```sql
-- New table for price history
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    price REAL NOT NULL,
    timestamp DATETIME NOT NULL,
    source TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX idx_price_history_product_time 
ON price_history(product_id, timestamp);

-- New table for monitoring configuration
CREATE TABLE monitoring_config (
    product_id TEXT PRIMARY KEY,
    interval_minutes INTEGER NOT NULL,
    last_check DATETIME,
    next_check DATETIME,
    status TEXT,  -- 'active', 'paused', 'error'
    failure_count INTEGER DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- New table for alerts
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    alert_type TEXT,  -- 'price_drop', 'target_reached'
    old_price REAL,
    new_price REAL,
    timestamp DATETIME NOT NULL,
    notified BOOLEAN DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### 4. Real-Time Update Service Component

**Purpose**: Push real-time updates to connected web clients

**Class**: `RealtimeUpdateService`

```python
class RealtimeUpdateService:
    def __init__(self):
        self.clients = set()  # Connected SSE clients
        self.update_queue = queue.Queue()
    
    def register_client(self, client_id: str):
        """Register a new SSE client"""
        pass
    
    def unregister_client(self, client_id: str):
        """Unregister SSE client"""
        pass
    
    def broadcast_price_update(self, product_id: str, price_data: dict):
        """Broadcast price update to all connected clients"""
        pass
    
    def broadcast_status_update(self, product_id: str, status: str):
        """Broadcast monitoring status update"""
        pass
    
    def send_to_client(self, client_id: str, message: dict):
        """Send message to specific client"""
        pass
```

**Flask SSE Endpoint**:

```python
@app.route('/api/stream')
def stream():
    """SSE endpoint for real-time updates"""
    def event_stream():
        client_id = str(uuid.uuid4())
        realtime_service.register_client(client_id)
        try:
            while True:
                message = realtime_service.get_message_for_client(client_id)
                if message:
                    yield f"data: {json.dumps(message)}\n\n"
                time.sleep(1)
        finally:
            realtime_service.unregister_client(client_id)
    
    return Response(event_stream(), mimetype='text/event-stream')
```

### 5. Configuration Manager Component

**Purpose**: Manage monitoring profiles and configuration with hot-reload

**Class**: `ConfigurationManager`

```python
class ConfigurationManager:
    PROFILES = {
        'conservative': {'interval': 30, 'description': 'Low frequency, minimal load'},
        'balanced': {'interval': 10, 'description': 'Moderate frequency'},
        'aggressive': {'interval': 2, 'description': 'High frequency, may hit rate limits'}
    }
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = {}
        self.backup_path = config_path + '.backup'
    
    def load_config(self) -> dict:
        """Load configuration from file"""
        pass
    
    def save_config(self, config: dict, create_backup: bool = True) -> bool:
        """Save configuration with optional backup"""
        pass
    
    def validate_config(self, config: dict) -> Tuple[bool, List[str]]:
        """Validate configuration and return errors"""
        pass
    
    def apply_profile(self, profile_name: str, product_ids: List[str]) -> bool:
        """Apply monitoring profile to products"""
        pass
    
    def get_optimal_settings(self, system_metrics: dict) -> dict:
        """Suggest optimal settings based on system resources"""
        pass
    
    def reload_config(self) -> bool:
        """Hot-reload configuration without restart"""
        pass
```

### 6. Alert Manager Component

**Purpose**: Manage price alerts with batching and prioritization

**Class**: `AlertManager`

```python
class AlertManager:
    def __init__(self, mailer, db_manager, realtime_service):
        self.mailer = mailer
        self.db = db_manager
        self.realtime = realtime_service
        self.pending_alerts = []
        self.batch_window = 60  # seconds
    
    def create_alert(self, product_id: str, alert_type: str, 
                    old_price: float, new_price: float) -> Alert:
        """Create a new price alert"""
        pass
    
    def should_batch_alert(self, alert: Alert) -> bool:
        """Determine if alert should be batched"""
        pass
    
    def send_alert(self, alert: Alert):
        """Send alert via email and real-time update"""
        pass
    
    def batch_and_send_alerts(self):
        """Process pending alerts and send batched notifications"""
        pass
    
    def get_alert_history(self, product_id: str, limit: int = 50) -> List[Alert]:
        """Get alert history for product"""
        pass
```

## Data Models

### Product Model

```python
@dataclass
class Product:
    id: str
    url: str
    name: str
    warn_price: float
    category: str
    added_date: datetime
    status: str  # 'active', 'paused', 'error', 'inactive'
```

### MonitoringConfig Model

```python
@dataclass
class MonitoringConfig:
    product_id: str
    interval_minutes: int
    last_check: Optional[datetime]
    next_check: Optional[datetime]
    status: str
    failure_count: int
    backoff_until: Optional[datetime]
```

### PricePoint Model

```python
@dataclass
class PricePoint:
    product_id: str
    price: float
    timestamp: datetime
    source: str  # 'SerpAPI', 'RapidAPI', etc.
```

### Alert Model

```python
@dataclass
class Alert:
    id: int
    product_id: str
    alert_type: str  # 'price_drop', 'target_reached'
    old_price: Optional[float]
    new_price: float
    price_difference: float
    timestamp: datetime
    notified: bool
    priority: str  # 'high', 'normal'
```

### TrendData Model

```python
@dataclass
class TrendData:
    product_id: str
    period: str  # '24h', '7d', '30d'
    data_points: List[PricePoint]
    min_price: float
    max_price: float
    avg_price: float
    current_price: float
    trend_direction: str  # 'up', 'down', 'stable'
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Interval Validation and Configuration

*For any* monitoring interval value, the system should accept values in the range [1, 60] minutes and reject all other values with appropriate validation messages.

**Validates: Requirements 1.1, 6.3**

### Property 2: Per-Product Schedule Independence

*For any* set of products with different monitoring intervals, advancing time by T minutes should result in each product being checked exactly floor(T / interval) times, independent of other products' schedules.

**Validates: Requirements 1.2**

### Property 3: Low-Frequency Warning Display

*For any* monitoring frequency below 5 minutes, the system should display a rate limiting warning to the user.

**Validates: Requirements 1.3**

### Property 4: Exponential Backoff on Failures

*For any* sequence of consecutive failures, the backoff delay should follow the pattern: delay_n = 2^n minutes (starting at 2 minutes), up to a maximum of 60 minutes.

**Validates: Requirements 1.4, 3.2**

### Property 5: Alert Timing Guarantee

*For any* detected price change, the time between detection and alert logging should be less than or equal to 30 seconds.

**Validates: Requirements 2.1**

### Property 6: Alert Content Completeness

*For any* alert where target price is reached, the alert record should contain all required fields: timestamp, old_price, new_price, and price_difference.

**Validates: Requirements 2.2**

### Property 7: Price History Persistence

*For any* price check performed, the system should store a record with product_id, price, timestamp, and source that can be retrieved later.

**Validates: Requirements 2.4, 8.1**

### Property 8: Notification Batching

*For any* sequence of N price changes occurring within a 60-second window, the system should send at most 1 batched notification rather than N individual notifications.

**Validates: Requirements 2.5**

### Property 9: Per-Domain Rate Limiting

*For any* two products from different domains, rate limiting applied to one domain should not affect the request rate to the other domain.

**Validates: Requirements 3.1**

### Property 10: Request Timing Randomization

*For any* scheduled request with base interval I, the actual request time should fall within the range [I * 0.8, I * 1.2].

**Validates: Requirements 3.4**

### Property 11: Cache TTL Enforcement

*For any* cached request, making the same request within 30 seconds should return the cached response, and making the request after 30 seconds should trigger a new fetch.

**Validates: Requirements 4.3**

### Property 12: Memory-Based Cleanup Trigger

*For any* system state where memory usage exceeds 500MB, the cleanup process should be triggered and should reduce memory usage.

**Validates: Requirements 4.2**

### Property 13: Graceful Shutdown Data Preservation

*For any* monitoring state at shutdown time, restarting the application should restore the same monitoring configuration and scheduled jobs.

**Validates: Requirements 4.5, 7.5**

### Property 14: Real-Time Update Latency

*For any* price update event, all connected clients should receive the update within 10 seconds of the event occurring.

**Validates: Requirements 5.1**

### Property 15: UI State Display Accuracy

*For any* product with a last check time T and status S, the web interface should display T and S correctly when queried.

**Validates: Requirements 5.2, 5.3**

### Property 16: Connection Error Recovery

*For any* connection failure, the system should display an error message and automatically retry the connection.

**Validates: Requirements 5.4**

### Property 17: Hot Configuration Reload

*For any* configuration change made while monitoring is active, the new configuration should take effect without requiring application restart.

**Validates: Requirements 6.1**

### Property 18: Configuration Backup Creation

*For any* configuration change, a backup of the previous configuration should be created before applying the new configuration.

**Validates: Requirements 6.4**

### Property 19: Fault Isolation

*For any* product that fails to scrape, all other products should continue to be monitored without interruption.

**Validates: Requirements 7.1**

### Property 20: Task Queuing During Network Outage

*For any* monitoring tasks scheduled during a network outage, those tasks should be queued and executed when network connectivity is restored.

**Validates: Requirements 7.2**

### Property 21: Invalid URL Handling

*For any* product URL that returns a 404 or invalid response, the product should be marked as inactive and a notification should be sent to the user.

**Validates: Requirements 7.3**

### Property 22: Parsing Error Fallback

*For any* parsing error encountered, the system should log detailed error information and attempt at least one alternative parsing strategy before failing.

**Validates: Requirements 7.4**

### Property 23: Data Compression After Threshold

*For any* price history data older than 30 days, the data should be stored in compressed format.

**Validates: Requirements 8.2**

### Property 24: Retention Policy Enforcement

*For any* configured retention policy with threshold T days, price history data older than T days should be removed from the database.

**Validates: Requirements 8.3**

### Property 25: CSV Export Completeness

*For any* product's price history, exporting to CSV should produce a valid CSV file containing all price records with columns: timestamp, price, source.

**Validates: Requirements 8.5**

## Error Handling

### Error Categories and Strategies

1. **Network Errors** (Connection timeout, DNS failure, SSL errors)
   - Strategy: Retry with exponential backoff, queue tasks during outages
   - Max retries: 3 attempts
   - Fallback: Mark product as temporarily unavailable, continue monitoring others

2. **Rate Limiting Errors** (HTTP 429, 503)
   - Strategy: Implement exponential backoff starting at 2 minutes
   - Reduce monitoring frequency for affected domain
   - Display rate limit status in UI with next retry time

3. **Parsing Errors** (Invalid HTML, missing price data)
   - Strategy: Try alternative parsing strategies from fallback chain
   - Log detailed error with HTML snippet for debugging
   - If all strategies fail, mark as parsing error and notify user

4. **Database Errors** (Connection failure, disk full, corruption)
   - Strategy: Retry database operations with backoff
   - If persistent, switch to file-based logging as fallback
   - Alert admin of database issues

5. **Configuration Errors** (Invalid JSON, missing required fields)
   - Strategy: Validate configuration before applying
   - Restore from backup if validation fails
   - Provide clear error messages with suggested corrections

6. **Resource Exhaustion** (High memory, high CPU, disk full)
   - Strategy: Trigger cleanup processes automatically
   - Reduce monitoring frequency adaptively
   - Alert admin when thresholds exceeded

### Error Recovery Mechanisms

```python
class ErrorHandler:
    def handle_scraping_error(self, product_id: str, error: Exception):
        """Handle errors during price scraping"""
        # Log error with context
        # Update failure count
        # Apply backoff if needed
        # Continue monitoring other products
        pass
    
    def handle_network_outage(self):
        """Handle complete network loss"""
        # Queue pending monitoring tasks
        # Set system status to offline
        # Retry connection periodically
        pass
    
    def handle_database_error(self, error: Exception):
        """Handle database errors"""
        # Attempt reconnection
        # Fall back to file logging
        # Alert admin
        pass
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit testing and property-based testing for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs using randomized testing

Together, these approaches provide comprehensive coverage where unit tests catch concrete bugs and property tests verify general correctness across the input space.

### Property-Based Testing

We will use **Hypothesis** (Python's property-based testing library) to implement the correctness properties defined above. Each property test will:

- Run a minimum of 100 iterations with randomized inputs
- Reference its corresponding design property in a comment tag
- Use the format: `# Feature: real-time-price-tracking, Property N: [property text]`

**Example Property Test**:

```python
from hypothesis import given, strategies as st
import hypothesis

@given(
    interval=st.integers(min_value=-100, max_value=200)
)
@hypothesis.settings(max_examples=100)
def test_interval_validation_property(interval):
    """
    Feature: real-time-price-tracking, Property 1: Interval Validation
    
    For any monitoring interval value, the system should accept values 
    in [1, 60] and reject all others.
    """
    config_manager = ConfigurationManager()
    
    if 1 <= interval <= 60:
        # Should accept valid intervals
        assert config_manager.validate_interval(interval) == True
    else:
        # Should reject invalid intervals
        assert config_manager.validate_interval(interval) == False
```

### Unit Testing Focus Areas

Unit tests should focus on:

1. **Specific Examples**: Test known edge cases (interval=1, interval=60, interval=0, interval=61)
2. **Integration Points**: Test Flask endpoints, database connections, SSE streaming
3. **Error Conditions**: Test specific error scenarios (network timeout, invalid JSON, disk full)
4. **Configuration Profiles**: Test that Conservative/Balanced/Aggressive profiles have correct values

**Example Unit Test**:

```python
def test_conservative_profile_has_30_minute_interval():
    """Test that conservative profile is configured correctly"""
    config_manager = ConfigurationManager()
    profile = config_manager.get_profile('conservative')
    
    assert profile['interval'] == 30
    assert 'description' in profile
```

### Test Configuration

- **Property test iterations**: Minimum 100 per test (due to randomization)
- **Test framework**: pytest with Hypothesis plugin
- **Coverage target**: 80% code coverage minimum
- **CI/CD**: Run all tests on every commit

### Testing Tools

- **pytest**: Test runner and framework
- **Hypothesis**: Property-based testing library
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking for external dependencies
- **freezegun**: Time manipulation for testing scheduling
- **responses**: HTTP request mocking

## Performance Considerations

### Scalability Targets

- Support monitoring up to 100 products simultaneously
- Handle monitoring intervals as low as 1 minute without performance degradation
- Maintain UI responsiveness with 10+ concurrent SSE connections
- Database queries should complete in <100ms for typical operations

### Optimization Strategies

1. **Connection Pooling**: Reuse HTTP connections across requests (requests.Session)
2. **Database Indexing**: Index on (product_id, timestamp) for fast history queries
3. **Caching**: Cache responses for 30 seconds to avoid duplicate API calls
4. **Batch Operations**: Batch database writes for price history
5. **Lazy Loading**: Load price history on-demand rather than preloading
6. **Data Compression**: Compress old price history to reduce storage

### Resource Limits

- **Memory**: Trigger cleanup at 500MB usage
- **CPU**: Reduce monitoring frequency if CPU usage exceeds 80%
- **Disk**: Implement retention policies when disk usage exceeds 90%
- **API Rate Limits**: Respect per-API limits (SerpAPI: 100/month, RapidAPI: 100/month)

## Security Considerations

1. **API Key Protection**: Store API keys in environment variables, never in code
2. **Input Validation**: Validate all user inputs (URLs, intervals, prices)
3. **SQL Injection Prevention**: Use parameterized queries for all database operations
4. **XSS Prevention**: Sanitize all data before displaying in web interface
5. **Rate Limiting**: Implement per-IP rate limiting on API endpoints
6. **Authentication**: Add admin authentication for sensitive operations (future enhancement)

## Deployment Considerations

### Migration Strategy

1. **Database Migration**: Add new tables (price_history, monitoring_config, alerts)
2. **Configuration Migration**: Extend config.json with new fields, maintain backward compatibility
3. **Gradual Rollout**: Start with conservative monitoring intervals, allow users to opt-in to aggressive monitoring
4. **Data Backups**: Backup existing products.json before migration

### Backward Compatibility

- Maintain existing 60-minute monitoring as default
- Existing products automatically get 60-minute interval
- Old API endpoints continue to work
- New features are additive, not breaking

### Monitoring and Observability

- Log all monitoring activities with timestamps
- Track API usage per provider
- Monitor system resource usage (CPU, memory, disk)
- Alert on repeated failures or rate limiting
- Dashboard for admin to view system health

## Future Enhancements

1. **Multi-User Support**: Allow multiple users with separate product lists
2. **Mobile App**: Native mobile app with push notifications
3. **Price Prediction**: ML-based price trend prediction
4. **Comparison Shopping**: Compare prices across multiple retailers
5. **Browser Extension**: Browser extension for one-click product tracking
6. **Webhook Support**: Allow external systems to receive price alerts via webhooks
7. **Advanced Analytics**: Price drop patterns, best time to buy recommendations
