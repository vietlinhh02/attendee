# Participant Events

Attendee tracks all participants in a meeting and when they take certain actions. This information can be used for tracking meeting attendance, monitoring participant status changes, or triggering actions when a certain number of participants have joined.

The bot itself is not considered a participant in the meeting and will not appear in the participant events.

## Participant Event Types

There are three types of participant events:

- **Join**: A participant has joined the meeting. This event is triggered when a participant first enters the meeting room.
- **Leave**: A participant has left the meeting. This event is triggered when a participant exits the meeting.
- **Update**: A participant's attributes have changed during the meeting. This event is triggered when participant properties are modified, such as:
  - Host status changes (when someone becomes a host or loses host privileges)
  
Note: Update events are currently tracked internally to maintain accurate participant state but are not yet persisted to the database or delivered via webhooks. Only Join and Leave events are available through the API and webhooks.

## Fetching Participant Events

You can retrieve a list of participant events for a specific bot by making a GET request to the `/bots/{bot_id}/participant_events` endpoint.

This endpoint returns paginated results of Join and Leave events. Each event includes:
- **Participant information**: Name, UUID, user UUID, and host status
- **Event type**: Either "join" or "leave"
- **Timestamp**: When the event occurred (in milliseconds)
- **Event data**: Additional context about the event (typically empty for join/leave)

