import React, { useState, useRef } from 'react';

export default function MorseCodeCommunicator() {
    const [isSending, setIsSending] = useState(false);
    const [morseOutput, setMorseOutput] = useState('');
    const [blankDelay, setBlankDelay] = useState(1500);
    const pressStartTime = useRef<number | null>(null);
    const lastInputTime = useRef(Date.now());
    const wordTimeout = useRef<NodeJS.Timeout | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const maxDisplayLength = 30;

    const handlePressStart = () => {
        pressStartTime.current = Date.now();
        setIsSending(true);
        if (wordTimeout.current) clearTimeout(wordTimeout.current);
    };

    const handlePressEnd = () => {
        if (pressStartTime.current === null) return;

        const pressDuration = Date.now() - pressStartTime.current;
        pressStartTime.current = null;
        setIsSending(false);
        lastInputTime.current = Date.now();

        const char = pressDuration < 300 ? '•' : '-';
        setMorseOutput(output => {
            const newOutput = output + char;
            return newOutput.length > maxDisplayLength ? newOutput.slice(newOutput.length - maxDisplayLength) : newOutput;
        });

        wordTimeout.current = setTimeout(() => {
            setMorseOutput(output => {
                const newOutput = output + ' ';
                return newOutput.length > maxDisplayLength ? newOutput.slice(newOutput.length - maxDisplayLength) : newOutput;
            });
        }, blankDelay);
    };

    const handleKnobChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(e.target.value);
        setBlankDelay(value);
    };

    return (
        <div className="bg-[#393E46] text-[#E4D6BD] min-h-screen flex flex-col items-center justify-center p-8 relative">
            {/* Rotatable Knob Control */}
            <div className="absolute top-6 left-6 flex flex-col items-center">
                <label htmlFor="blankDelay" className="mb-2 text-sm">Blank Timing</label>
                <input
                    type="range"
                    id="blankDelay"
                    min="500"
                    max="1500"
                    value={blankDelay}
                    onChange={handleKnobChange}
                    className="w-32 h-6 appearance-none bg-[#A29787] rounded-lg hover:bg-[#A29787]"
                />

                <span className="text-xs mt-1">{blankDelay}ms</span>
            </div>

            <h1 className="text-3xl font-bold mb-6">Morse Code Communicator</h1>

            <div className="flex items-center gap-12 mb-8">
                {/* Sending Lamp */}
                <div className="flex flex-col items-center">
                    <div className={`w-12 h-12 rounded-full border-2 border-[#FFD86E] ${isSending ? 'bg-[#FFD86E]' : 'bg-[#2F343D]'} transition-colors`}></div>
                    <span className="mt-2 text-sm">Sending</span>
                </div>

                {/* Tap Button */}
                <button
                    onPointerDown={handlePressStart}
                    onPointerUp={handlePressEnd}
                    className="bg-[#908573] hover:bg-[#A29787] text-white px-6 py-3 rounded-xl shadow-lg active:scale-95 transition-transform"
                >
                    Tap for Morse
                </button>

                {/* Receiving Lamp */}
                <div className="flex flex-col items-center">
                    <div className={`w-12 h-12 rounded-full border-2 border-[#6EDB8A] bg-[#2F343D] transition-colors`}></div>
                    <span className="mt-2 text-sm">Receiving</span>
                </div>
            </div>

            {/* Morse Display Area */}
            <div className="w-full max-w-2xl bg-[#908573] border border-[#A29787] rounded-lg p-4 text-xl font-mono text-[#1D222B] overflow-hidden whitespace-nowrap">
                <div className="w-full overflow-hidden">
                    <div className="inline-block" ref={scrollRef} style={{ whiteSpace: 'nowrap' }}>
                        {morseOutput.replace(/ /g, '_').padStart(maxDisplayLength)}
                    </div>
                </div>
            </div>
        </div>
    );
}