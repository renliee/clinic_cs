interface WelcomeScreenProps {
    onAction: (message: string) => void;
}

const actions = [
    {label: "Booking Treatment", message: "Mau booking treatment"},
    {label: "Jenis Treatment", message: "Ada treatment apa aja?"},
    {label: "Cek Harga", message: "Berapa aja harga treatment?"},
    {label: "Jam Buka", message: "Jam operasional klinik setiap hari kapan aja?"},
    {label: "Lokasi", message: "Klinik lokasinya ada dimana aja?"},
];

// items/justify center is for its child, while mx-auto for its own element
const WelcomeScreen = ({ onAction }: WelcomeScreenProps) => {
    return(
        <div className="flex-1 flex flex-col items-center justify-center gap-8 p-8">
            <div className="text-center">
                <div className="w-16 h-16 rounded-full bg-teal-600 flex items-center justify-center mx-auto mb-4">
                    <span className="text-white text-xl font-bold">KC</span>
                </div>
                <h1 className="text-xl font-semibold text-gray-800">Klinik Cantik X</h1>
                <p className="text-gray-400 text-sm mt-1">Assisten booking digital</p>
            </div>
            <div className="flex flex-col gap-2.5 w-full max-w-xs">
                {actions.map((action, i) =>(
                    <button
                        key={i}
                        onClick={() => onAction(action.message)}
                        className="rounded-full border border-teal-600 text-teal-700 px-6 py-3 text-sm font-medium hover:bg-teal-50 transition-colors"
                    >
                        {action.label}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default WelcomeScreen;