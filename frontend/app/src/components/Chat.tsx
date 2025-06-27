// src/components/EnhancedMorseChat.tsx
import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import { channelService } from '../services/channelService';

interface User {
    id: string;
    callsign: string;
    status: 'online' | 'offline' | 'waiting' | 'busy';
    created_at: string;
}

interface EnhancedMorseChatProps {
    token: string;
    currentUser: User;
    invitedFriend?: User | null;
    joinChannelId?: string | null;
    onChannelConnectionChange?: (isConnected: boolean, channelId?: string) => void;
}

interface ChannelInvitation {
    friendId: string;
    friendCallsign: string;
    channelId: string;
}

export interface MorseChatRef {
    joinChannel: (channelId: string) => Promise<void>;
    disconnect: () => void;
    getConnectionStatus: () => {
        isConnected: boolean;
        isConnecting: boolean;
        channelId: string | null;
    };
}

const EnhancedMorseChat = forwardRef<MorseChatRef, EnhancedMorseChatProps>(({
                                                                                token,
                                                                                currentUser,
                                                                                invitedFriend,
                                                                                joinChannelId,
                                                                                onChannelConnectionChange
                                                                            }, ref) => {
    const [isSending, setIsSending] = useState(false);
    const [isReceiving, setIsReceiving] = useState(false);
    const [morseOutput, setMorseOutput] = useState('');
    const [blankDelay, setBlankDelay] = useState(1500);
    const [isConnected, setIsConnected] = useState(false);
    const [partner, setPartner] = useState<User | null>(null);
    const [connectionStatus, setConnectionStatus] = useState('Disconnected');
    const [channelId, setChannelId] = useState<string | null>(null);
    const [pendingInvitation, setPendingInvitation] = useState<ChannelInvitation | null>(null);
    const [isConnecting, setIsConnecting] = useState(false);

    const pressStartTime = useRef<number | null>(null);
    const lastInputTime = useRef(Date.now());
    const wordTimeout = useRef<NodeJS.Timeout | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const maxDisplayLength = 50;

    // Expose methods to parent components via ref
    useImperativeHandle(ref, () => ({
        joinChannel: async (targetChannelId: string) => {
            await connectToChannel('specific', targetChannelId);
        },
        disconnect: () => {
            handleDisconnect();
        },
        getConnectionStatus: () => {
            return {
                isConnected,
                isConnecting,
                channelId
            };
        }
    }));

    // Effect to handle join channel from sidebar
    useEffect(() => {
        if (joinChannelId && !isConnected && !isConnecting) {
            console.log(`Auto-joining channel: ${joinChannelId}`);
            connectToChannel('specific', joinChannelId);
        }
    }, [joinChannelId, isConnected, isConnecting]);

    // Notify parent of connection status changes
    useEffect(() => {
        if (onChannelConnectionChange) {
            onChannelConnectionChange(isConnected, channelId || undefined);
        }
    }, [isConnected, channelId, onChannelConnectionChange]);

    // Connect to WebSocket channel using channelService
    const connectToChannel = async (channelType: 'random' | 'specific' | 'create', specificChannelId?: string) => {
        setIsConnecting(true);

        const callbacks = {
            onOpen: (connectedChannelId: string) => {
                setIsConnected(true);
                setIsConnecting(false);
                setChannelId(connectedChannelId);

                if (channelType === 'create') {
                    setConnectionStatus(`Hosting channel ${connectedChannelId} - Waiting for someone to join...`);
                } else if (specificChannelId) {
                    setConnectionStatus(`Joining channel ${specificChannelId}...`);
                } else {
                    setConnectionStatus('Connected - Waiting for partner...');
                }
            },
            onUserJoined: (user: User, connectedChannelId: string) => {
                setPartner(user);
                setConnectionStatus(`Connected with ${user.callsign}`);
                if (connectedChannelId && connectedChannelId !== channelId) {
                    setChannelId(connectedChannelId);
                }
            },
            onUserLeft: () => {
                setPartner(null);
                setConnectionStatus('Partner disconnected');
            },
            onMorseSignal: (signal: string) => {
                handleReceivedMorse(signal);
            },
            onClose: (event: CloseEvent) => {
                setIsConnected(false);
                setIsConnecting(false);
                setPartner(null);

                if (event.code === 1008) {
                    setConnectionStatus(`Connection failed: ${event.reason || 'Authentication error'}`);
                } else {
                    setConnectionStatus('Disconnected');
                }

                // Only clear channel ID for random channels
                if (channelType === 'random') {
                    setChannelId(null);
                }
            },
            onError: (error: Event) => {
                console.error('WebSocket error:', error);
                setConnectionStatus('Connection error');
                setIsConnecting(false);
            }
        };

        try {
            const result = await channelService.connectToChannel(
                channelType,
                token,
                currentUser,
                callbacks,
                specificChannelId
            );

            if (!result.success) {
                setConnectionStatus(result.message);
                setIsConnecting(false);
            }
        } catch (error) {
            console.error('Failed to connect to channel:', error);
            setConnectionStatus('Failed to connect');
            setIsConnecting(false);
        }
    };

    const handleReceivedMorse = (signal: string) => {
        setIsReceiving(true);
        setTimeout(() => setIsReceiving(false), 200);

        setMorseOutput(output => {
            const newOutput = output + signal;
            return newOutput.length > maxDisplayLength ? newOutput.slice(newOutput.length - maxDisplayLength) : newOutput;
        });
    };

    const handleDisconnect = () => {
        channelService.disconnect();
        setPartner(null);
        setIsConnected(false);
        setIsConnecting(false);
        setConnectionStatus('Disconnected');
    };

    const createChannel = () => {
        connectToChannel('create');
    };

    const joinRandomChannel = () => {
        connectToChannel('random');
    };

    const acceptInvitation = () => {
        if (pendingInvitation) {
            connectToChannel('specific', pendingInvitation.channelId);
            setPendingInvitation(null);
        }
    };

    const declineInvitation = () => {
        setPendingInvitation(null);
    };

    useEffect(() => {
        if (invitedFriend && !isConnected) {
            const newChannelId = channelService.generateChannelId();
            setPendingInvitation({
                friendId: invitedFriend.id,
                friendCallsign: invitedFriend.callsign,
                channelId: newChannelId
            });
        }
    }, [invitedFriend, isConnected]);

    const handlePressStart = () => {
        if (!isConnected) return;

        pressStartTime.current = Date.now();
        setIsSending(true);
        if (wordTimeout.current) clearTimeout(wordTimeout.current);
    };

    const handlePressEnd = () => {
        if (pressStartTime.current === null || !isConnected) return;

        const pressDuration = Date.now() - pressStartTime.current;
        pressStartTime.current = null;
        setIsSending(false);
        lastInputTime.current = Date.now();

        const signal = pressDuration < 300 ? '•' : '-';

        // Send to partner via channelService
        const sent = channelService.sendMorseSignal(signal);
        if (sent) {
            setMorseOutput(output => {
                const newOutput = output + signal;
                return newOutput.length > maxDisplayLength ? newOutput.slice(newOutput.length - maxDisplayLength) : newOutput;
            });

            // Auto-send space after delay
            wordTimeout.current = setTimeout(() => {
                const spaceSignal = ' ';
                const spaceSent = channelService.sendMorseSignal(spaceSignal);
                if (spaceSent) {
                    setMorseOutput(output => {
                        const newOutput = output + spaceSignal;
                        return newOutput.length > maxDisplayLength ? newOutput.slice(newOutput.length - maxDisplayLength) : newOutput;
                    });
                }
            }, blankDelay);
        }
    };

    const handleKnobChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(e.target.value);
        setBlankDelay(value);
    };

    const clearOutput = () => {
        setMorseOutput('');
    };

    useEffect(() => {
        return () => {
            channelService.disconnect();
        };
    }, []);

    return (
        <div className="bg-[#393E46] text-[#E4D6BD] h-full flex flex-col justify-center p-4 sm:p-8 relative">
            {/* Pending Invitation Modal */}
            {pendingInvitation && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-[#222831] rounded-lg p-6 max-w-md w-full mx-4">
                        <h3 className="text-xl font-bold mb-4 text-[#DFD0B8]">
                            Channel Invitation
                        </h3>
                        <p className="text-[#A29787] mb-6">
                            {pendingInvitation.friendCallsign} invited you to join a private morse channel.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={acceptInvitation}
                                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md transition-colors"
                            >
                                Accept
                            </button>
                            <button
                                onClick={declineInvitation}
                                className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-md transition-colors"
                            >
                                Decline
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Header */}
            <h1 className="text-2xl sm:text-3xl font-bold mb-6 text-center">Morse Code Communicator</h1>

            {/* Top Controls Container */}
            <div className="w-full max-w-4xl mx-auto mb-8">
                {/* Blank Timing - Top Left */}
                <div className="absolute top-4 sm:top-6 left-4 sm:left-6">
                    <label htmlFor="blankDelay" className="mb-2 text-sm block">Blank Timing</label>
                    <input
                        type="range"
                        id="blankDelay"
                        min="500"
                        max="1500"
                        value={blankDelay}
                        onChange={handleKnobChange}
                        className="w-32 h-2 bg-[#393E46] rounded-lg appearance-none cursor-pointer slider"
                        style={{
                            background: `linear-gradient(
                                            to right, 
                                            #908573 0%, 
                                            #908573 ${((blankDelay - 500) / 1000) * 100}%, 
                                            #393E46 ${((blankDelay - 500) / 1000) * 100}%, 
                                            #222831 100%)`
                        }}
                    />
                    <span className="text-xs mt-1 block">{blankDelay}ms</span>
                </div>

                {/* Status Info - Top Right */}
                <div className="absolute top-4 sm:top-6 right-4 sm:right-6 text-right">
                    <div className="text-sm text-[#A29787]">Status:</div>
                    <div className="text-sm font-medium text-[#E4D6BD]">
                        {isConnecting ? 'Connecting...' : connectionStatus}
                    </div>
                    {partner && (
                        <div className="text-xs text-[#A29787] mt-1">
                            Partner: {partner.callsign}
                        </div>
                    )}
                    {channelId && (
                        <div className="text-xs text-[#A29787] mt-1">
                            Channel: {channelId}
                        </div>
                    )}
                </div>

                {/* Connection Buttons - Center */}
                <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 max-w-md mx-auto">
                    {!isConnected && !isConnecting ? (
                        <>
                            <button
                                onClick={createChannel}
                                className="w-full bg-[#908573] hover:bg-[#A29787] text-white px-4 py-2 rounded-md transition-colors text-sm"
                            >
                                🏠 Create Channel
                            </button>
                            <button
                                onClick={joinRandomChannel}
                                className="w-full bg-[#6B7280] hover:bg-[#4B5563] text-white px-4 py-2 rounded-md transition-colors text-sm"
                            >
                                🎲 Find Random Partner
                            </button>
                            {joinChannelId && (
                                <button
                                    onClick={() => connectToChannel('specific', joinChannelId)}
                                    className="w-full bg-[#5D6B3F] hover:bg-[#6D7B4F] text-white px-4 py-2 rounded-md transition-colors text-sm"
                                >
                                    📡 Join Channel {joinChannelId}
                                </button>
                            )}
                        </>
                    ) : isConnecting ? (
                        <button
                            disabled
                            className="w-full bg-[#555] text-[#999] px-4 py-2 rounded-md text-sm cursor-not-allowed"
                        >
                            Connecting...
                        </button>
                    ) : (
                        <button
                            onClick={handleDisconnect}
                            className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md transition-colors text-sm"
                        >
                            Disconnect
                        </button>
                    )}
                </div>
            </div>

            {/* Main Interface */}
            <div className="flex flex-col items-center gap-8 mb-8">
                {/* Lamps and Button */}
                <div className="flex flex-col sm:flex-row items-center gap-8 sm:gap-12">
                    {/* Sending Lamp */}
                    <div className="flex flex-col items-center">
                        <div className={`w-12 h-12 rounded-full border-2 border-[#FFD86E] ${isSending ? 'bg-[#FFD86E]' : 'bg-[#2F343D]'} transition-colors`}></div>
                        <span className="mt-2 text-sm">Sending</span>
                    </div>

                    {/* Tap Button */}
                    <button
                        onPointerDown={handlePressStart}
                        onPointerUp={handlePressEnd}
                        disabled={!isConnected || isConnecting}
                        className={`px-6 py-3 rounded-xl shadow-lg active:scale-95 transition-transform ${
                            isConnected && !isConnecting
                                ? 'bg-[#908573] hover:bg-[#A29787] text-white'
                                : 'bg-[#555] text-[#999] cursor-not-allowed'
                        }`}
                    >
                        {isConnecting ? 'Connecting...' : isConnected ? 'Tap for Morse' : 'Connect First'}
                    </button>

                    {/* Receiving Lamp */}
                    <div className="flex flex-col items-center">
                        <div className={`w-12 h-12 rounded-full border-2 border-[#6EDB8A] ${isReceiving ? 'bg-[#6EDB8A]' : 'bg-[#2F343D]'} transition-colors`}></div>
                        <span className="mt-2 text-sm">Receiving</span>
                    </div>
                </div>
            </div>

            {/* Morse Display Area */}
            <div className="w-full max-w-4xl mx-auto bg-[#908573] border border-[#A29787] rounded-lg p-4 text-lg sm:text-xl font-mono text-[#1D222B] overflow-hidden">
                <div className="w-full overflow-hidden whitespace-nowrap">
                    <div className="inline-block" ref={scrollRef}>
                        {morseOutput.replace(/ /g, '_').padStart(maxDisplayLength, '_')}
                    </div>
                </div>
            </div>
            <button
                onClick={clearOutput}
                className="w-full max-w-4xl mx-auto mt-2 bg-[#393E46] hover:bg-[#4A5059] text-[#E4D6BD] px-4 py-2 rounded-md transition-colors text-sm"
            >
                Clear Display
            </button>

            {/* Instructions */}
            <div className="mt-6 text-center text-sm text-[#A29787] max-w-2xl mx-auto px-4">
                <p>Short tap = dot (•) | Long tap = dash (-) | Pause = space</p>
                {!isConnected && !isConnecting && (
                    <p className="mt-2">Connect to start communicating with morse code!</p>
                )}
                {isConnecting && (
                    <p className="mt-2">Connecting to channel...</p>
                )}
                {isConnected && !partner && (
                    <p className="mt-2">Waiting for someone to join your channel...</p>
                )}
            </div>
            <style>{`
                .slider::-webkit-slider-thumb {
                    appearance: none;
                    width: 20px;
                    height: 20px;
                    background: #DFD0B8;
                    cursor: pointer;
                    border-radius: 50%;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }

                .slider::-moz-range-thumb {
                    width: 20px;
                    height: 20px;
                    background: #DFD0B8;
                    cursor: pointer;
                    border-radius: 50%;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    border: none;
                }
            `}</style>
        </div>
    );
});

EnhancedMorseChat.displayName = 'EnhancedMorseChat';

export default EnhancedMorseChat;