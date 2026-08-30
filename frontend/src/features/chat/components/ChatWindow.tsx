import { useState, useRef, useEffect} from "react";
import ChatBubble from "@/components/chat/ChatBubble";
import ChatInput from "@/components/chat/ChatInput";
import type { ChatMessage, ChatResponse } from "@/types/chat";
import QuickReplies from "@/components/chat/QuickReplies";
import TypingIndicator from "@/components/chat/TypingIndicator";
import WelcomeScreen from "@/components/chat/WelcomeScreen";

//every change on useState variable triggers render from react (render runs all the code, but render returns old value on useRef)
//react renders (execute all its changed useState) only when the code isnt being run (code ends or in await mode)

const ChatWindow = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            role: "bot",
            content: "Halo! Selamat datang di Klinik Cantik Bella. Ada yang bisa dibantu?",
            timestamp: new Date().toISOString(),
        },
    ]);
    //for now, set always false untill there is api
    const [isLoading, setIsLoading] = useState(false);
    //set bottomRef as variable that reference/point to a div (HTMLDivElement)
    const bottomRef = useRef<HTMLDivElement>(null);

    //useEffect(callback, deps): runs callback function after render, reruns when deps change. note: everytime messages changed, run callbacks after react renders everything
    useEffect(() => {
        bottomRef.current?.scrollIntoView({behavior: "smooth"}); // '.current' access the div then scroll to it smoothly.
    }, [messages]) 

    const userId = useRef(`user_${Date.now()}`); //useRef bcs we dont want user id to change every time react re-renders

    //props that will be sent to ChatInput then ChatInput decide when to run 
    const handleSend = async (message: string) => {
        const userMsg: ChatMessage = {
            role: "user",
            content: message,
            timestamp: new Date().toISOString(),
        };
        //calling function from useState, if we fill a function in it, react will pass newest state value to the args of the function 
        //if we fill a value (not function), react wont pass any args, react will change the current state to the new value
        setMessages((prev) => [...prev, userMsg]); 
        setIsLoading(true); //disable the sendbutton due to sending request to backend and waiting for response

        try{
            //await here make react to renders changed useState above (setIsLoading and setMessages) 
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/chat`, {
                method: "POST",
                headers: {"Content-Type": "application/json"}, //tell http the type of data to be sent
                body: JSON.stringify({ //convert to json string (http only accept string)
                    user_id: userId.current,
                    message: message,
                }),
            });
            //response.ok = status code between 200-299, out of that will be trown to catch(error)
            if(!response.ok) throw new Error(`HTTP ${response.status}`);

            const data: ChatResponse = await response.json();

            const botMsg: ChatMessage = {
                role: "bot",
                content: data.reply,
                timestamp: data.timestamp,
                quick_replies: data.quick_replies,
            };
            //react passes args(latest message list) to prev, then add botMsg
            setMessages((prev) => [...prev, botMsg]);
        } catch (error){
            const errorMsg: ChatMessage = {
                role: "bot",
                content: "Maaf, terjadi kesalahan. Coba lagi ya.",
                timestamp: new Date().toISOString(),
            };
            //react passes args(latest message list) to prev, then add errorMsg
            setMessages((prev) => [...prev, errorMsg]);
        } finally{
            setIsLoading(false); //enable the sendbutton 
        };
    };

    const lastBotMsg = [...messages].reverse().find((m) => m.role === "bot"); //reverse: reverse the list member, find: loop every message and pass each list member as args. If return true, function returns that correct list member
    const quickReplies = lastBotMsg?.quick_replies ?? []; //"??" as a fallback if value is undefined (no bot message/no quickreply), so default = []

    //overflow-y-auto: activate vertical scroll if the contents is higher than the container
    return (
        <div className="flex flex-col h-screen max-w-md mx-auto bg-white shadow-lg">
            {messages.length <= 1 ? (
                <WelcomeScreen onAction = {handleSend}/>
            ) : (
                <>
                    {/*header*/}
                    <div className="flex items-center gap-3 px-4 py-3 bg-teal-50 border-b border-teal-100">
                        <div className="w-9 h-9 rounded-full bg-teal-600 flex items-center justify-center">
                            <span className="text-white text-sm font-bold">KC</span>
                        </div>
                        <p className="text-teal-800 text-sm font-semibold">Klinik Cantik X</p>
                    </div>
                    {/*main component*/}
                    <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-white">
                        {messages.map((msg, i) => (
                            <ChatBubble key={i} message={msg}/>
                        ))}
                        {isLoading && <TypingIndicator />} {/*if isLoading = True, will show typing indicator like the bot is writing*/}
                        <div ref={bottomRef}/> {/*'ref=' make this div as reference of bottomRef which is an invisible div below the Chat bubbles*/}
                    </div>
                    {quickReplies.length > 0 && <QuickReplies quickReplies={quickReplies} onSelect={handleSend} disabled={isLoading}/>}
                </>
            )}
            <ChatInput onSend={handleSend} disabled={isLoading}/>
        </div>
    );
};

export default ChatWindow;