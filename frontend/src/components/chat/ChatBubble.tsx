import type { ChatMessage } from "@/types/chat"; //@ is "/src" in tsconfig.app.json

interface ChatBubbleProps {
    message: ChatMessage;
}

//{message} is a props: {message: 'real msg'}
const ChatBubble = ({message}: ChatBubbleProps) => {
    const isUser = message.role === "user";

    return (
        <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>  {/*if chat is from user, push chat to the right otherwise left*/}
            {/*max-w-[80%]: max width is 80% of the parents full width*/}
            {/*rounded-br-sm: to give a detail of point to the sender message; whitespace-pre-wrap: execute '\n' not directly write it*/}
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 ${ 
                    isUser
                        ? "bg-blue-500 text-white rounded-br-sm"
                        : "bg-gray-100 text-gray-900 rounded-bl-sm"
                }`}>
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
        </div>
    );
};

export default ChatBubble;