document.addEventListener('DOMContentLoaded', function() {
    const conversationId = document.getElementById('conversation-id').value;
    const userId = document.getElementById('user-id').value;
    const messageContainer = document.getElementById('message-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const fileInput = document.getElementById('file-input');

    // Initialize WebSocket
    const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${wsProtocol}${window.location.host}/ws/chat/${conversationId}/`;
    const chatSocket = new WebSocket(wsUrl);

    chatSocket.onopen = function() {
        console.log('WebSocket connected');
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'chat_message') {
            displayMessage(data);
            markMessagesAsRead();
        } else if (data.type === 'typing') {
            showTypingIndicator(data.user_id, data.username);
        } else if (data.type === 'read_receipt') {
            updateReadReceipt(data.message_id, data.user_id);
        }
    };

    chatSocket.onclose = function(e) {
        console.error('WebSocket closed:', e);
    };

    chatSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
    };

    // Send message
    function sendMessage() {
        const message = messageInput.value.trim();
        const files = fileInput.files;

        if (message || files.length > 0) {
            const formData = new FormData();
            formData.append('message', message);
            for (let file of files) {
                formData.append('attachments', file);
            }

            fetch(`/chat/conversations/${conversationId}/send/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            }).then(response => {
                if (response.ok) {
                    messageInput.value = '';
                    fileInput.value = '';
                } else {
                    console.error('Failed to send message');
                }
            });
        }
    }

    // Display message
    function displayMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', data.user_id == userId ? 'sent' : 'received');
        
        let content = `<p><strong>${data.username}</strong> <small>${data.timestamp}</small></p>`;
        if (data.message) {
            content += `<p>${data.message}</p>`;
        }
        if (data.attachments && data.attachments.length > 0) {
            data.attachments.forEach(attachment => {
                if (attachment.endsWith('.jpg') || attachment.endsWith('.png') || attachment.endsWith('.jpeg')) {
                    content += `<img src="${attachment}" alt="attachment" class="img-fluid" style="max-width: 200px;">`;
                } else {
                    content += `<a href="${attachment}" target="_blank">Download ${attachment.split('/').pop()}</a>`;
                }
            });
        }
        content += `<small class="read-status" data-message-id="${data.message_id}">${data.read_by.includes(parseInt(userId)) ? 'Read' : ''}</small>`;
        
        messageDiv.innerHTML = content;
        messageContainer.appendChild(messageDiv);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    // Typing indicator
    let typingTimeout;
    messageInput.addEventListener('input', function() {
        chatSocket.send(JSON.stringify({
            type: 'typing',
            user_id: userId,
            username: document.getElementById('username').value
        }));
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(() => {
            typingIndicator.innerHTML = '';
        }, 2000);
    });

    function showTypingIndicator(userIdOther, username) {
        if (userIdOther != userId) {
            typingIndicator.innerHTML = `${username} is typing...`;
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => {
                typingIndicator.innerHTML = '';
            }, 2000);
        }
    }

    // Mark messages as read
    function markMessagesAsRead() {
        fetch(`/chat/conversations/${conversationId}/mark_read/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({})
        }).then(response => {
            if (!response.ok) {
                console.error('Failed to mark messages as read');
            }
        });
    }

    function updateReadReceipt(messageId, userIdOther) {
        if (userIdOther != userId) {
            const readStatus = document.querySelector(`.read-status[data-message-id="${messageId}"]`);
            if (readStatus) {
                readStatus.textContent = 'Read';
            }
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // CSRF token utility
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});