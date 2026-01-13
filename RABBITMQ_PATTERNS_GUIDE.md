# RabbitMQ Queue Patterns Guide

This guide explains different RabbitMQ queue patterns with working examples in Node-RED.

## Overview of Examples

We have created multiple flow examples demonstrating different RabbitMQ patterns:

1. **Basic Work Queue** (`rabbitmq_queue_flow.json`) - Original example
2. **Advanced Patterns** (`rabbitmq_advanced_flows.json`) - Three new patterns

---

## 1. Basic Work Queue Pattern

**File:** `rabbitmq_queue_flow.json`

### How It Works

- **Queue Name:** `work_queue`
- **Pattern:** Round-robin task distribution
- **Prefetch:** Both workers use `prefetch=1`
- **Distribution:** Fair - each worker gets one task at a time

### Key Concepts

```javascript
channel.prefetch(1); // Fair dispatch - only 1 unacked message per worker
```

When you have multiple workers consuming from the same queue:
- RabbitMQ distributes messages in round-robin fashion
- With `prefetch=1`, each worker must acknowledge before receiving next task
- This prevents fast workers from getting overloaded while slow workers idle

### When to Use

- Equal capacity workers
- Simple task distribution
- Fair load balancing

---

## 2. Prefetch Control Pattern

**File:** `rabbitmq_advanced_flows.json` (Tab: "Prefetch Control Example")

### How It Works

- **Queue Name:** `prefetch_queue`
- **Fast Worker:** `prefetch=3` - can handle 3 tasks simultaneously
- **Slow Worker:** `prefetch=1` - handles 1 task at a time
- **Result:** Fast worker receives more tasks proportional to capacity

### The Prefetch Concept

**Prefetch** (also called QoS - Quality of Service) controls how many unacknowledged messages a worker can have:

```javascript
// Fast worker - can buffer up to 3 tasks
channel.prefetch(3);

// Slow worker - processes one at a time
channel.prefetch(1);
```

### How Distribution Works

When you send 20 tasks to the queue:

1. **Initial Distribution:**
   - Fast worker receives 3 tasks immediately
   - Slow worker receives 1 task
   - Remaining 16 tasks stay in queue

2. **As Tasks Complete:**
   - When fast worker completes a task (acknowledges), it receives another
   - When slow worker completes, it receives another
   - Fast worker processes ~75% of tasks, slow worker ~25%

### Visual Example

```
Queue: [T1][T2][T3][T4][T5][T6][T7][T8][T9][T10]...

Fast Worker (prefetch=3):
  ├─ T1 (processing)
  ├─ T2 (processing)
  └─ T3 (processing)

Slow Worker (prefetch=1):
  └─ T4 (processing)

Remaining in queue: [T5][T6][T7][T8][T9][T10]...
```

### When to Use

- **Heterogeneous workers** with different processing capacities
- **Scaled deployments** where some instances have more resources
- **Optimizing throughput** by matching worker capacity to task load
- **GPU vs CPU workers** - GPU worker might prefetch more

### Real-World Example

```javascript
// High-performance server (8 cores, 32GB RAM)
channel.prefetch(10);

// Standard server (4 cores, 8GB RAM)
channel.prefetch(3);

// Low-power instance (2 cores, 4GB RAM)
channel.prefetch(1);
```

---

## 3. Priority Queue Pattern

**File:** `rabbitmq_advanced_flows.json` (Tab: "Priority Queue Example")

### How It Works

- **Queue Name:** `priority_queue`
- **Priority Range:** 1-10 (10 = highest)
- **Behavior:** Higher priority messages delivered first
- **Same Priority:** FIFO order

### Configuration

```javascript
// Create queue with max priority
await channel.assertQueue('priority_queue', { 
    durable: true,
    maxPriority: 10  // Support priorities 0-10
});

// Send message with priority
channel.sendToQueue(queueName, Buffer.from(message), { 
    persistent: true,
    priority: 10  // High priority
});
```

### How Priority Works

1. **Queue Ordering:**
   ```
   Priority 10: [High Task 1][High Task 2]
   Priority 5:  [Med Task 1][Med Task 2]
   Priority 1:  [Low Task 1][Low Task 2][Low Task 3]
   ```

2. **Processing Order:**
   - All priority 10 tasks processed first
   - Then priority 5 tasks
   - Finally priority 1 tasks

