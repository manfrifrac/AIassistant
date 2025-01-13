import axios from 'axios';

const API_BASE_URL = '/api';  // Update to match backend prefix

export const API_PATHS = {
    CHAT: `${API_BASE_URL}/chat/message`,
    AUDIO: `${API_BASE_URL}/audio`,
    STATUS: `${API_BASE_URL}/status`
};

export interface ChatMessage {
    message: string;
    user_id: string;
    session_id: string;
    metadata: Record<string, any>;
}

export interface ChatResponse {
    message: string;
    session_id: string;
    metadata: Record<string, any>;
    status: string;
    audio_response?: string;
}

// Update API request functions
export const sendMessage = async (message: ChatMessage): Promise<ChatResponse> => {
    try {
        const response = await axios.post<ChatResponse>(API_PATHS.CHAT, message);
        return response.data;
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
};

// ...existing code...
