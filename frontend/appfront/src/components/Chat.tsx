import React from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ChatMessage, sendMessage } from '../api/api';

interface ChatState {
    userId: string;
    sessionId: string;
}

const Chat = (): JSX.Element => {
    const [state] = React.useState<ChatState>({
        userId: uuidv4(),
        sessionId: uuidv4()
    });

    const handleSendMessage = async (message: string) => {
        try {
            const chatMessage: ChatMessage = {
                message,
                user_id: state.userId,
                session_id: state.sessionId,
                metadata: {}
            };
            
            const response = await sendMessage(chatMessage);
            // Handle response...
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };

    return (
        <div>
            {/* Chat UI implementation */}
        </div>
    );
};

export default Chat;
