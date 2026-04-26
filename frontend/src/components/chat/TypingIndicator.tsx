const TypingIndicator = () => {
    return (
        <div className="flex items-end gap-2 justify-start">
            <div className="w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center flex-shrink-0 mb-1">
                <span className="text-white text-xs font-bold">KC</span>
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1.5 items-center">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
        </div>
    );
};
    
export default TypingIndicator;