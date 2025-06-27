// src/components/RegisterPage.tsx
import React, { useState } from 'react';

interface RegisterPageProps {
    onRegister: () => void;
    onSwitchToLogin: () => void;
}

export default function RegisterPage({ onRegister, onSwitchToLogin }: RegisterPageProps) {
    const [callsign, setCallsign] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            setIsLoading(false);
            return;
        }

        try {
            const response = await fetch('http://localhost:8000/users/', {
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
                throw new Error(errorData.detail || 'Registration failed');
            }

            setSuccess(true);
            setTimeout(() => {
                onRegister();
                onSwitchToLogin();
            }, 2000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    if (success) {
        return (
            <div className="bg-[#393E46] text-[#E4D6BD] min-h-screen flex flex-col items-center justify-center p-8">
                <div className="bg-[#222831] rounded-lg p-8 shadow-lg max-w-md w-full text-center">
                    <div className="text-green-400 text-5xl mb-4">✓</div>
                    <h2 className="text-2xl font-bold mb-4">Registration Successful!</h2>
                    <p className="text-[#A29787]">Redirecting to login...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-[#393E46] text-[#E4D6BD] min-h-screen flex flex-col items-center justify-center p-8">
            <div className="bg-[#222831] rounded-lg p-8 shadow-lg max-w-md w-full">
                <h1 className="text-3xl font-bold text-center mb-8 text-[#DFD0B8]">
                    Join Morse-Me
                </h1>

                <form onSubmit={handleRegister} className="space-y-6">
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
                            placeholder="Choose your callsign (min. 3 characters)"
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
                            placeholder="Choose a password (min. 8 characters)"
                            required
                            minLength={8}
                        />
                    </div>

                    <div>
                        <label htmlFor="confirmPassword" className="block text-sm font-medium mb-2">
                            Confirm Password
                        </label>
                        <input
                            type="password"
                            id="confirmPassword"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="w-full px-3 py-2 bg-[#393E46] border border-[#A29787] rounded-md text-[#E4D6BD] focus:outline-none focus:ring-2 focus:ring-[#908573] focus:border-transparent"
                            placeholder="Confirm your password"
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
                        {isLoading ? 'Creating Account...' : 'Register'}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <p className="text-sm text-[#A29787]">
                        Already have an account?{' '}
                        <button
                            onClick={onSwitchToLogin}
                            className="text-[#908573] hover:text-[#A29787] underline"
                        >
                            Login here
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
}