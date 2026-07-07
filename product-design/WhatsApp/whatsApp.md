## Functional Requirements
- Users should be able to send/receive messages.
- Users should be able to start group chats with multiple participants (limit 100).
- Users should be able to receive messages sent while they are not online (up to 30 days).
- Users should be able to send/receive media in their messages.

## NFR

- Eventaully consistent data
- Message should be delivered to all user withi in 500 ms (low lattency)
- System should able handel billion user and their message
- The system should be resilient, on individual componet failure

## core entities
User
Message
Group/Chats (2 to 100 user)


## API

- POST v1/chats/
{
    user_ids : []
    Name
    image
}
PATCH v1/chats/{id}
{
    user_ids : []
    Name
    image
}
.....

## WS commands

SendMessage{
    chat_id
    message
    attachments
}
SendAck{
    chat_id
    Recived
}

- we will use webscoket for sending and recving messages to chat and reaming can be done through REST.



