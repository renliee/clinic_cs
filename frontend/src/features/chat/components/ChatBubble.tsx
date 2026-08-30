import type { ChatMessage } from "@/types/chat"; //@ is "/src" in tsconfig.app.json

interface ChatBubbleProps {
    message: ChatMessage;
}

//{message} is a props: {message: 'real msg'}
const ChatBubble = ({message}: ChatBubbleProps) => {
    const isUser = message.role === "user";

    return (
        <div className={`flex items-end gap-2 ${isUser ? "justify-end" : "justify-start"}`}>  {/*if chat is from user, push chat to the right otherwise left*/}
            {/*bot avatar*/}
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center flex-shrink-0 mb-1">
                    <span className="text-white text-xs font-bold">KC</span>
                </div>
            )}
            {/*max-w-[80%]: max width 80% of the parents width; overflow: handle huge emoji, etc to stay in border; leading-relaxed: loosen the space line; break-words: cut message to next line if very long word*/}
            <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 overflow-hidden ${ 
                isUser
                    ? "bg-teal-600 text-white rounded-br-sm"
                    : "bg-gray-100 text-gray-800 rounded-bl-sm"
            }`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{message.content}</p>
            </div>
        </div>
    );
};

export default ChatBubble;  