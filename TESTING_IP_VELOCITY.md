# Testing IP Velocity Features

Quick guide to test the new fraud detection features.

## Setup

1. **Restart MongoDB** to apply new indexes:
```bash
docker-compose restart mongodb
```

2. **Regenerate data** with IP velocity simulation:
```bash
python3 generate_all_data.py --num-users 50
```

3. **Restart Web UI** to load new API endpoints:
```bash
docker-compose restart web-ui
```

## Verify Data Generation

### Check Login Sessions Were Created

```bash
# Count login sessions
docker exec lynx-mongodb mongosh -u admin -p mongopass123 \
  --authenticationDatabase admin idv_data \
  --eval "db.login_sessions.countDocuments({})"

# Expected: 250-1500 sessions (5-30 per user)
```

### View Sample Session

```bash
docker exec lynx-mongodb mongosh -u admin -p mongopass123 \
  --authenticationDatabase admin idv_data \
  --eval "db.login_sessions.findOne()" | head -25
```

Should see:
- `sessionId`
- `userId`
- `ipAddress`
- `userAgent`
- `isHighVelocityIP` (boolean)
- `riskScore` (0.0-1.0)

## Test API Endpoints

### 1. IP Velocity Detection

```bash
curl -s http://localhost:5050/api/fraud-patterns/ip-velocity | python3 -m json.tool | head -50
```

**Expected Output:**
- Array of IPs with multiple users
- Each IP shows: `ipAddress`, `userCount`, `sessionCount`, `avgRiskScore`, `isHighVelocityIP`
- `totalHighVelocityIPs` count

**Look For:**
- IPs with `userCount >= 3` (suspicious)
- IPs with `userCount >= 5` (critical)
- IPs with `isHighVelocityIP: true`

### 2. Filter High Velocity Users

```bash
curl -s "http://localhost:5050/api/fraud-patterns/users-by-filter?filter=high_ip_velocity" | python3 -m json.tool
```

**Expected Output:**
```json
{
  "filter": "high_ip_velocity",
  "userIds": ["uuid1", "uuid2", ...],
  "count": 7
}
```

**Expected Count:** ~15-30% of total users (depends on data size)

### 3. User Session Details

```bash
# Get a user ID from the filter above
USER_ID="<paste-a-user-id-here>"

curl -s "http://localhost:5050/api/fraud-patterns/user/$USER_ID/sessions" | python3 -m json.tool
```

**Expected Output:**
- Array of sessions for that user
- `totalSessions` count
- `uniqueIPs` count
- `highVelocitySessions` count
- `velocityRatio` (0.0-1.0)

## Test Web UI

### 1. Open Visualization

```bash
open http://localhost:5050
# Or: http://YOUR_SERVER_IP:5050
```

### 2. Test Fraud Filter

1. Look for **"Fraud Filters"** dropdown in top-right controls
2. Select **"High IP Velocity"**
3. **Expected:**
   - Some user nodes turn RED (larger size)
   - Other user nodes turn GRAY (dimmed)
   - Red nodes are flagged users

4. Select **"Show All"** to reset
5. **Expected:**
   - All nodes return to original colors
   - All nodes return to original sizes

### 3. Test IP Velocity Report

1. Click **"IP Velocity Report"** button
2. **Expected:**
   - Modal opens with table
   - Shows top 20 IPs by user count
   - Columns: IP Address, Users, Sessions, Avg Risk
   - High velocity IPs highlighted in red background

3. Check for:
   - IPs with 3+ users (suspicious)
   - IPs with 5+ users (critical)
   - Average risk scores >= 0.5

### 4. Test Node Interaction

1. Apply "High IP Velocity" filter
2. Click on a RED (flagged) user node
3. **Expected in detail panel:**
   - User information
   - Insurance data (if available)
   - Verification status

4. Right-click on the red node
5. Select "Add to Investigation"
6. **Expected:**
   - Modal opens
   - Shows selected node + connected nodes
   - Can add investigation name and notes

## MongoDB Queries for Validation

### Find High Velocity IPs

```javascript
use idv_data

db.login_sessions.aggregate([
  {
    $group: {
      _id: "$ipAddress",
      users: { $addToSet: "$userId" },
      count: { $sum: 1 }
    }
  },
  {
    $project: {
      ipAddress: "$_id",
      userCount: { $size: "$users" },
      sessionCount: "$count"
    }
  },
  {
    $match: {
      userCount: { $gt: 2 }  // 3+ users
    }
  },
  {
    $sort: { userCount: -1 }
  },
  {
    $limit: 10
  }
])
```

### Find Users on High Velocity IPs

```javascript
use idv_data

db.login_sessions.aggregate([
  {
    $match: {
      isHighVelocityIP: true
    }
  },
  {
    $group: {
      _id: "$userId",
      sessionCount: { $sum: 1 },
      avgRiskScore: { $avg: "$riskScore" }
    }
  },
  {
    $match: {
      sessionCount: { $gte: 3 }
    }
  },
  {
    $sort: { sessionCount: -1 }
  }
])
```

