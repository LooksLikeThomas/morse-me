import React, { useRef } from 'react';

export default function LoginPage() {
    const callsignRef = useRef<HTMLInputElement>(null);
    const passwordRef = useRef<HTMLInputElement>(null);

    const loginUser = (callsign: string, password: string) => {
        // TODO: implement login logic with callsign & password
        console.log('Login:', { callsign, password });
    };

    const registerUser = (callsign: string, password: string) => {
        // TODO: implement registration logic with callsign & password
        console.log('Register:', { callsign, password });
    };

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const form = e.currentTarget;
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const callsign = callsignRef.current?.value || '';
        const password = passwordRef.current?.value || '';
        const action = (e.nativeEvent as any).submitter.name;

        if (action === 'login') {
            loginUser(callsign, password);
        } else if (action === 'register') {
            registerUser(callsign, password);
        }
    };

    return (
        <div className="bg-[#393E46] min-h-screen flex items-center justify-center p-8">
            <div className="bg-[#2F343D] rounded-2xl shadow-lg p-10 w-full max-w-md">
                <h2 className="text-2xl font-bold mb-6 text-center text-[#E4D6BD]">Morse Login</h2>

                <form className="space-y-6" onSubmit={handleSubmit} noValidate>
                    <div>
                        <label htmlFor="callsign" className="block text-sm text-[#E4D6BD] mb-1">
                            Callsign
                        </label>
                        <input
                            id="callsign"
                            name="callsign"
                            type="text"
                            ref={callsignRef}
                            required
                            className="w-full rounded-lg bg-[#393E46] border border-[#A29787] text-[#E4D6BD] placeholder-[#B0A89B] focus:outline-none focus:ring-2 focus:ring-[#A29787] p-3"
                            placeholder="N0CALL"
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm text-[#E4D6BD] mb-1">
                            Password
                        </label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            ref={passwordRef}
                            required
                            minLength={8}
                            className="w-full rounded-lg bg-[#393E46] border border-[#A29787] text-[#E4D6BD] placeholder-[#B0A89B] focus:outline-none focus:ring-2 focus:ring-[#A29787] p-3"
                            placeholder="••••••••"
                        />
                        <p className="mt-1 text-xs text-[#B0A89B]">Password must be at least 8 characters.</p>
                    </div>

                    <div className="flex justify-between">
                        <button
                            type="submit"
                            name="register"
                            className="bg-[#A29787] hover:bg-[#B0A89B] text-[#393E46] font-semibold px-6 py-2 rounded-lg transition-colors flex-1 mr-2"
                        >
                            Register
                        </button>
                        <button
                            type="submit"
                            name="login"
                            className="bg-[#E4D6BD] hover:bg-[#F0E8D8] text-[#393E46] font-semibold px-6 py-2 rounded-lg transition-colors flex-1 ml-2"
                        >
                            Login
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}