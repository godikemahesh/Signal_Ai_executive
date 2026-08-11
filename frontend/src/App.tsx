import React, { useEffect, useState } from 'react';
import { LandingPage } from './components/LandingPage';
import { AuthScreen } from './components/AuthScreen';
import { AppShell } from './components/AppShell';
import { api } from './lib/api';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<'landing' | 'auth' | 'dashboard'>('landing');
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [userProfile, setUserProfile] = useState<any>(null);

  useEffect(() => {
    // 1. Check for token in URL query params (from Google OAuth callback)
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get('token');

    if (urlToken) {
      localStorage.setItem('signal_token', urlToken);
      // Clean query params from URL without page reload
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    // 2. Validate session token if present
    const existingToken = localStorage.getItem('signal_token');
    if (existingToken) {
      api.getMe()
        .then((user) => {
          setUserProfile(user);
          setCurrentScreen('dashboard');
        })
        .catch(() => {
          localStorage.removeItem('signal_token');
          setCurrentScreen('landing');
        })
        .finally(() => {
          setIsLoadingSession(false);
        });
    } else {
      setIsLoadingSession(false);
    }

    // 3. Listen for unauthorized API events
    const handleUnauthorized = () => {
      setUserProfile(null);
      setCurrentScreen('landing');
    };

    window.addEventListener('signal-unauthorized', handleUnauthorized);
    return () => window.removeEventListener('signal-unauthorized', handleUnauthorized);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('signal_token');
    setUserProfile(null);
    setCurrentScreen('landing');
  };

  if (isLoadingSession) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center gap-3 font-sans">
        <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        <p className="text-sm text-slate-400 font-medium">Initializing Signal Assistant...</p>
      </div>
    );
  }

  if (currentScreen === 'landing') {
    return (
      <LandingPage
        onGetStarted={() => setCurrentScreen('auth')}
        onSignIn={() => setCurrentScreen('auth')}
      />
    );
  }

  if (currentScreen === 'auth') {
    return (
      <AuthScreen
        onLogin={() => setCurrentScreen('dashboard')}
      />
    );
  }

  return (
    <AppShell
      userProfile={userProfile}
      onLogout={handleLogout}
    />
  );
}


