// ============================================================
// src/App.jsx
// Point d'entrée — Routage Login ↔ Dashboard
// ============================================================

import { useState, useEffect } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import { authService } from './services/api';

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    // Restaurer la session si token déjà en localStorage
    if (authService.isLoggedIn()) {
      const u = authService.getUser();
      if (u) setUser(u);
    }
    setChecking(false);
  }, []);

  if (checking) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return user
    ? <Dashboard user={user} />
    : <Login onLogin={setUser} />;
}
