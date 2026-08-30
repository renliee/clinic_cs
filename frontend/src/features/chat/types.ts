export interface ChatRequest {
    user_id: string;
    message: string;
}

export interface QuickReply {
    label: string;
    payload: string;
}

export interface ChatResponse {
    reply: string;
    user_id: string;
    quick_replies: QuickReply[]; //list of QuickReply, default [] set from schemas.py
    timestamp: string;
}

//consist full conversation between user and bot to show on UI
export interface ChatMessage {
    role: "bot" | "user";
    content: string;
    timestamp: string;
    quick_replies?: QuickReply[]; //optional bcs user messages ever have QuickReply
}