3. **Dynamic Priority:**
   - New high-priority messages jump to front
   - Even if low-priority messages already in queue

### When to Use

- **Critical vs routine tasks**
- **SLA requirements** - premium customers get priority
- **Time-sensitive operations** - real-time alerts vs batch reports
- **Resource allocation** - VIP processing lanes

### Real-World Examples

```javascript
// Critical system alert
{ priority: 10, type: 'security_breach' }

// User-facing task
{ priority: 7, type: 'api_request' }

// Background job
{ priority: 3, type: 'analytics' }

// Cleanup task
{ priority: 1, type: 'log_rotation' }
```

### Important Notes

⚠️ **Performance Impact:**
- Priority queues have slight overhead
- Use only when needed (not all queues need priority)
- Consider separate queues for very different task types

---

## 4. Dead Letter Queue (DLQ) Pattern

**File:** `rabbitmq_advanced_flows.json` (Tab: "Dead Letter Queue Example")

### How It Works

- **Main Queue:** `main_queue` - normal processing
- **Dead Letter Exchange:** `dlx` - routing for failed messages
- **Dead Letter Queue:** `dead_letter_queue` - holds failed messages
- **Behavior:** Failed tasks automatically routed to DLQ

### Architecture

```
[Producer] → [main_queue] → [Worker]
                    ↓ (reject/expire)
              [dlx exchange]
                    ↓
           [dead_letter_queue] → [DLQ Consumer]
```

### Configuration

```javascript
// Setup DLX (Dead Letter Exchange)
await channel.assertExchange('dlx', 'direct', { durable: true });

// Setup DLQ
await channel.assertQueue('dead_letter_queue', { durable: true });
await channel.bindQueue('dead_letter_queue', 'dlx', 'dead');

// Configure main queue to use DLX
await channel.assertQueue('main_queue', { 
    durable: true,
    deadLetterExchange: 'dlx',
    deadLetterRoutingKey: 'dead',
    messageTtl: 60000  // Optional: expire after 60s
});
```

### When Messages Go to DLQ

1. **Explicit Rejection:**
   ```javascript
   // Reject without requeue → goes to DLQ
   channel.nack(msg, false, false);
   ```

2. **Message Expiration:**
   ```javascript
   // Message expires after TTL → goes to DLQ
   messageTtl: 60000  // 60 seconds
   ```

3. **Queue Length Limit:**
   ```javascript
   maxLength: 1000  // When queue full, oldest → DLQ
   ```

4. **Consumer Processing Failure:**
   ```javascript
   try {
       processTask(task);
       channel.ack(msg);
   } catch (error) {
       // Processing failed, send to DLQ
       channel.nack(msg, false, false);
   }
   ```

### DLQ Consumer Responsibilities

```javascript
// Monitor and handle dead letters
channel.consume('dead_letter_queue', (msg) => {
    const task = JSON.parse(msg.content.toString());
    
    // Actions you can take:
    // 1. Log for debugging
    console.error('Task failed:', task);
    
    // 2. Send alert
    sendAlert(`Task ${task.taskId} failed`);
    
    // 3. Store for manual review
    database.save('failed_tasks', task);
    
    // 4. Retry with backoff
    if (task.retryCount < 3) {
        setTimeout(() => retryTask(task), 60000);
    }
    
    // 5. Move to archive
    archiveQueue.send(task);
    
    channel.ack(msg);
});
```

### When to Use

- **Error handling** - capture and handle failures
- **Debugging** - inspect failed messages
- **Monitoring** - track failure rates
- **Retry mechanisms** - intelligent retry strategies
- **Compliance** - audit trail of failed operations

### Real-World Example

```javascript
// E-commerce order processing
main_queue: order_processing
  ↓ (payment fails, inventory error, etc.)
dead_letter_queue: failed_orders
  ↓
DLQ Consumer:
  - Notify customer service
  - Send email to customer
  - Create support ticket
  - Log to error tracking system
  - Attempt automated resolution
```

### Best Practices

1. **Always monitor DLQ** - set up alerts
2. **Set TTL** - prevent infinite message retention
3. **Add metadata** - include retry count, error messages
4. **Separate DLQs** - different queues for different failure types
5. **Automate recovery** - intelligent retry with exponential backoff

