# RabbitMQ Work Queue Example in Node-RED

This flow demonstrates the **Work Queue** (Task Queue) pattern using RabbitMQ and Node-RED.

## What's Included

The flow implements a distributed task processing system with:

1. **Task Producer** - Creates tasks and sends them to a queue
2. **Two Workers** - Consume tasks from the queue and process them
3. **Round-robin distribution** - RabbitMQ distributes tasks evenly between workers

## How to Import the Flow

### Option 1: Manual Import via UI
1. Open Node-RED: http://localhost:1880
2. Click the menu (☰) → Import
3. Copy the contents of `rabbitmq_queue_flow.json`
4. Paste and click Import

### Option 2: Using the API
```bash
curl -X POST http://localhost:1880/flows \
  -H "Content-Type: application/json" \
  -H "Node-RED-Deployment-Type: nodes" \
  -d @rabbitmq_queue_flow.json
```

## Configuration

The flow is pre-configured to connect to your local RabbitMQ instance:

- **Host:** `rabbitmq` (Docker container name)
- **Port:** `5672`
- **Username:** `admin`
- **Password:** `rabbitmqpass123`
- **Queue Name:** `work_queue`

### Setting Credentials

After importing, you'll need to configure the AMQP broker credentials:

1. Double-click any AMQP node (e.g., "Send to Queue" or "Worker 1")
2. Click the pencil icon next to "RabbitMQ Local"
3. Go to the "Security" tab
4. Enter credentials:
   - Username: `admin`
   - Password: `rabbitmqpass123`
5. Click Update, then Done
6. Deploy the flow

## How to Use

### 1. Generate a Single Task
- Click the button on the **"Generate Task"** inject node
- This creates one task with random complexity (1-5 seconds processing time)
- The task is sent to the `work_queue`

### 2. Generate Multiple Tasks
- Click the button on the **"Generate 10 Tasks"** inject node
- This creates 10 tasks and sends them to the queue
- Watch how the two workers distribute the load

### 3. Watch the Processing
- Open the Debug sidebar (bug icon in the top right)
- You'll see:
  - Tasks being created
  - Workers picking up tasks (round-robin)
  - Tasks being completed with timing information

## Flow Components

### Producer Section
- **Generate Task** - Inject node that triggers single task creation
- **Generate 10 Tasks** - Inject node that triggers batch creation
- **Create Task** - Function that generates a task with random properties
- **Create Batch Tasks** - Function that generates multiple tasks
- **Send to Queue** - AMQP Out node that publishes to RabbitMQ

### Consumer Section (Workers)
- **Worker 1** - AMQP In node consuming from `work_queue`
- **Worker 2** - AMQP In node consuming from the same queue
- **Process Task** - Functions that simulate work (sleep based on complexity)
- **Debug nodes** - Show received and completed tasks

## Key Features

### Fair Distribution
- Both workers have `prefetch: 1` set
- This means each worker gets one task at a time
- Ensures fair distribution based on processing speed

### Durable Queue
- Queue is marked as `durable: true`
- Messages persist even if RabbitMQ restarts
- Messages aren't lost if Node-RED crashes

### Acknowledgments
- Workers use manual acknowledgment (`noAck: false`)
- RabbitMQ only removes a message when the worker finishes
- If a worker crashes, the task is redelivered

## Testing the Flow

### Test 1: Basic Functionality
1. Click "Generate Task" once
2. Watch the debug panel - one worker should pick it up
3. Wait for completion message

### Test 2: Load Balancing
1. Click "Generate 10 Tasks"
2. Watch the debug panel
3. Observe tasks being distributed between Worker 1 and Worker 2
4. Notice they process tasks in parallel

### Test 3: Different Complexities
Tasks have random complexity (1-5):
- Complexity 1 = 1 second processing
- Complexity 5 = 5 seconds processing

Watch how the faster-finishing worker picks up more tasks!

## Monitoring in RabbitMQ

1. Open RabbitMQ Management: http://localhost:15672
2. Login: `admin` / `rabbitmqpass123`
3. Go to the **Queues** tab
4. Click on `work_queue` to see:
   - Message rates
   - Ready messages
   - Unacknowledged messages
   - Consumer details

## Common Patterns to Try

### Pattern 1: Priority Tasks
Modify the `Create Task` function to add priority:
```javascript
msg.payload.priority = Math.floor(Math.random() * 10);
```

### Pattern 2: Error Handling
Add error simulation to the worker function:
```javascript
if (Math.random() < 0.1) { // 10% failure rate
    node.error("Task failed!", msg);
    return null; // Don't acknowledge - message will be redelivered
}
```

### Pattern 3: Dead Letter Queue
Configure a dead letter exchange for failed tasks after retry limit.

## Troubleshooting

### Workers Not Connecting
- Check RabbitMQ is running: `docker ps | grep rabbitmq`
- Verify credentials in AMQP broker configuration
- Check Node-RED logs: `docker logs lynx-nodered`

### No Messages Being Processed
- Ensure you've deployed the flow (Deploy button)
- Check that both AMQP In nodes show "connected" status
- Verify the queue name matches in both producer and consumers

### Messages Stuck in Queue
- Check RabbitMQ management console
- Ensure workers are connected and active
- Look for errors in the debug panel

## Next Steps

Try these enhancements:

1. **Add a third worker** - Copy Worker 2 and see how distribution changes
2. **Create different queue types** - Try topic exchanges with routing keys
3. **Add monitoring** - Send completion stats to a database
4. **Implement retry logic** - Handle failed tasks with exponential backoff
5. **Add result aggregation** - Collect all completed tasks and aggregate results

## Architecture

```
Producer → [work_queue] → Worker 1
                       ↘
                         Worker 2

- Producer creates tasks and sends to queue
- RabbitMQ holds tasks in work_queue
- Workers compete for tasks (round-robin)
- Each worker processes one task at a time
- Completed tasks are acknowledged and removed
```

## References

- [RabbitMQ Work Queues Tutorial](https://www.rabbitmq.com/tutorials/tutorial-two-python.html)
- [Node-RED AMQP Documentation](https://flows.nodered.org/node/node-red-contrib-amqp)
- [Message Queue Patterns](https://www.enterpriseintegrationpatterns.com/patterns/messaging/)
