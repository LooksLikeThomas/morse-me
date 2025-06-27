// src/components/LoginPage.tsx
import React, { useState } from 'react';

interface LoginPageProps {
    onLogin: (token: string, user: any) => void;
    onSwitchToRegister: () => void;
}

export default function LoginPage({ onLogin, onSwitchToRegister }: LoginPageProps) {
    const [callsign, setCallsign] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const response = await fetch('http://localhost:8000/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    callsign,
                    password,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed');
            }

            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            onLogin(data.access_token, data.user);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-[#393E46] text-[#E4D6BD] min-h-screen flex flex-col items-center justify-center p-8">
            <div className="bg-[#222831] rounded-lg p-8 shadow-lg max-w-md w-full">
                <h1 className="text-3xl font-bold text-center mb-8 text-[#DFD0B8]">
                    Morse-Me Login
                </h1>

                <form onSubmit={handleLogin} className="space-y-6">
                    <div>
                        <label htmlFor="callsign" className="block text-sm font-medium mb-2">
                            Callsign
                        </label>
                        <input
                            type="text"
                            id="callsign"
                            value={callsign}
                            onChange={(e) => setCallsign(e.target.value)}
                            className="w-full px-3 py-2 bg-[#393E46] border border-[#A29787] rounded-md text-[#E4D6BD] focus:outline-none focus:ring-2 focus:ring-[#908573] focus:border-transparent"
                            placeholder="Enter your callsign"
                            required
                            minLength={3}
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm font-medium mb-2">
                            Password
                        </label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-3 py-2 bg-[#393E46] border border-[#A29787] rounded-md text-[#E4D6BD] focus:outline-none focus:ring-2 focus:ring-[#908573] focus:border-transparent"
                            placeholder="Enter your password"
                            required
                            minLength={8}
                        />
                    </div>

                    {error && (
                        <div className="text-red-400 text-sm text-center">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-[#908573] hover:bg-[#A29787] text-white py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? 'Logging in...' : 'Login'}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <p className="text-sm text-[#A29787]">
                        Don't have an account?{' '}
                        <button
                            onClick={onSwitchToRegister}
                            className="text-[#908573] hover:text-[#A29787] underline"
                        >
                            Register here
                        </button>
                    </p>
                </div>

                <div className="mt-8 text-center">
                    <div className="text-xs text-[#A29787] font-mono">
                        -.-- --- ..- / -.-. .- -. / -.. --- / .. -
                    </div>
                    <div className="text-xs text-[#A29787] mt-1">
                        "YOU CAN DO IT" in Morse Code
                    </div>
                </div>
            </div>
        </div>
    );
}