---

## Comparison Table

| Pattern | Use Case | Prefetch | Priority | Error Handling |
|---------|----------|----------|----------|----------------|
| **Basic Work Queue** | Equal workers, fair distribution | 1 | No | Manual |
| **Prefetch Control** | Different worker capacities | Variable | No | Manual |
| **Priority Queue** | Urgent vs routine tasks | Any | Yes (1-10) | Manual |
| **Dead Letter Queue** | Production error handling | Any | Optional | Automatic |

---

## Combining Patterns

You can combine these patterns:

### Example: Priority + DLQ

```javascript
await channel.assertQueue('priority_work_queue', { 
    durable: true,
    maxPriority: 10,              // Priority support
    deadLetterExchange: 'dlx',    // DLQ support
    deadLetterRoutingKey: 'dead'
});
```

### Example: Prefetch + Priority + DLQ

```javascript
// Fast worker with priority and error handling
await channel.assertQueue('production_queue', { 
    durable: true,
    maxPriority: 10,
    deadLetterExchange: 'dlx',
    deadLetterRoutingKey: 'dead'
});

channel.prefetch(5);  // Fast worker capacity
```

---

## Testing the Examples

### Import the Flows

1. **Basic Pattern:**
   ```bash
   # Import rabbitmq_queue_flow.json via Node-RED UI
   ```

2. **Advanced Patterns:**
   ```bash
   # Import rabbitmq_advanced_flows.json via Node-RED UI
   ```

### Test Prefetch Control

1. Click "Start Fast Worker" and "Start Slow Worker"
2. Click "Send 20 Tasks"
3. Observe: Fast worker processes ~15 tasks, slow worker ~5 tasks

### Test Priority Queue

1. Click "Start Priority Worker"
2. Send several "Low Priority Tasks"
3. Then send "High Priority Tasks"
4. Observe: High priority tasks processed first, even though low priority were sent earlier

### Test Dead Letter Queue

1. Click "Start Main Worker" and "Start DLQ Consumer"
2. Send "Normal Task" - should complete successfully
3. Send "Failing Task" - should be rejected to DLQ
4. Watch debug output to see DLQ consumer receive failed task

---

## Additional Patterns (Not Yet Implemented)

### Other patterns you might want to explore:

1. **Pub/Sub (Fanout Exchange)**
   - Broadcast messages to all subscribers
   - Use case: Notifications, event broadcasting

2. **Topic Exchange**
   - Route based on pattern matching
   - Use case: Logging levels, regional routing

3. **Request/Reply (RPC)**
   - Synchronous request-response pattern
   - Use case: Microservice communication

4. **Delayed Messages**
   - Schedule messages for future delivery
   - Use case: Scheduled tasks, reminders

5. **Message TTL with Retry**
   - Automatic retry with exponential backoff
   - Use case: Transient failure handling

---

## Performance Tuning

### Prefetch Guidelines

```javascript
// CPU-bound tasks
prefetch = number_of_cpu_cores

// I/O-bound tasks (network, disk)
prefetch = number_of_cpu_cores * 2

// Very fast tasks (<10ms)
prefetch = 50-100

// Slow tasks (>1s)
prefetch = 1-3
```

### Queue Configuration

```javascript
// Production-ready queue
await channel.assertQueue(queueName, {
    durable: true,           // Survive broker restart
    maxPriority: 10,         // If priority needed
    messageTtl: 3600000,     // 1 hour expiry
    maxLength: 10000,        // Max queue size
    deadLetterExchange: 'dlx'
});
```

---

## Monitoring

Key metrics to monitor:

1. **Queue Depth** - messages waiting
2. **Consumer Count** - active workers
3. **Message Rate** - throughput
4. **Ack Rate** - successful processing
5. **DLQ Size** - failure rate
6. **Prefetch Utilization** - worker efficiency

Access RabbitMQ Management UI:
```
http://localhost:15672
Username: admin
Password: rabbitmqpass123
```

---

## Summary

- ✅ **Basic Work Queue**: Fair distribution, simple setup
- ✅ **Prefetch Control**: Optimize for different worker capacities  
- ✅ **Priority Queue**: Process urgent tasks first
- ✅ **Dead Letter Queue**: Robust error handling

Each pattern solves different problems. Choose based on your requirements!
