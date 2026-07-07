import { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { Shield, Eye, EyeOff, Loader } from 'lucide-react';
import { authService } from '../services/api';

export default function Login({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
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

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    if (password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caracteres.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Les deux mots de passe ne correspondent pas.');
      return;
    }

    setLoading(true);
    try {
      const user = await authService.register(name, email, password);
      onLogin(user);
    } catch (e) {
      setError(e.response?.data?.detail || 'Inscription impossible.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    if (!credentialResponse.credential) {
      setError('Verification Google impossible.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const user = await authService.registerWithGoogle(credentialResponse.credential);
      onLogin(user);
    } catch (e) {
      setError(e.response?.data?.detail || 'Inscription Google impossible.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="absolute inset-0 opacity-5 bg-[linear-gradient(to_right,#334155_1px,transparent_1px),linear-gradient(to_bottom,#334155_1px,transparent_1px)] bg-[size:32px_32px]" />

      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 mb-4">
            <Shield className="text-emerald-400" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide">PURECONTROL</h1>
          <p className="text-slate-400 text-sm mt-1">Systeme de detection de fuites IoT</p>
          <p className="text-slate-600 text-xs mt-1 font-mono">IUT Fotso Victor Bandjoun - L3 QSIR</p>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 shadow-2xl">
          <div className="grid grid-cols-2 gap-1 bg-slate-900 border border-slate-800 rounded-lg p-1 mb-5">
            {[
              { id: 'login', label: 'Connexion' },
              { id: 'register', label: 'Inscription' },
            ].map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  setMode(item.id);
                  setError('');
                }}
                className={`rounded-md py-2 text-xs font-semibold transition ${
                  mode === item.id
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-500 hover:text-slate-200'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-5">
            {mode === 'login' ? 'Connexion securisee' : 'Creation de compte'}
          </h2>

          {mode === 'login' && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
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
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="********"
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 pr-10 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(!showPwd)}
                  className="absolute right-3 top-8 text-slate-500 hover:text-slate-300"
                >
                  {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {error && (
                <div className="bg-rose-950/30 border border-rose-800/50 rounded-lg px-3 py-2 text-xs text-rose-400">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader size={15} className="animate-spin" /> Connexion...
                  </>
                ) : (
                  'Se connecter'
                )}
              </button>
            </form>
          )}

          {mode === 'register' && (
            <div className="space-y-4">
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">Nom complet</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Operateur PURECONTROL"
                    required
                    minLength={2}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
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
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="6 caracteres minimum"
                    required
                    minLength={6}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 pr-10 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd(!showPwd)}
                    className="absolute right-3 top-8 text-slate-500 hover:text-slate-300"
                  >
                    {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>

                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">Confirmer le mot de passe</label>
                  <input
                    type={showPwd ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeter le mot de passe"
                    required
                    minLength={6}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition font-mono"
                  />
                </div>

                {error && (
                  <div className="bg-rose-950/30 border border-rose-800/50 rounded-lg px-3 py-2 text-xs text-rose-400">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader size={15} className="animate-spin" /> Creation...
                    </>
                  ) : (
                    'Creer mon compte'
                  )}
                </button>
              </form>

              <div className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-3">
                <p className="text-xs text-slate-400 leading-relaxed">
                  Google reste disponible si le navigateur de l'appareil le prend en charge.
                </p>
              </div>

              <div className="flex justify-center">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={() => setError('Connexion Google annulee ou impossible.')}
                  theme="filled_black"
                  text="signup_with"
                  shape="rectangular"
                  width="320"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
