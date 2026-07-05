// ============================================================
// src/pages/Login.jsx
// Page de connexion — Style industriel PURECONTROL
// ============================================================

import { useState } from 'react';
import { Shield, Eye, EyeOff, Loader } from 'lucide-react';
import { authService } from '../services/api';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await authService.login(email, password);
      onLogin(user);
    } catch {
      setError('Email ou mot de passe incorrect.');
    } finally {
      setLoading(false);
    }
  };

  // Comptes de test rapide (doc section 2.2)
  const quickFill = (em, pw) => { setEmail(em); setPassword(pw); };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      {/* Grille de fond */}
      <div className="absolute inset-0 opacity-5 bg-[linear-gradient(to_right,#334155_1px,transparent_1px),linear-gradient(to_bottom,#334155_1px,transparent_1px)] bg-[size:32px_32px]" />

      <div className="relative w-full max-w-md">
        {/* Logo / titre */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 mb-4">
            <Shield className="text-emerald-400" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide">PURECONTROL</h1>
          <p className="text-slate-400 text-sm mt-1">Système de détection de fuites IoT</p>
          <p className="text-slate-600 text-xs mt-1 font-mono">IUT Fotso Victor Bandjoun — L3 QSIR</p>
        </div>

        {/* Formulaire */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 shadow-2xl">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-5">
            Connexion Sécurisée
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="operateur@iut-bandjoun.cm"
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition font-mono"
              />
            </div>

            <div className="relative">
              <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">Mot de passe</label>
              <input
                type={showPwd ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 pr-10 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition font-mono"
              />
              <button type="button" onClick={() => setShowPwd(!showPwd)}
                className="absolute right-3 top-8 text-slate-500 hover:text-slate-300">
                {showPwd ? <EyeOff size={16}/> : <Eye size={16}/>}
              </button>
            </div>

            {error && (
              <div className="bg-rose-950/30 border border-rose-800/50 rounded-lg px-3 py-2 text-xs text-rose-400">
                {error}
              </div>
            )}

            <button type="submit" disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition flex items-center justify-center gap-2">
              {loading ? <><Loader size={15} className="animate-spin"/> Connexion...</> : 'Se connecter'}
            </button>
          </form>

          {/* Comptes de test */}
          <div className="mt-5 pt-4 border-t border-slate-800">
            <p className="text-xs text-slate-600 uppercase tracking-wider mb-2">Comptes de test</p>
            <div className="space-y-1">
              {[
                { label: 'Admin', email: 'admin@iut-bandjoun.cm', pw: 'admin123', color: 'text-rose-400' },
                { label: 'Responsable', email: 'securite@iut-bandjoun.cm', pw: 'resp123', color: 'text-amber-400' },
                { label: 'Opérateur', email: 'operateur@iut-bandjoun.cm', pw: 'oper123', color: 'text-emerald-400' },
              ].map(acc => (
                <button key={acc.label} onClick={() => quickFill(acc.email, acc.pw)}
                  className="w-full text-left bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded px-3 py-1.5 text-xs flex flex-col gap-0.5 sm:flex-row sm:justify-between sm:items-center transition">
                  <span className={`font-semibold ${acc.color}`}>{acc.label}</span>
                  <span className="text-slate-500 font-mono break-all">{acc.email}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