For more details on the API, see the [API reference](https://docs.attendee.dev/api-reference#tag/bots/get/api/v1/bots/{object_id}/participant_events).

## Webhooks for Participant Events

You can also receive real-time notifications for participant events by setting up a webhook. To do this, create a webhook in the dashboard and ensure the `participant_events.join_leave` trigger is enabled.

### When are webhooks sent?

Webhooks are sent in real-time when:
- A participant **joins** the meeting (becomes active)
- A participant **leaves** the meeting (becomes inactive)

Webhooks are **not** currently sent for Update events (such as host status changes).

### Webhook Payload Structure

When a participant joins or leaves, Attendee will send a webhook payload to your specified URL with the following structure:

```json
{
  "idempotency_key": "<UUID that uniquely identifies this webhook delivery>",
  "bot_id": "<ID of the bot associated with the webhook>",
  "bot_metadata": "<Any metadata associated with the bot>",
  "trigger": "participant_events.join_leave",
  "data": {
    "id": "<The ID of the participant event>",
    "participant_name": "<The name of the participant>",
    "participant_uuid": "<The UUID of the participant>",
    "participant_user_uuid": "<The UUID of the participant's user account within the meeting platform>",
    "participant_is_host": "<Boolean indicating if the participant is the host>",
    "event_type": "<Either 'join' or 'leave'>",
    "event_data": "<Additional event data (typically empty for join/leave events)>",
    "timestamp_ms": "<Timestamp in milliseconds when the event occurred>"
  }
}
```

### Example Webhook Payloads

**Join Event:**
```json
{
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
  "bot_id": "bot_abc123xyz",
  "bot_metadata": {"meeting_type": "sales_call"},
  "trigger": "participant_events.join_leave",
  "data": {
    "id": "pe_def456uvw",
    "participant_name": "John Doe",
    "participant_uuid": "user_789",
    "participant_user_uuid": "platform_user_456",
    "participant_is_host": true,
    "event_type": "join",
    "event_data": {},
    "timestamp_ms": 1704556800000
  }
}
```

**Leave Event:**
```json
{
  "idempotency_key": "650e8400-e29b-41d4-a716-446655440001",
  "bot_id": "bot_abc123xyz",
  "bot_metadata": {"meeting_type": "sales_call"},
  "trigger": "participant_events.join_leave",
  "data": {
    "id": "pe_ghi789rst",
    "participant_name": "John Doe",
    "participant_uuid": "user_789",
    "participant_user_uuid": "platform_user_456",
    "participant_is_host": true,
    "event_type": "leave",
    "event_data": {},
    "timestamp_ms": 1704560400000
  }
}
```

### Use Cases

Participant event webhooks are useful for:
- **Attendance tracking**: Log when specific participants join and leave meetings
- **Automated actions**: Trigger workflows when key stakeholders join (e.g., start recording when the host joins)
- **Meeting analytics**: Calculate meeting duration per participant
- **Notifications**: Alert team members when important participants join or leave
- **Capacity monitoring**: Track the number of active participants in real-time

For more details on the webhook payload, see the [webhooks documentation](https://docs.attendee.dev/guides/webhooks#webhook-payload__payload-for-participanteventsjoinleave-trigger).

## Participant Identification

Each participant is uniquely identified across events using the following identifiers:

### participant_uuid
A unique identifier for the participant within the context of the specific meeting. This UUID remains consistent across all events for the same participant during a single meeting session. Use this to track a participant's actions throughout a meeting.

**Important**: If a participant leaves and rejoins the same meeting, they may receive a new `participant_uuid` depending on the meeting platform.

### participant_user_uuid  
The user ID provided by the meeting platform (e.g., Zoom user ID, Google Meet user ID). This identifier represents the participant's account on the meeting platform and can be used to correlate participants across different meetings.

**Note**: This field may be `null` for:
- Guest participants who join without signing in
- Participants using phone dial-in
- Platforms that don't provide user identifiers

### participant_name
The display name of the participant as shown in the meeting. This name can change during a meeting if the participant updates their display name, and may not be unique (multiple participants can have the same name).

## Platform-Specific Behavior

Participant event behavior can vary depending on the meeting platform:

### Zoom
- Join events are triggered when a participant enters the main meeting room
- Participants in the waiting room are not yet considered "joined"
- When a participant is admitted from the waiting room, a join event is fired
- Breakout room movements are tracked as separate events

### Google Meet
- Join/leave detection relies on the meeting's participant list updates
- There may be a slight delay (typically under a few seconds) in detecting leave events
- The bot tracks participants through the `deviceId` provided by Google Meet

### Microsoft Teams
- Participant events are based on roster updates from the Teams meeting
- Phone dial-in participants are tracked when Teams provides their information
- Join/leave timing aligns with Teams' native participant notifications

### Web-based Platforms (Generic)
- Event detection depends on the platform's participant API
- Some platforms may have delays in reporting join/leave events
- Accuracy depends on how reliably the platform reports participant status changes

## Best Practices

### 1. Use Idempotency Keys
Always track the `idempotency_key` from webhooks to avoid processing duplicate events. Webhooks may be retried if delivery fails, so the same event could be delivered multiple times.

```python
# Example: Check if event was already processed
if Event.objects.filter(idempotency_key=webhook_data['idempotency_key']).exists():
    return  # Already processed
    
# Process the event...
Event.objects.create(idempotency_key=webhook_data['idempotency_key'], ...)
```

### 2. Handle Missing participant_user_uuid
Not all participants will have a `participant_user_uuid`. Design your system to handle `null` values:

```python
participant_user_uuid = event_data.get('participant_user_uuid')
if participant_user_uuid:
    # Link to known user account
    user = get_user_by_platform_id(participant_user_uuid)
else:
    # Handle guest or anonymous participant
    user = create_guest_user(event_data['participant_name'])
```

### 3. Track Participant Duration
Calculate how long participants stay in meetings by pairing join and leave events:

```python
join_event = get_participant_join_event(participant_uuid, meeting_id)
leave_event = get_participant_leave_event(participant_uuid, meeting_id)

duration_ms = leave_event['timestamp_ms'] - join_event['timestamp_ms']
duration_minutes = duration_ms / (1000 * 60)
```

### 4. Filter Events by Timestamp
When polling the API, use the `after` parameter to retrieve only new events:

```http
GET /api/v1/bots/{bot_id}/participant_events?after=2024-01-06T10:30:00Z
```

This reduces data transfer and ensures you only process events that occurred since your last poll.

### 5. Monitor Bot Participation
Remember that the bot itself is **not included** in participant events. If you need to track when the bot joins or leaves, monitor the bot's state changes instead:
- Use the `bot.state_change` webhook trigger
- Check for states like `in_meeting`, `left_meeting`, etc.

### 6. Handle Reconnections
Participants may temporarily disconnect and reconnect (e.g., due to network issues). A participant who disconnects briefly will generate:
1. A `leave` event when they disconnect
2. A `join` event when they reconnect (potentially with a new `participant_uuid`)

Consider implementing grace periods or connection tracking to distinguish between brief disconnections and intentional departures.

### 7. Rate Limiting Considerations
When building systems that react to participant events:
- Don't trigger heavy operations on every join event (e.g., API calls to external services)
- Consider batching operations or using a queue system for high-volume meetings
- Implement exponential backoff for webhook delivery failures

## Technical Details

### Event Ordering
Events are ordered by their `timestamp_ms` field, which represents when the event occurred according to the meeting platform. Events are generally delivered in chronological order, but network conditions may occasionally cause out-of-order delivery.

### Event Retention
Participant events are retained indefinitely and can be queried at any time through the API. However, we recommend exporting important event data to your own systems for long-term storage and analysis.

### Polling vs Webhooks
- **Webhooks**: Real-time delivery (typically within seconds) - Recommended for time-sensitive operations
- **API Polling**: Controlled request rate, useful for batch processing or when webhooks aren't available

Both methods deliver the same event data. Choose based on your system's requirements.