### Sessions Per User Distribution

```javascript
use idv_data

db.login_sessions.aggregate([
  {
    $group: {
      _id: "$userId",
      sessionCount: { $sum: 1 }
    }
  },
  {
    $group: {
      _id: null,
      avgSessions: { $avg: "$sessionCount" },
      minSessions: { $min: "$sessionCount" },
      maxSessions: { $max: "$sessionCount" }
    }
  }
])
```

Expected: avg ~15, min ~5, max ~30

## Expected Test Results

### For 50 Users:

- **Login Sessions:** ~750-1500 (15 avg per user)
- **Unique IPs:** ~50-100 (mix of shared and unique)
- **High Velocity IPs:** ~5-10 IPs with 3+ users
- **Critical IPs:** ~2-3 IPs with 5+ users
- **Flagged Users:** ~15-20 (30% of users)
- **High Risk Users:** ~10-15 (average risk >= 0.7)

### For 100 Users:

- **Login Sessions:** ~1500-3000
- **Unique IPs:** ~80-150
- **High Velocity IPs:** ~10-15 IPs with 3+ users
- **Critical IPs:** ~4-6 IPs with 5+ users
- **Flagged Users:** ~30-40
- **High Risk Users:** ~20-30

## Troubleshooting

### No Login Sessions Created

**Check generation output:**
```bash
python3 generate_all_data.py --num-users 20
```

Should see line:
```
Inserted 341 login sessions into MongoDB
```

**If not present:**
- Check `generate_idv_data.py` has `generate_login_sessions()` method
- Verify `generate_batch()` includes login_sessions in return dict
- Check DataIngestor handles `data.get('login_sessions')`

### Fraud Filter Not Working

**Check browser console:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Apply filter
4. Look for errors

**Common issues:**
- API endpoint returns 500 error → Check Flask logs
- JavaScript error → Check index.html syntax
- No users highlighted → Check filter returned user IDs

**Check Flask logs:**
```bash
docker logs lynx-web-ui --tail 50
```

### IP Velocity Report Empty

**Verify data:**
```bash
# Check for IPs with multiple users
docker exec lynx-mongodb mongosh -u admin -p mongopass123 \
  --authenticationDatabase admin idv_data \
  --eval "db.login_sessions.aggregate([
    { \$group: { _id: '\$ipAddress', users: { \$addToSet: '\$userId' } } },
    { \$project: { userCount: { \$size: '\$users' } } },
    { \$match: { userCount: { \$gt: 1 } } },
    { \$count: 'sharedIPs' }
  ])"
```

Should return count > 0.

**If count is 0:**
- Regenerate with more users: `--num-users 100`
- Check IP pool is being used in `generate_login_sessions()`

### Filter Highlights Wrong Nodes

**Check filter logic:**
1. API returns user IDs: `/api/fraud-patterns/users-by-filter?filter=high_ip_velocity`
2. JavaScript filters nodes where `node.type === 'user'`
3. Matches `node.id` against returned `userIds` array

**Debug in console:**
```javascript
// Get filtered users
fetch('/api/fraud-patterns/users-by-filter?filter=high_ip_velocity')
  .then(r => r.json())
  .then(d => console.log('Filtered users:', d.userIds))

// Check node types
nodes.forEach(node => {
  if (node.type === 'user') {
    console.log('User node:', node.id)
  }
})
```

## Success Criteria

✅ **Data Generation:**
- Login sessions created for all users
- Some sessions marked `isHighVelocityIP: true`
- IP addresses show sharing patterns

✅ **API Endpoints:**
- `/api/fraud-patterns/ip-velocity` returns IPs with multiple users
- `/api/fraud-patterns/users-by-filter` returns filtered user IDs
- `/api/fraud-patterns/user/{id}/sessions` returns user sessions

✅ **UI Functionality:**
- Fraud filter dropdown present and functional
- Selecting filter highlights nodes in red
- "Show All" resets to original colors
- IP Velocity Report opens with data table

✅ **Visual Indicators:**
- Red nodes for flagged users (size 30)
- Gray nodes for normal users when filtered
- High velocity IPs highlighted in report table

## Next Steps

After successful testing:

1. **Deploy to Ubuntu** (if needed):
   - Follow UBUNTU_SETUP.md
   - Regenerate data on production server
   - Test remote access to UI

2. **Customize Thresholds:**
   - Edit high velocity threshold in app.py (default: 3+ sessions)
   - Adjust risk score threshold (default: 0.7)
   - Modify IP pool size in generate_idv_data.py

3. **Add More Patterns:**
   - Device fingerprint clustering
   - Geographic impossibility
   - Time-based velocity
   - User agent anomalies

4. **Export Data:**
   - Investigation reports
   - Fraud pattern summaries
   - Risk score distributions
