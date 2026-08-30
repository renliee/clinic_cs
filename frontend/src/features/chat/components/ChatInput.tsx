import { useState } from "react";

//disabled = boolean info from parents; onSend = function to run from parents;
interface ChatInputProps {
    onSend: (message: string) => void;
    disabled?: boolean,
}

//ChatInput decide when to run the onSend function (when user click button or press Enter at keyboard)
const ChatInput = ({onSend, disabled = false}: ChatInputProps) => {
    const [input, setInput] = useState("");

    //handleSend is called everytime user want to sent message
    const handleSend = () => {
        if(disabled) return; //handle if user click enter 2x fast
        const message = input.trim();
        if (message === "") return;
        onSend(message);
        setInput("");
    };

    //border-t as separator line 
    return (
        <div className="flex gap-2 p-3 border-t border-gray-100 bg-white">
            <input 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                    if(e.key === "Enter" && !e.shiftKey){
                        //prevent strange thing from browser when enter is clicked
                        e.preventDefault(); 
                        handleSend();
                    }
                }}
                aria-label="Ketik pesan"
                placeholder="Ketik pesan..."
                disabled={disabled}
                className="flex-1 bg-gray-50 rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-teal-500 placeholder-gray-400"
            />
            {/*if no input yet, disabled send button*/}
            <button
                onClick={handleSend}
                disabled={disabled || input.trim() === ""} 
                className="bg-teal-600 text-white rounded-full px-5 py-2.5 text-sm font-medium hover:bg-teal-700 disabled:opacity-40 transition-colors"
            >
                Kirim
            </button>
        </div>
    );
};

export default ChatInput;