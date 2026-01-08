# IP Velocity and Fraud Pattern Detection Features

## Overview

The IDV system now includes advanced fraud detection capabilities that simulate and detect IP velocity patterns. IP velocity refers to the phenomenon where multiple user accounts share the same IP address, which can indicate:

- Bot farms
- Account takeover attempts
- Coordinated fraud attacks
- VPN/proxy usage for fraud
- Account creation factories

## Features

### 1. Login Session Tracking

Each user now has 5-30 login sessions tracked in the `login_sessions` MongoDB collection with:

- **sessionId**: Unique session identifier
- **userId**: User who owns the session
- **timestamp**: When the session occurred
- **ipAddress**: IP address used (from shared pool or unique)
- **userAgent**: Browser/device user agent string
- **location**: Geographic location (city, country, lat/long)
- **deviceFingerprint**: SHA256 device fingerprint
- **sessionDuration**: How long the session lasted (seconds)
- **actionsPerformed**: Number of actions in the session
- **isHighVelocityIP**: Boolean flag for known high-velocity IPs
- **riskScore**: 0.0-1.0 risk assessment

### 2. IP Velocity Simulation

The data generation creates realistic fraud patterns:

- **50 Shared IPs**: Pool of IPs that multiple users can share
- **10 High Velocity IPs**: Subset flagged as particularly suspicious
- **30% of Users**: Show high IP velocity patterns (3+ users per IP)
- **70% of Users**: Normal behavior (mostly unique IPs)

#### IP Assignment Logic

Normal users:
- 85% chance of unique IP
- 15% chance of shared IP from pool

High velocity users (30% of all users):
- 60% chance of high velocity IP
- 40% chance of regular shared IP

### 3. Fraud Detection API Endpoints

#### `/api/fraud-patterns/ip-velocity`

Returns IPs with multiple users sharing them.

**Response:**
```json
{
  "patterns": [
    {
      "ipAddress": "22.175.57.209",
      "userCount": 7,
      "sessionCount": 16,
      "avgRiskScore": 0.608,
      "isHighVelocityIP": true,
      "users": ["user-id-1", "user-id-2", ...]
    }
  ],
  "totalHighVelocityIPs": 3
}
```

#### `/api/fraud-patterns/users-by-filter?filter={type}`

Get users filtered by fraud patterns.

**Filter Types:**
- `high_ip_velocity` - Users with 3+ sessions on high velocity IPs
- `high_risk` - Users with average risk score >= 0.7

**Response:**
```json
{
  "filter": "high_ip_velocity",
  "userIds": ["user-1", "user-2", ...],
  "count": 7
}
```

#### `/api/fraud-patterns/user/{userId}/sessions`

Get all sessions for a specific user with velocity metrics.

**Response:**
```json
{
  "userId": "abc-123",
  "sessions": [...],
  "totalSessions": 15,
  "uniqueIPs": 8,
  "highVelocitySessions": 5,
  "velocityRatio": 0.333
}
```

### 4. UI Fraud Filters

The graph visualization now includes fraud pattern filtering:

**Filter Dropdown** (top right controls):
- **Show All** - Default view, all nodes with original colors
- **High IP Velocity** - Highlights users with suspicious IP sharing patterns
  - Flagged users: Red nodes (larger size)
  - Other users: Dimmed gray
- **High Risk Score** - Highlights users with risk scores >= 0.7
  - High risk users: Red nodes
  - Other users: Dimmed gray

**IP Velocity Report Button**:
- Opens modal with detailed table of shared IPs
- Shows user count, session count, and average risk score per IP
- High velocity IPs highlighted in red
- Shows top 20 IPs by user count

### 5. Node Highlighting

When filters are applied:
- **Flagged Users**: `#ff4444` (red), size 30
- **Normal Users**: `#cccccc` (light gray), size 25
- **Original colors**: Restored when filter is cleared

### 6. MongoDB Indexes

Optimized indexes for fast fraud pattern queries:

```javascript
// login_sessions indexes
db.login_sessions.createIndex({ "userId": 1 });
db.login_sessions.createIndex({ "ipAddress": 1 });
db.login_sessions.createIndex({ "timestamp": -1 });
db.login_sessions.createIndex({ "isHighVelocityIP": 1 });
db.login_sessions.createIndex({ "ipAddress": 1, "userId": 1 });
```

## Data Generation

### Generating Data with IP Velocity

```bash
# Generate 50 users with login sessions and IP velocity patterns
python3 generate_all_data.py --num-users 50

# Or use the original IDV script
python3 generate_idv_data.py -n 50
```

### What Gets Created

For 50 users:
- ~50 users
- ~100 verifications
- ~250 verification attempts
- **~750-1500 login sessions** (new!)
- Insurance records linked to users

### Expected Patterns

