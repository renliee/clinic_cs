import ChatBubble from "@/components/chat/ChatBubble";
import type { ChatMessage } from "@/types/chat";

const testMessage: ChatMessage[] = [
    {
        role: "bot",
        content: "Halo! Selamat datang di Klinik Cantik Bella. Ada yang bisa saya bantu?",
        timestamp: new Date().toISOString(),
    },
    {
        role: "user",
        content: "Mau booking facial dong",
        timestamp: new Date().toISOString(),
    },
    {
        role: "bot",
        content: "Baik kak! Untuk booking facial, boleh tau nama lengkapnya?",
        timestamp: new Date().toISOString(),
    },
]

const App = () => {
    return (
        <div className="flex flex-col gap-3 p-4 max-w-md mx-auto">
            {testMessage.map((msg, i) => (
                <ChatBubble key={i} message={msg}/>
            ))}
        </div>
    );
};

export default App;