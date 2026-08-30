import type { QuickReply } from "@/types/chat";

interface QuickRepliesProps {
    quickReplies: QuickReply[]; 
    onSelect: (payload: string) => void;
    disabled?: boolean;
}

const QuickReplies = ({ quickReplies, onSelect, disabled = false}: QuickRepliesProps) => {
    return (
        <div className="flex gap-2 px-4 py-2 flex-wrap"> {/* flex wrap: if buttons exceeds width, they will move to the next line*/}
            {quickReplies.map((qr, i) => (
                <button
                    key={i}
                    onClick = {() => {
                        if(disabled) return;
                        onSelect(qr.payload)}
                    }
                    disabled = {disabled}
                    className="border border-teal-600 text-teal-700 text-sm rounded-full px-3.5 py-1.5 hover:bg-teal-50 disabled:opacity-40 transition-colors"
                >
                    {qr.label}
                </button>
            ))}
        </div>
    )
}

export default QuickReplies;