With 50 users, expect approximately:
- 15 users with high IP velocity patterns
- 5-10 IPs with 3+ users sharing
- 2-3 IPs with 5+ users sharing (critical)
- 30-40% of sessions on shared IPs
- 10-15% of sessions flagged as high velocity

## Usage Workflow

### 1. Detect High Velocity IPs

```bash
curl http://localhost:5050/api/fraud-patterns/ip-velocity
```

### 2. Filter Users in UI

1. Open visualization: http://localhost:5050
2. Click "Fraud Filters" dropdown (top right)
3. Select "High IP Velocity"
4. Red nodes are flagged users

### 3. Investigate Specific User

1. Click on a red (flagged) node
2. View details panel shows insurance + IDV data
3. Right-click node → "Add to Investigation"
4. Add notes about the suspicious pattern

### 4. View IP Velocity Report

1. Click "IP Velocity Report" button
2. Review table of shared IPs
3. Note IPs with high user counts (red highlighting)
4. Cross-reference with flagged users

## Technical Implementation

### Data Flow

```
generate_idv_data.py
  → IDVDataGenerator.__init__()
    → Creates shared_ip_pool (50 IPs)
    → Creates high_velocity_ips (10 IPs)
  
  → generate_login_sessions(userId, num_sessions)
    → 30% of users: high velocity patterns
    → Assigns IPs from pools based on pattern
    → Sets isHighVelocityIP flag
  
  → generate_batch()
    → Creates user profiles
    → Creates login sessions for each user
    → Creates verifications and attempts

MongoDB:
  → login_sessions collection
  → Indexed by userId, ipAddress, timestamp

Web UI:
  → /api/fraud-patterns/ip-velocity
    → Aggregates sessions by IP
    → Returns IPs with multiple users
  
  → /api/fraud-patterns/users-by-filter
    → Filters users by pattern type
    → Returns userIds matching criteria
  
  → Frontend JavaScript
    → Fetches filtered user IDs
    → Updates node colors/sizes
    → Highlights fraud patterns
```

### Key Algorithms

**IP Velocity Detection:**
```python
# Aggregate pipeline in MongoDB
{
  '$group': {
    '_id': '$ipAddress',
    'users': {'$addToSet': '$userId'},
    'sessionCount': {'$sum': 1}
  },
  '$match': {
    'userCount': {'$gt': 1}  # Multiple users
  }
}
```

**High Risk Users:**
```python
{
  '$group': {
    '_id': '$userId',
    'avgRiskScore': {'$avg': '$riskScore'}
  },
  '$match': {
    'avgRiskScore': {'$gte': 0.7}
  }
}
```

## Fraud Detection Best Practices

### What to Look For

1. **Critical (5+ users per IP)**
   - Likely bot farm or fraud ring
   - Immediate investigation required
   - Consider blocking IP

2. **High (3-4 users per IP)**
   - Suspicious pattern
   - Could be shared VPN or proxy
   - Review user behaviors

3. **Medium (2 users per IP)**
   - Could be legitimate (family, office)
   - Monitor for escalation
   - Check other indicators

### Combined Indicators

Look for users with:
- High IP velocity + High risk score
- High velocity + Multiple rejected verifications
- High velocity + Short session durations
- High velocity + Suspicious user agents

### Investigation Workflow

1. Filter by "High IP Velocity"
2. Click IP Velocity Report
3. Find IPs with 5+ users
4. Click on users from that IP
5. Check verification status
6. Check insurance claims
7. Right-click → Add to Investigation
8. Document findings in investigation notes

## Performance Notes

- Indexes optimize velocity queries to < 100ms
- Report loads top 20 IPs (configurable)
- UI filter updates ~50-100 nodes in < 200ms
- Aggregation pipelines use MongoDB's native grouping

## Future Enhancements

Potential additions:
- Time-based velocity (users/IP in last 24h)
- Geographic impossibility detection
- Device fingerprint clustering
- User agent anomaly detection
- Behavior pattern matching
- Machine learning risk scoring
- Real-time alerts for critical patterns

## Troubleshooting

### No Login Sessions Generated

```bash
# Check if login_sessions collection exists
docker exec lynx-mongodb mongosh -u admin -p mongopass123 \
  --authenticationDatabase admin idv_data \
  --eval "db.login_sessions.countDocuments()"

# Should return > 0
```

### Filters Not Working

1. Check web UI logs: `docker logs lynx-web-ui`
2. Verify API endpoint: `curl http://localhost:5050/api/fraud-patterns/ip-velocity`
3. Check browser console for JavaScript errors
4. Restart web UI: `docker-compose restart web-ui`

### No High Velocity Patterns

- Need at least 30-50 users for realistic patterns
- Regenerate with more users: `python3 generate_all_data.py --num-users 100`
- Check high velocity IP count in data

## Credits

IP velocity simulation based on real-world fraud detection patterns observed in:
- Identity verification systems
- Financial transaction monitoring
- Account security systems
- Bot detection frameworks
