# Frontend Integration for Judy Chat

This document provides instructions and guidelines for integrating the Judy Chatbot with your frontend application. Judy Chatbot's backend is implemented using Django Channels and handles WebSocket connections for real-time messaging.

## WebSocket Connection

### Establishing a Connection

- **URL**: Connect to the WebSocket using this URL: `ws://judy-dev.essentialrecruit-api.com/ws/chat/`.
- **Connection Protocol**: Use WebSocket (ws) or WebSocket Secure (wss), depending on your server configuration.
- **Handling Connection**: Implement logic to manage successful or failed connection attempts.

#### Example

```javascript
const socket = new WebSocket("ws://judy-dev.essentialrecruit-api.com/ws/chat/");

socket.onopen = function(e) {
  console.log("[open] Connection established");
};

socket.onerror = function(error) {
  console.error(`[error] ${error.message}`);
};
```

## Sending Messages

### Message Format

Messages to the chatbot should be sent in JSON format.

- **Conversational Query**:
  ```json
  {
    "type": "user_message",
    "message": "Your question here"
  }```

- **Upvote or Downvote a Returned Response**:
  ```json
  {
    "type": "upvote",
    "messageId": "message id of the message to be upvoted"
  }

  {
    "type": "downvote",
    "messageId": "message id of the message to be downvoted"
  }```

- **End Session After a Stipulated Period Of Inactivity**:
  ```json
  {
    "type": "end_session",
    "userId": "Id of the user from ER platform",
    "email": "Email of the user from ER platform",
    "name": "Full name of the user from ER platform",
    "role": "Role of the user from ER platform",  # For example, a candidate or a recruiter
  }```

Example
javascript
function sendMessage(message) {
  socket.send(JSON.stringify({
    type: "user_message",
    message: message
  }));
}

Receiving Messages
The chatbot will send responses in JSON format.

- **Ongoing Chats**:
  ```json
  {
    "message": "Judy's response here [might include citation number]",
    "citations": {}, # citation number as key, and citation content as value
    "messageId": "msg_XQWvsWPbtWk9U6XUQABEYpxw"  # message id to enable upvoting or downvoting
  }```

- **Ended Chats**:
  ```json
  {
    "message": "session_ended",
  }```

Handle incoming messages by adding an event listener to the socket.
Example
javascript
socket.onmessage = function(event) {
  const response = JSON.parse(event.data);
  console.log("Message from server:", response.message);
};

Handling Different Message Types
The chatbot can send different types of messages, such as chat responses, session end confirmations, etc.
Implement logic to handle different type values in the received messages.
Example
javascript
Copy code
socket.onmessage = function(event) {
  const response = JSON.parse(event.data);
  switch(response.type) {
    case "chat_message":
      displayChatMessage(response.message);
      break;
    // Handle other message types as needed
  }
};

## Closing the Connection

### Close the WebSocket connection when it's no longer needed or when the user leaves the chat interface.

Example
javascript

function closeConnection() {
  socket.close();
}

## Error Handling

### Implement error handling for scenarios such as network issues, server downtime, or JSON parsing errors.
Example
javascript
socket.onerror = function(error) {
  console.error("WebSocket Error: ", error);
};

## Additional Tips
- Ensure that your frontend handles reconnection logic in case of dropped connections.
- Provide user feedback for connection status (e.g., connecting, connected, disconnected).
- Consider security aspects, such as using WebSocket Secure (wss) and handling authentication tokens if necessary.
