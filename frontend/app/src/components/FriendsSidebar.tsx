// src/components/FriendsSidebar.tsx
import React, { useState, useEffect } from 'react';
import { channelService } from '../services/channelService';

interface User {
    id: string;
    callsign: string;
    status: 'online' | 'offline' | 'waiting' | 'busy';
    created_at: string;
}

interface Channel {
    channel_id: string;
    users: User[];
    is_full: boolean;
    created_at: string;
}

interface FriendsSidebarProps {
    token: string;
    currentUser: User;
    onInviteFriend: (friendId: string) => void;
    onJoinChannel?: (channelId: string) => void;
}

export default function FriendsSidebar({ token, currentUser, onJoinChannel }: FriendsSidebarProps) {
    const [friends, setFriends] = useState<User[]>([]);
    const [showAddFriend, setShowAddFriend] = useState(false);
    const [newFriendCallsign, setNewFriendCallsign] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const [channels, setChannels] = useState<Channel[]>([]);
    const [joinChannelId, setJoinChannelId] = useState('');
    const [showJoinChannel, setShowJoinChannel] = useState(false);
    const [joiningChannelId, setJoiningChannelId] = useState<string | null>(null);

    // Fetch friends list using backend API
    const fetchFriends = async () => {
        try {
            const response = await fetch('http://localhost:8000/follow/', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (response.ok) {
                const friendsData = await response.json();
                setFriends(friendsData);
            }
        } catch (err) {
            console.error('Failed to fetch friends:', err);
        }
    };

    // Fetch active channels using the service
    const fetchChannels = async () => {
        try {
            const channelsData = await channelService.getChannels(token);
            setChannels(channelsData);
        } catch (err) {
            console.error('Failed to fetch channels:', err);
        }
    };

    useEffect(() => {
        fetchFriends();
        fetchChannels();
        // Poll for updates every 10 seconds
        const interval = setInterval(() => {
            fetchFriends();
            fetchChannels();
        }, 10000);
        return () => clearInterval(interval);
    }, [token]);

    const handleAddFriend = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        setMessage('');

        try {
            // First, find user by callsign using backend API
            const userResponse = await fetch(`http://localhost:8000/users/callsign/${newFriendCallsign}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!userResponse.ok) {
                throw new Error('User not found');
            }

            const userData = await userResponse.json();

            // Then follow the user using backend API
            const followResponse = await fetch(`http://localhost:8000/follow/${userData.id}/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (followResponse.ok) {
                setMessage(`Successfully added ${newFriendCallsign} as friend!`);
                setNewFriendCallsign('');
                setShowAddFriend(false);
                fetchFriends(); // Refresh friends list
            } else if (followResponse.status === 304) {
                setMessage(`You're already friends with ${newFriendCallsign}`);
            } else {
                throw new Error('Failed to add friend');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to add friend');
        } finally {
            setIsLoading(false);
        }
    };

    const handleRemoveFriend = async (friendId: string, friendCallsign: string) => {
        try {
            const response = await fetch(`http://localhost:8000/follow/${friendId}/`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (response.ok) {
                setMessage(`Removed ${friendCallsign} from friends`);
                fetchFriends(); // Refresh friends list
            }
        } catch (err) {
            setError('Failed to remove friend');
        }
    };

    const handleJoinChannelById = async () => {
        if (!joinChannelId || !channelService.isValidChannelId(joinChannelId)) {
            setError('Please enter a valid 6-digit channel ID');
            return;
        }

        setJoiningChannelId(joinChannelId);
        setError('');
        setMessage('');

        try {
            // Validate the channel first
            const result = await channelService.joinChannel(token, joinChannelId);

            if (result.success) {
                setMessage('Channel validated - connecting...');
                setJoinChannelId('');
                setShowJoinChannel(false);

                // Call the parent callback to trigger the chat component
                if (onJoinChannel) {
                    onJoinChannel(joinChannelId);
                }

                // Refresh data after a short delay
                setTimeout(() => {
                    fetchChannels();
                    fetchFriends();
                }, 1000);
            } else {
                setError(result.message);
            }
        } catch (err) {
            setError('Failed to validate channel');
        } finally {
            setJoiningChannelId(null);
        }
    };

    const handleJoinFriendChannel = async (friendId: string, friendCallsign: string, channelId: string) => {
        setJoiningChannelId(channelId);
        setError('');
        setMessage('');

        try {
            // First check if we can join the friend's channel
            const friendChannelCheck = await channelService.getFriendJoinableChannel(token, friendId);

            if (!friendChannelCheck.canJoin) {
                setError(friendChannelCheck.reason || `Cannot join ${friendCallsign}'s channel`);
                return;
            }

            // Validate the channel
            const result = await channelService.joinChannel(token, channelId);

            if (result.success) {
                setMessage(`Connecting to ${friendCallsign}'s channel...`);

                // Call the parent callback to trigger the chat component
                if (onJoinChannel) {
                    onJoinChannel(channelId);
                }

                // Refresh data after a short delay
                setTimeout(() => {
                    fetchChannels();
                    fetchFriends();
                }, 1000);
            } else {
                setError(result.message);
            }
        } catch (err) {
            setError(`Failed to join ${friendCallsign}'s channel`);
        } finally {
            setJoiningChannelId(null);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'online': return 'bg-green-500';
            case 'waiting': return 'bg-yellow-500';
            case 'busy': return 'bg-red-500';
            default: return 'bg-gray-500';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'online': return '🟢';
            case 'waiting': return '🟡';
            case 'busy': return '🔴';
            default: return '⚫';
        }
    };

    const getFriendChannel = (friendId: string): Channel | null => {
        return channels.find(channel =>
            channel.users.some(user => user.id === friendId)
        ) || null;
    };

    const canJoinFriendChannel = (friendChannel: Channel | null): boolean => {
        if (!friendChannel) return false;
        if (friendChannel.is_full) return false;
        if (friendChannel.users.length >= 2) return false;

        // Check if current user is already in the channel
        const isAlreadyInChannel = friendChannel.users.some(user => user.id === currentUser.id);
        return !isAlreadyInChannel;
    };

    // Clear messages after 5 seconds
    useEffect(() => {
        if (message || error) {
            const timer = setTimeout(() => {
                setMessage('');
                setError('');
            }, 5000);
            return () => clearTimeout(timer);
        }
    }, [message, error]);

    return (
        <div className="bg-[#222831] h-full w-full border-r border-[#393E46] flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-[#393E46]">
                <h2 className="text-xl font-bold text-[#DFD0B8] mb-2">Friends</h2>
                <div className="text-sm text-[#A29787]">
                    {currentUser.callsign} • {friends.length} friends
                </div>
            </div>

            {/* Join Channel Input */}
            <div className="p-4 border-b border-[#393E46]">
                {!showJoinChannel && !showAddFriend ? (
                    <div className="space-y-2">
                        <button
                            onClick={() => setShowAddFriend(true)}
                            className="w-full bg-[#908573] hover:bg-[#A29787] text-white py-2 px-4 rounded-md transition-colors text-sm"
                        >
                            + Add Friend
                        </button>
                        <button
                            onClick={() => setShowJoinChannel(true)}
                            className="w-full bg-[#6A5F4F] hover:bg-[#7A6F5F] text-white py-2 px-4 rounded-md transition-colors text-sm"
                        >
                            Join Channel by ID
                        </button>
                    </div>
                ) : showAddFriend ? (
                    <form onSubmit={handleAddFriend} className="space-y-2">
                        <input
                            type="text"
                            value={newFriendCallsign}
                            onChange={(e) => setNewFriendCallsign(e.target.value)}
                            placeholder="Enter callsign"
                            className="w-full px-3 py-2 bg-[#393E46] border border-[#A29787] rounded-md text-[#E4D6BD] text-sm focus:outline-none focus:ring-2 focus:ring-[#908573]"
                            required
                            minLength={3}
                        />
                        <div className="flex gap-2">
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="flex-1 bg-[#908573] hover:bg-[#A29787] text-white py-1 px-3 rounded-md transition-colors text-sm disabled:opacity-50"
                            >
                                {isLoading ? 'Adding...' : 'Add'}
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setShowAddFriend(false);
                                    setNewFriendCallsign('');
                                    setError('');
                                }}
                                className="flex-1 bg-[#393E46] hover:bg-[#4A5059] text-[#E4D6BD] py-1 px-3 rounded-md transition-colors text-sm"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                ) : (
                    <div className="space-y-2">
                        <input
                            type="text"
                            value={joinChannelId}
                            onChange={(e) => setJoinChannelId(e.target.value)}
                            placeholder="Enter 6-digit channel ID"
                            className="w-full px-3 py-2 bg-[#393E46] border border-[#A29787] rounded-md text-[#E4D6BD] text-sm focus:outline-none focus:ring-2 focus:ring-[#908573]"
                            maxLength={6}
                        />
                        <div className="flex gap-2">
                            <button
                                onClick={handleJoinChannelById}
                                disabled={!channelService.isValidChannelId(joinChannelId) || joiningChannelId === joinChannelId}
                                className="flex-1 bg-[#908573] hover:bg-[#A29787] text-white py-1 px-3 rounded-md transition-colors text-sm disabled:opacity-50"
                            >
                                {joiningChannelId === joinChannelId ? 'Joining...' : 'Join'}
                            </button>
                            <button
                                onClick={() => {
                                    setShowJoinChannel(false);
                                    setJoinChannelId('');
                                }}
                                className="flex-1 bg-[#393E46] hover:bg-[#4A5059] text-[#E4D6BD] py-1 px-3 rounded-md transition-colors text-sm"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Messages */}
            {(error || message) && (
                <div className="p-4">
                    {error && <div className="text-red-400 text-sm mb-2">{error}</div>}
                    {message && <div className="text-green-400 text-sm mb-2">{message}</div>}
                </div>
            )}

            {/* Friends List */}
            <div className="flex-1 overflow-y-auto">
                {friends.length === 0 ? (
                    <div className="p-4 text-center text-[#A29787]">
                        <div className="mb-2">📡</div>
                        <div className="text-sm">No friends yet</div>
                        <div className="text-xs">Add friends to start chatting!</div>
                    </div>
                ) : (
                    <div className="space-y-1 p-2">
                        {friends.map((friend) => {
                            const friendChannel = getFriendChannel(friend.id);
                            const isInChannel = friendChannel !== null;
                            const canJoin = canJoinFriendChannel(friendChannel);

                            return (
                                <div
                                    key={friend.id}
                                    className="bg-[#393E46] hover:bg-[#4A5059] rounded-lg p-3 transition-colors group"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center space-x-3">
                                            <div className="relative">
                                                <div className="w-8 h-8 bg-[#908573] rounded-full flex items-center justify-center text-white text-sm font-bold">
                                                    {friend.callsign.charAt(0).toUpperCase()}
                                                </div>
                                                <div
                                                    className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-[#393E46] ${getStatusColor(friend.status)}`}
                                                    title={friend.status}
                                                ></div>
                                            </div>
                                            <div>
                                                <div className="text-[#E4D6BD] font-medium text-sm flex items-center gap-2">
                                                    {friend.callsign}
                                                    {isInChannel && (
                                                        <span className="text-xs bg-[#222831] px-2 py-0.5 rounded-full text-[#A29787]">
                                                            Ch: {friendChannel.channel_id}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="text-[#A29787] text-xs capitalize">
                                                    {getStatusIcon(friend.status)} {friend.status}
                                                    {isInChannel && (
                                                        <span className="ml-1">
                                                            ({friendChannel.users.length}/2)
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            {canJoin && (
                                                <button
                                                    onClick={() => handleJoinFriendChannel(friend.id, friend.callsign, friendChannel!.channel_id)}
                                                    disabled={joiningChannelId === friendChannel!.channel_id}
                                                    className="bg-green-600 hover:bg-green-700 text-white p-1 rounded text-xs px-2 disabled:opacity-50"
                                                    title="Join channel"
                                                >
                                                    {joiningChannelId === friendChannel!.channel_id ? '...' : 'Join'}
                                                </button>
                                            )}
                                            <button
                                                onClick={() => handleRemoveFriend(friend.id, friend.callsign)}
                                                className="bg-red-600 hover:bg-red-700 text-white p-1 rounded text-xs"
                                                title="Remove friend"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Status Legend */}
            <div className="p-4 border-t border-[#393E46]">
                <div className="text-xs text-[#A29787] space-y-1">
                    <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>Online</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                        <span>Waiting for partner</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                        <span>In channel</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                        <span>Offline</span>
                    </div>
                </div>
            </div>
        </div>
    );
}