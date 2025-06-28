// src/App.tsx
import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import Learn from './components/Learn';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import EnhancedMorseChat, { MorseChatRef } from './components/Chat';
import FriendsSidebar from './components/FriendsSidebar';

interface User {
    id: string;
    callsign: string;
    status: 'online' | 'offline' | 'waiting' | 'busy';
    created_at: string;
}

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [currentUser, setCurrentUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [showRegister, setShowRegister] = useState(false);
    const [invitedFriend, setInvitedFriend] = useState<User | null>(null);
    const [joinChannelId, setJoinChannelId] = useState<string | null>(null);
    const [currentChannelId, setCurrentChannelId] = useState<string | null>(null);

    // Ref to access MorseChat methods
    const morseChatRef = useRef<MorseChatRef>(null);

    // Check for existing authentication on app start
    useEffect(() => {
        const savedToken = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');

        if (savedToken && savedUser) {
            try {
                const user = JSON.parse(savedUser);
                setToken(savedToken);
                setCurrentUser(user);
                setIsAuthenticated(true);
            } catch (error) {
                // Invalid saved data, clear it
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        }
    }, []);

    const handleLogin = (newToken: string, user: User) => {
        setToken(newToken);
        setCurrentUser(user);
        setIsAuthenticated(true);
    };

    const handleLogout = () => {
        // Disconnect from any active channels
        if (morseChatRef.current) {
            morseChatRef.current.disconnect();
        }

        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setToken(null);
        setCurrentUser(null);
        setIsAuthenticated(false);
        setJoinChannelId(null);
        setInvitedFriend(null);
        setCurrentChannelId(null);
    };

    const handleInviteFriend = (friendId: string) => {
        // In a real implementation, you would fetch the friend's data
        // For now, we'll simulate this
        console.log(`Inviting friend ${friendId} to channel`);

        // This would typically involve sending an invitation through the API
        // and the friend would receive it via WebSocket or polling

        // For demo purposes, we'll just log it
        // The invitation system would need to be implemented with proper backend support
    };

    const handleJoinChannel = async (channelId: string) => {
        console.log(`Request to join channel: ${channelId}`);

        // Clear any pending friend invitations when joining a channel
        setInvitedFriend(null);

        // Set the join channel ID which will trigger the chat component to connect
        setJoinChannelId(channelId);

        // Use the ref to directly trigger the channel join in the chat component
        if (morseChatRef.current) {
            try {
                await morseChatRef.current.joinChannel(channelId);
                console.log(`Successfully requested join for channel: ${channelId}`);
            } catch (error) {
                console.error(`Failed to join channel ${channelId}:`, error);
            }
        }
    };

    const handleChannelConnectionChange = (isConnected: boolean, channelId?: string) => {
        console.log(`Channel connection changed: ${isConnected}, channelId: ${channelId}`);

        if (isConnected && channelId) {
            setCurrentChannelId(channelId);
            // Clear join request once successfully connected
            setJoinChannelId(null);
        } else {
            setCurrentChannelId(null);
        }
    };

    const handleSwitchToRegister = () => {
        setShowRegister(true);
    };

    const handleSwitchToLogin = () => {
        setShowRegister(false);
    };

    const handleRegisterSuccess = () => {
        // Registration successful, will redirect to login
    };

    // Show authentication screens
    if (!isAuthenticated) {
        if (showRegister) {
            return (
                <RegisterPage
                    onRegister={handleRegisterSuccess}
                    onSwitchToLogin={handleSwitchToLogin}
                />
            );
        } else {
            return (
                <LoginPage
                    onLogin={handleLogin}
                    onSwitchToRegister={handleSwitchToRegister}
                />
            );
        }
    }

    // Show main application
    return (
        <div className="text-center bg-[#393E46] min-h-screen flex flex-col">
            <header className="bg-[#222831] p-4 text-[#DFD0B8] shadow-lg sticky top-0 z-50">
                <div className="flex justify-between items-center w-full">
                    <Header />
                    <div className="flex items-center space-x-4">
                        <span className="text-sm text-[#A29787]">
                            Welcome, {currentUser?.callsign}
                        </span>
                        {currentChannelId && (
                            <span className="text-xs bg-[#908573] px-2 py-1 rounded text-white">
                                Channel: {currentChannelId}
                            </span>
                        )}
                        <button
                            onClick={handleLogout}
                            className="bg-[#908573] hover:bg-[#A29787] text-white px-3 py-1 rounded text-sm transition-colors"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            <div className="flex-1 flex w-full h-full overflow-hidden">
                {/* Friends Sidebar - Left */}
                <div className="flex-none w-80">
                    {token && currentUser && (
                        <FriendsSidebar
                            token={token}
                            currentUser={currentUser}
                            onInviteFriend={handleInviteFriend}
                            onJoinChannel={handleJoinChannel}
                        />
                    )}
                </div>

                {/* Main Chat - Center (larger) */}
                <div className="flex-1 flex justify-center items-center min-w-0">
                    {token && currentUser && (
                        <EnhancedMorseChat
                            ref={morseChatRef}
                            token={token}
                            currentUser={currentUser}
                            invitedFriend={invitedFriend}
                            joinChannelId={joinChannelId}
                            onChannelConnectionChange={handleChannelConnectionChange}
                        />
                    )}
                </div>

                {/* Learn Component - Right */}
                <div className="bg-[#222831] flex-none w-96 flex justify-center items-center p-4">
                    <Learn />
                </div>
            </div>
        </div>
    );
}

export default App;