# RabbitMQ Quick Reference

## Files Created

1. **`rabbitmq_queue_flow.json`** - Basic work queue (already exists)
2. **`rabbitmq_advanced_flows.json`** - Three advanced patterns (NEW)
3. **`RABBITMQ_PATTERNS_GUIDE.md`** - Detailed documentation (NEW)

---

## Quick Pattern Comparison

### 1. Basic Work Queue
```javascript
channel.prefetch(1);  // Fair dispatch
```
- ✓ Equal workers
- ✓ Simple round-robin
- ✓ Fair load balancing

### 2. Prefetch Control (NEW!)
```javascript
// Fast worker
channel.prefetch(3);  // Can handle 3 tasks at once

// Slow worker  
channel.prefetch(1);  // One task at a time
```
- ✓ Different worker capacities
- ✓ Optimizes throughput
- ✓ Proportional task distribution

### 3. Priority Queue (NEW!)
```javascript
await channel.assertQueue('queue', { maxPriority: 10 });
channel.sendToQueue('queue', msg, { priority: 10 });
```
- ✓ Process urgent tasks first
- ✓ SLA compliance
- ✓ VIP processing

### 4. Dead Letter Queue (NEW!)
```javascript
await channel.assertQueue('main_queue', {
    deadLetterExchange: 'dlx',
    deadLetterRoutingKey: 'dead'
});
channel.nack(msg, false, false);  // Send to DLQ
```
- ✓ Automatic error handling
- ✓ Failed message inspection
- ✓ Retry mechanisms
- ✓ Production-ready

---

## Prefetch Explained (The Key to Understanding!)

**Prefetch** = How many unacknowledged messages a worker can have at once

### Example with prefetch=1
```
Queue: [T1][T2][T3][T4][T5]

Worker A: T1 ← processing
Worker B: T2 ← processing

Remaining: [T3][T4][T5]

When Worker A finishes T1 and acks → receives T3
When Worker B finishes T2 and acks → receives T4
```

### Example with prefetch=3
```
Queue: [T1][T2][T3][T4][T5][T6][T7][T8]

Worker A (prefetch=3):
  ├─ T1 ← processing
  ├─ T2 ← processing  
  └─ T3 ← processing

Worker B (prefetch=1):
  └─ T4 ← processing

Remaining: [T5][T6][T7][T8]

When Worker A finishes T1 → receives T5
When Worker A finishes T2 → receives T6
When Worker B finishes T4 → receives T7
```

**Result:** Worker A processes 75% of tasks, Worker B processes 25%

---

## Common Prefetch Values

| Task Type | Prefetch | Why |
|-----------|----------|-----|
| CPU-intensive (encoding, ML) | 1-2 | Avoid overload |
| I/O-bound (API calls, DB) | 5-10 | Can wait in parallel |
| Fast tasks (<100ms) | 20-50 | Reduce network overhead |
| Slow tasks (>10s) | 1 | One at a time |

---

## Import Instructions

### Node-RED UI
1. Open http://localhost:1880
2. Menu (☰) → Import
3. Paste JSON content
4. Click Import

### Files to Import
- Basic: `rabbitmq_queue_flow.json`
- Advanced: `rabbitmq_advanced_flows.json` (3 tabs!)

---

## Test Scenarios

### Test Prefetch Control
```bash
# Start both workers
# Click "Send 20 Tasks"
# Watch distribution: Fast worker gets ~15, Slow gets ~5
```

### Test Priority Queue
```bash
# Send 5 low priority tasks
# Send 3 high priority tasks
# High priority processed first!
```

### Test Dead Letter Queue
```bash
# Send "Normal Task" → Success ✓
# Send "Failing Task" → Goes to DLQ automatically
# DLQ Consumer receives and handles it
```

---

## Real-World Examples

### Image Processing Service
```javascript
// GPU-enabled server
channel.prefetch(10);  // Can handle many in parallel

// CPU-only server
channel.prefetch(2);   // Limited capacity
```

### E-commerce Order Processing
```javascript
// Priority queue
{ priority: 10 } // VIP customer orders
{ priority: 5 }  // Standard orders  
{ priority: 1 }  // Batch imports

// Dead letter queue for payment failures
```

### API Request Processing
```javascript
// Fast worker (premium instance)
channel.prefetch(20);

// Slow worker (free tier)
channel.prefetch(1);
```

---

## Key Takeaways

1. **Prefetch controls concurrency** - How many tasks each worker handles at once
2. **Higher prefetch ≠ always better** - Match to task type and worker capacity
3. **Priority queues** have overhead - Use when needed
4. **Dead letter queues** are essential for production
5. **Combine patterns** for robust systems

---

## Next Steps

1. Import the flows into Node-RED
2. Run the examples and observe behavior
3. Read `RABBITMQ_PATTERNS_GUIDE.md` for deep dive
4. Adapt patterns to your use case

---

## Monitoring

Access RabbitMQ Management UI:
```
http://localhost:15672
admin / rabbitmqpass123
```

Watch these metrics:
- Queue depth
- Consumer count  
- Message rates
- Prefetch utilization
