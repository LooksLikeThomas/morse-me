// src/services/channelService.ts

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

interface ChannelJoinResponse {
    success: boolean;
    message: string;
    channel?: Channel;
}

interface ConnectionCallbacks {
    onOpen?: (channelId: string) => void;
    onMessage?: (data: any) => void;
    onClose?: (event: CloseEvent) => void;
    onError?: (error: Event) => void;
    onUserJoined?: (user: User, channelId: string) => void;
    onUserLeft?: (user: User) => void;
    onMorseSignal?: (signal: string) => void;
}

class ChannelService {
    private baseUrl: string;
    private wsUrl: string;
    private currentWebSocket: WebSocket | null = null;
    private currentChannelId: string | null = null;

    constructor(baseUrl: string = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.wsUrl = baseUrl.replace('http', 'ws');
    }

    /**
     * Get list of active channels from backend
     */
    async getChannels(token: string): Promise<Channel[]> {
        try {
            const response = await fetch(`${this.baseUrl}/channel/list`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (response.ok) {
                const data = await response.json();
                return data.channels || [];
            }
            return [];
        } catch (err) {
            console.error('Failed to fetch channels:', err);
            return [];
        }
    }

    /**
     * Check if a channel is joinable by connecting to WebSocket
     */
    async canJoinChannel(token: string, channelId: string): Promise<{
        canJoin: boolean;
        reason?: string;
        channel?: Channel;
    }> {
        try {
            const channels = await this.getChannels(token);
            const channel = channels.find(ch => ch.channel_id === channelId);

            if (!channel) {
                return {
                    canJoin: true,
                    reason: 'Channel will be created'
                };
            }

            if (channel.is_full) {
                return {
                    canJoin: false,
                    reason: 'Channel is full',
                    channel
                };
            }

            if (channel.users.length >= 2) {
                return {
                    canJoin: false,
                    reason: 'Channel has reached maximum capacity',
                    channel
                };
            }

            return {
                canJoin: true,
                channel
            };
        } catch (err) {
            console.error('Error checking channel joinability:', err);
            return {
                canJoin: false,
                reason: 'Error checking channel status'
            };
        }
    }

    /**
     * Connect to WebSocket channel - this is the main connection function
     */
    async connectToChannel(
        channelType: 'random' | 'specific' | 'create',
        token: string,
        currentUser: User,
        callbacks: ConnectionCallbacks,
        specificChannelId?: string
    ): Promise<{
        success: boolean;
        message: string;
        channelId?: string;
    }> {
        // Close existing connection
        if (this.currentWebSocket) {
            this.currentWebSocket.close();
            this.currentWebSocket = null;
        }


        try {
            let wsUrl: string;
            let targetChannelId: string;

            if (channelType === 'create') {
                // Generate a new channel ID and connect to it
                targetChannelId = Math.floor(100000 + Math.random() * 900000).toString();
                wsUrl = `${this.wsUrl}/channel/${targetChannelId}?token=${token}`;
            } else if (channelType === 'specific' && specificChannelId) {
                // Connect to specific channel
                targetChannelId = specificChannelId;
                wsUrl = `${this.wsUrl}/channel/${targetChannelId}?token=${token}`;
            } else {
                // Connect to random channel
                wsUrl = `${this.wsUrl}/channel/random?token=${token}`;
                targetChannelId = 'random';
            }

            console.log(`Connecting to WebSocket: ${wsUrl}`);
            const ws = new WebSocket(wsUrl);
            this.currentWebSocket = ws;
            this.currentChannelId = targetChannelId !== 'random' ? targetChannelId : null;

            // Set up event handlers
            ws.onopen = () => {
                console.log(`WebSocket connected to channel: ${targetChannelId}`);
                if (callbacks.onOpen) {
                    callbacks.onOpen(this.currentChannelId || targetChannelId);
                }
            };

            ws.onmessage = (event) => {
                console.log('WebSocket message received:', event.data);

                if (callbacks.onMessage) {
                    callbacks.onMessage(event.data);
                }

                try {
                    const data = JSON.parse(event.data);

                    if (data.event === 'user_joined') {
                        console.log('User joined event:', data);

                        // Update channel ID if provided (for random channels)
                        if (data.channel_id && data.channel_id !== targetChannelId) {
                            this.currentChannelId = data.channel_id;
                        }

                        // If it's not the current user joining, it's the partner
                        if (data.user && data.user.id !== currentUser.id) {
                            if (callbacks.onUserJoined) {
                                callbacks.onUserJoined(data.user, data.channel_id || this.currentChannelId);
                            }
                        }
                    } else if (data.event === 'user_left') {
                        console.log('User left event:', data);
                        if (callbacks.onUserLeft) {
                            callbacks.onUserLeft(data.user);
                        }
                    } else if (data.type === 'morse') {
                        console.log('Morse signal received:', data.signal);
                        if (callbacks.onMorseSignal) {
                            callbacks.onMorseSignal(data.signal);
                        }
                    }
                } catch (e) {
                    // Handle plain text messages (legacy support)
                    console.log('Plain text message received:', event.data);
                    if (callbacks.onMorseSignal) {
                        callbacks.onMorseSignal(event.data);
                    }
                }
            };

            ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.currentWebSocket = null;
                this.currentChannelId = null;

                if (callbacks.onClose) {
                    callbacks.onClose(event);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                if (callbacks.onError) {
                    callbacks.onError(error);
                }
            };

            return {
                success: true,
                message: 'Connecting to channel...',
                channelId: this.currentChannelId || targetChannelId
            };

        } catch (err) {
            console.error('Error connecting to channel:', err);
            return {
                success: false,
                message: 'Failed to connect to channel'
            };
        }
    }

    /**
     * Send a morse signal through the current WebSocket connection
     */
    sendMorseSignal(signal: string): boolean {
        if (this.currentWebSocket && this.currentWebSocket.readyState === WebSocket.OPEN) {
            const message = JSON.stringify({
                type: 'morse',
                signal: signal
            });
            this.currentWebSocket.send(message);
            console.log('Sent morse signal:', signal);
            return true;
        }
        return false;
    }

    /**
     * Disconnect from current channel
     */
    disconnect(): void {
        if (this.currentWebSocket) {
            this.currentWebSocket.close();
            this.currentWebSocket = null;
            this.currentChannelId = null;
        }
    }

    /**
     * Join a channel by ID
     */
    async joinChannel(token: string, channelId: string): Promise<ChannelJoinResponse> {
        try {
            // Validate channel ID format (6 digits)
            if (!/^\d{6}$/.test(channelId)) {
                return {
                    success: false,
                    message: 'Channel ID must be a 6-digit number'
                };
            }

            // Check if we can join
            const joinCheck = await this.canJoinChannel(token, channelId);

            if (!joinCheck.canJoin) {
                return {
                    success: false,
                    message: joinCheck.reason || 'Cannot join channel'
                };
            }

            return {
                success: true,
                message: 'Channel validated - ready to connect',
                channel: joinCheck.channel
            };
        } catch (err) {
            console.error('Error joining channel:', err);
            return {
                success: false,
                message: 'Network error while validating channel'
            };
        }
    }

    /**
     * Find user's current channel from the channels list
     */
    async getUserChannel(token: string, userId: string): Promise<Channel | null> {
        try {
            const channels = await this.getChannels(token);
            return channels.find(channel =>
                channel.users.some(user => user.id === userId)
            ) || null;
        } catch (err) {
            console.error('Error finding user channel:', err);
            return null;
        }
    }

    /**
     * Get friend's channel if they have one and it's joinable
     */
    async getFriendJoinableChannel(token: string, friendId: string): Promise<{
        channel: Channel | null;
        canJoin: boolean;
        reason?: string;
    }> {
        try {
            const friendChannel = await this.getUserChannel(token, friendId);

            if (!friendChannel) {
                return {
                    channel: null,
                    canJoin: false,
                    reason: 'Friend is not in any channel'
                };
            }

            const joinCheck = await this.canJoinChannel(token, friendChannel.channel_id);

            return {
                channel: friendChannel,
                canJoin: joinCheck.canJoin,
                reason: joinCheck.reason
            };
        } catch (err) {
            console.error('Error checking friend channel:', err);
            return {
                channel: null,
                canJoin: false,
                reason: 'Error checking friend status'
            };
        }
    }

    /**
     * Generate a random 6-digit channel ID
     */
    generateChannelId(): string {
        return Math.floor(100000 + Math.random() * 900000).toString();
    }

    /**
     * Validate channel ID format
     */
    isValidChannelId(channelId: string): boolean {
        return /^\d{6}$/.test(channelId);
    }
}

// Export singleton instance
export const channelService = new ChannelService();