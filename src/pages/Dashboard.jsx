// ============================================================
// src/pages/Dashboard.jsx
// Dashboard principal — Style SiteKiosk / PURECONTROL
// Branché sur API réelle (Étudiant 2 — FastAPI)
// ============================================================

import { useState, useEffect, useCallback } from 'react';
import {
  Shield, Activity, Bell, MapPin, Droplets, Flame, Thermometer,
  CheckCircle2, AlertTriangle, XCircle, RefreshCw, LogOut,
  Settings, Users, BarChart2, Sliders, Volume2, VolumeX, Download,
  Wifi, Battery, Clock
} from 'lucide-react';
import { dashboardService, actionService, authService, WS_BASE_URL } from '../services/api';

// ---- Icône selon type de capteur (doc §3.2) ----
function SensorIcon({ type, size = 14, className = '' }) {
  const props = { size, className };
  if (type === 'GAZ_GPL' || type === 'GAZ_CO') return <Flame {...props} />;
  if (type === 'NIVEAU_CUVE' || type === 'LIQUIDE_SOL') return <Droplets {...props} />;
  if (type === 'TEMPERATURE') return <Thermometer {...props} />;
  return <Activity {...props} />;
}

// ---- Badge statut ----
function StatusBadge({ status }) {
  const map = {
    NORMAL:  { cls: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', label: 'Normal' },
    WARNING: { cls: 'bg-amber-500/10 text-amber-400 border-amber-500/30',   label: 'Warning' },
    DANGER:  { cls: 'bg-rose-500/10 text-rose-400 border-rose-800/40 animate-pulse', label: 'Danger' },
    ACTIF:   { cls: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', label: 'Actif' },
    INACTIF: { cls: 'bg-slate-700/50 text-slate-400 border-slate-700', label: 'Inactif' },
  };
  const s = map[status] || map['NORMAL'];
  return (
    <span className={`px-2 py-0.5 rounded border text-[10px] font-semibold font-mono ${s.cls}`}>
      {s.label}
    </span>
  );
}

// ---- Donut SVG ----
function DonutChart({ value, total, color = '#10b981' }) {
  const R = 28, C = 2 * Math.PI * R;
  const pct = total > 0 ? value / total : 0;
  const dash = pct * C;
  return (
    <svg width="70" height="70" viewBox="0 0 70 70">
      <circle cx="35" cy="35" r={R} fill="none" stroke="#1e293b" strokeWidth="8"/>
      <circle cx="35" cy="35" r={R} fill="none" stroke={color} strokeWidth="8"
        strokeDasharray={`${dash} ${C}`} strokeDashoffset={C * 0.25}
        strokeLinecap="round" style={{ transition: 'stroke-dasharray 0.6s ease' }}/>
      <text x="35" y="38" textAnchor="middle" fill="white" fontSize="13" fontWeight="700">{value}</text>
    </svg>
  );
}

// ---- Sidebar nav items ----
const NAV = [
  { id: 'dashboard', label: 'Dashboard',   icon: BarChart2 },
  { id: 'capteurs',  label: 'Capteurs',    icon: Activity },
  { id: 'alertes',   label: 'Alertes',     icon: Bell },
  { id: 'vannes',    label: 'Électrovannes', icon: Sliders },
  { id: 'zones',     label: 'Zones',       icon: MapPin },
  { id: 'users',     label: 'Utilisateurs', icon: Users },
];

// ============================================================
export default function Dashboard({ user }) {
  const [activeNav, setActiveNav]     = useState('dashboard');
  const [stats, setStats]             = useState(null);
  const [zones, setZones]             = useState([]);
  const [capteurs, setCapteurs]       = useState([]);
  const [alertes, setAlertes]         = useState([]);
  const [vannes, setVannes]           = useState([]);
  const [loading, setLoading]         = useState(true);
  const [liveData, setLiveData]       = useState(null);
  const [soundOn, setSoundOn]         = useState(false);
  const [acquitLoading, setAcquitLoading] = useState(null);
  const [vanneLoading, setVanneLoading]   = useState(null);
  const [lastUpdate, setLastUpdate]   = useState('—');

  // ---- Chargement initial ----
  const loadAll = useCallback(async () => {
    try {
      const [sRes, zRes, cRes, aRes, vRes] = await Promise.all([
        dashboardService.getStats(),
        dashboardService.getZones(),
        dashboardService.getCapteurs(),
        dashboardService.getAlertes(),
        dashboardService.getVannes(),
      ]);
      setStats(sRes.data);
      setZones(zRes.data.zones || []);
      setCapteurs(cRes.data.capteurs || []);
      setAlertes(aRes.data.alertes || aRes.data || []);
      setVannes(vRes.data.vannes || vRes.data || []);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (e) {
      console.error('Erreur chargement API:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  // ---- WebSocket temps réel (doc §6 /ws/live) ----
  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket(`${WS_BASE_URL}/ws/live`);
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          setLiveData(data);
          // Mettre à jour la valeur live d'un capteur si disponible
          if (data.capteur_id && data.valeur !== undefined) {
            setCapteurs(prev => prev.map(c =>
              c.id === data.capteur_id ? { ...c, derniere_valeur: data.valeur } : c
            ));
          }
          // Son d'alerte si DANGER
          if (data.statut === 'DANGER' && soundOn) playAlertSound();
          setLastUpdate(new Date().toLocaleTimeString());
        } catch {}
      };
      ws.onerror = () => { /* silencieux si le WS n'est pas dispo */ };
    } catch {}
    return () => { if (ws) ws.close(); };
  }, [soundOn]);

  // ---- Son d'alerte ----
  const playAlertSound = () => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      [0, 0.22, 0.44].forEach(t => {
        const o = ctx.createOscillator(), g = ctx.createGain();
        o.type = 'sawtooth';
        o.frequency.setValueAtTime(1100, ctx.currentTime + t);
        o.frequency.linearRampToValueAtTime(550, ctx.currentTime + t + 0.18);
        g.gain.setValueAtTime(0.2, ctx.currentTime + t);
        g.gain.linearRampToValueAtTime(0, ctx.currentTime + t + 0.2);
        o.connect(g); g.connect(ctx.destination);
        o.start(ctx.currentTime + t); o.stop(ctx.currentTime + t + 0.22);
      });
    } catch {}
  };

  // ---- Acquitter alerte ----
  const handleAcquitter = async (alerte) => {
    if (acquitLoading) return;
    setAcquitLoading(alerte.id);
    try {
      await actionService.acquitterAlerte(alerte.id, 'Acquitté depuis dashboard');
      await loadAll();
    } catch (e) {
      alert('Erreur : ' + (e.response?.data?.detail || 'Token requis'));
    } finally {
      setAcquitLoading(null);
    }
  };

  // ---- Contrôle vanne ----
  const handleVanne = async (vanne, action) => {
    if (vanneLoading) return;
    setVanneLoading(vanne.id);
    try {
      if (action === 'fermer') await actionService.fermerVanne(vanne.id, vanne.zone_id);
      else await actionService.ouvrirVanne(vanne.id, vanne.zone_id);
      await loadAll();
    } catch (e) {
      alert('Erreur : ' + (e.response?.data?.detail || 'Token requis'));
    } finally {
      setVanneLoading(null);
    }
  };

  // ---- Statut global → couleur ----
  const globalStatus = stats?.statut_global || 'NORMAL';
  const globalColor = { NORMAL: '#10b981', WARNING: '#f59e0b', DANGER: '#ef4444' }[globalStatus] || '#10b981';

  // ============================================================
  // RENDER
  // ============================================================
  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 overflow-hidden font-sans">

      {/* ===== SIDEBAR (style SiteKiosk) ===== */}
      <aside className="w-52 bg-slate-950 border-r border-slate-800 flex flex-col shrink-0">
        {/* Logo */}
        <div className="p-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Shield size={20} className="text-emerald-400" />
            <div>
              <div className="text-sm font-bold text-white">PURECONTROL</div>
              <div className="text-[9px] text-slate-500 font-mono">v1.0 — PFE L3</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          {NAV.map(item => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            const alertCount = item.id === 'alertes' ? (stats?.alertes?.actives || 0) : 0;
            return (
              <button key={item.id} onClick={() => setActiveNav(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                }`}>
                <Icon size={15} />
                <span>{item.label}</span>
                {alertCount > 0 && (
                  <span className="ml-auto bg-rose-500 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full">
                    {alertCount}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Profil + déconnexion */}
        <div className="p-3 border-t border-slate-800">
          <div className="text-[10px] text-slate-400 mb-1 truncate">{user?.nom}</div>
          <div className="text-[9px] text-slate-600 font-mono mb-2">{user?.role}</div>
          <button onClick={() => authService.logout()}
            className="w-full flex items-center gap-2 text-slate-500 hover:text-rose-400 text-xs transition px-1">
            <LogOut size={12} /> Se déconnecter
          </button>
        </div>
      </aside>

      {/* ===== CONTENU PRINCIPAL ===== */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* --- Top bar --- */}
        <header className="bg-slate-950 border-b border-slate-800 px-5 py-3 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-semibold text-white capitalize">{activeNav}</h1>
            {/* Fil d'Ariane */}
            <span className="text-slate-600 text-xs">/ Dashboard /</span>
            <span className="text-slate-400 text-xs capitalize">{activeNav}</span>
          </div>
          <div className="flex items-center gap-3">
            {/* Statut live */}
            {liveData && (
              <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                <Wifi size={10} className="animate-pulse" /> LIVE
              </span>
            )}
            <span className="text-[10px] text-slate-500 font-mono flex items-center gap-1">
              <Clock size={10} /> {lastUpdate}
            </span>
            {/* Son */}
            <button onClick={() => setSoundOn(!soundOn)}
              className={`flex items-center gap-1.5 px-2 py-1 rounded text-[10px] border transition ${
                soundOn ? 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10' : 'border-slate-700 text-slate-400'
              }`}>
              {soundOn ? <Volume2 size={11}/> : <VolumeX size={11}/>}
              {soundOn ? 'Son ON' : 'Son OFF'}
            </button>
            {/* Refresh */}
            <button onClick={loadAll}
              className="flex items-center gap-1.5 px-2 py-1 rounded text-[10px] border border-slate-700 text-slate-400 hover:border-slate-500 transition">
              <RefreshCw size={11} /> Actualiser
            </button>
            {/* Statut global */}
            <span className="px-2.5 py-1 rounded text-[10px] font-bold font-mono border"
              style={{ borderColor: globalColor + '60', color: globalColor, background: globalColor + '15' }}>
              ● {globalStatus}
            </span>
          </div>
        </header>

        {/* --- Corps scrollable --- */}
        <main className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <RefreshCw className="animate-spin text-emerald-400" size={32} />
            </div>
          ) : (
            <>
              {/* ======== VUE DASHBOARD ======== */}
              {activeNav === 'dashboard' && (
                <div className="space-y-4">

                  {/* KPI row (style SiteKiosk — 4 cartes) */}
                  <div className="grid grid-cols-4 gap-4">
                    {[
                      { label: 'Capteurs actifs', val: stats?.capteurs?.actifs ?? '—', total: stats?.capteurs?.total ?? 0,
                        sub: `/ ${stats?.capteurs?.total ?? 0} total`, color: '#10b981', icon: Activity },
                      { label: 'Alertes actives', val: stats?.alertes?.actives ?? '—', total: stats?.alertes?.total ?? 0,
                        sub: `${stats?.alertes?.critiques ?? 0} critiques`, color: '#ef4444', icon: Bell },
                      { label: 'Alertes total', val: stats?.alertes?.total ?? '—', total: Math.max(stats?.alertes?.total ?? 0, 1),
                        sub: 'historique', color: '#f59e0b', icon: BarChart2 },
                      { label: 'Zones surveillées', val: zones.length, total: zones.length,
                        sub: 'laboratoire IoT', color: '#3b82f6', icon: MapPin },
                    ].map((kpi, i) => {
                      const Icon = kpi.icon;
                      return (
                        <div key={i} className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex justify-between items-center hover:border-slate-700 transition">
                          <div>
                            <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{kpi.label}</div>
                            <div className="text-2xl font-bold text-white">{kpi.val}</div>
                            <div className="text-[10px] text-slate-500 mt-0.5">{kpi.sub}</div>
                          </div>
                          <DonutChart value={kpi.val} total={kpi.total} color={kpi.color} />
                        </div>
                      );
                    })}
                  </div>

                  {/* Ligne 2 : Statuts + Zones + Alertes actives */}
                  <div className="grid grid-cols-3 gap-4">

                    {/* Machine Status (style SiteKiosk) */}
                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Statut Capteurs</h3>
                        <Activity size={13} className="text-slate-600" />
                      </div>
                      <div className="flex items-center gap-4 justify-center py-2">
                        <DonutChart value={capteurs.filter(c=>c.actif).length} total={capteurs.length} color="#10b981" />
                        <div className="space-y-1.5 text-xs">
                          {[
                            { label: 'Actifs', count: capteurs.filter(c=>c.actif).length, color: '#10b981' },
                            { label: 'Inactifs', count: capteurs.filter(c=>!c.actif).length, color: '#6b7280' },
                            { label: 'Warning', count: capteurs.filter(c=>c.derniere_valeur > c.seuil_warning).length, color: '#f59e0b' },
                            { label: 'Danger', count: capteurs.filter(c=>c.derniere_valeur > c.seuil_danger).length, color: '#ef4444' },
                          ].map(s => (
                            <div key={s.label} className="flex items-center gap-2">
                              <span className="w-2.5 h-2.5 rounded-sm" style={{ background: s.color }}></span>
                              <span className="text-slate-300">{s.count} {s.label}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Projects Status → Zones */}
                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Statut Zones</h3>
                        <MapPin size={13} className="text-slate-600" />
                      </div>
                      <div className="space-y-2">
                        {zones.slice(0,4).map(z => (
                          <div key={z.id} className="flex items-center justify-between bg-slate-900 rounded px-3 py-2 border border-slate-800">
                            <div>
                              <div className="text-xs text-white font-medium">{z.nom}</div>
                              <div className="text-[10px] text-slate-500">{z.superficie} m²</div>
                            </div>
                            <StatusBadge status="ACTIF" />
                          </div>
                        ))}
                        {zones.length === 0 && <p className="text-xs text-slate-600 text-center py-3">Aucune zone</p>}
                      </div>
                    </div>

                    {/* Alertes actives */}
                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Alertes actives</h3>
                        <Bell size={13} className="text-rose-500 animate-pulse" />
                      </div>
                      <div className="space-y-2">
                        {alertes.filter(a => !a.acquittee).slice(0, 4).map(a => (
                          <div key={a.id} className="bg-rose-950/20 border border-rose-900/40 rounded px-3 py-2">
                            <div className="flex justify-between items-start gap-2">
                              <div className="flex-1 min-w-0">
                                <div className="text-xs text-rose-300 font-medium truncate">{a.message || a.type}</div>
                                <div className="text-[10px] text-slate-500 font-mono mt-0.5">{a.capteur_id}</div>
                              </div>
                              <button onClick={() => handleAcquitter(a)} disabled={acquitLoading === a.id}
                                className="shrink-0 bg-rose-700 hover:bg-rose-600 text-white text-[9px] px-2 py-0.5 rounded transition disabled:opacity-50">
                                {acquitLoading === a.id ? '...' : 'Acquitter'}
                              </button>
                            </div>
                          </div>
                        ))}
                        {alertes.filter(a => !a.acquittee).length === 0 && (
                          <div className="text-center py-4">
                            <CheckCircle2 className="text-emerald-500 mx-auto mb-1" size={22}/>
                            <p className="text-xs text-slate-500">Aucune alerte active</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Ligne 3 : Tableau capteurs + Vannes */}
                  <div className="grid grid-cols-3 gap-4">
                    {/* Tableau projets (liste capteurs — style SiteKiosk) */}
                    <div className="col-span-2 bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
                      <div className="bg-slate-900 border-b border-slate-800 px-4 py-3 flex justify-between items-center">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Matrice Capteurs</h3>
                        <span className="text-[10px] text-slate-500 font-mono">{capteurs.length} périphériques</span>
                      </div>
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="bg-slate-900/50">
                            <th className="text-left px-4 py-2 text-[10px] text-slate-500 uppercase font-semibold">Capteur</th>
                            <th className="text-left px-3 py-2 text-[10px] text-slate-500 uppercase font-semibold">Zone</th>
                            <th className="text-left px-3 py-2 text-[10px] text-slate-500 uppercase font-semibold">Type</th>
                            <th className="text-left px-3 py-2 text-[10px] text-slate-500 uppercase font-semibold">Valeur</th>
                            <th className="text-left px-3 py-2 text-[10px] text-slate-500 uppercase font-semibold">Statut</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/40">
                          {capteurs.map(c => {
                            const isWarn = c.derniere_valeur > c.seuil_warning;
                            const isDanger = c.derniere_valeur > c.seuil_danger;
                            return (
                              <tr key={c.id} className="hover:bg-slate-900/40 transition">
                                <td className="px-4 py-2.5">
                                  <div className="flex items-center gap-2">
                                    <SensorIcon type={c.type} size={13}
                                      className={isDanger ? 'text-rose-400' : isWarn ? 'text-amber-400' : 'text-emerald-400'} />
                                    <div>
                                      <div className="text-white font-medium">{c.nom}</div>
                                      <div className="text-[10px] text-slate-500 font-mono">{c.id}</div>
                                    </div>
                                  </div>
                                </td>
                                <td className="px-3 py-2.5 text-slate-400">{c.zone_id}</td>
                                <td className="px-3 py-2.5 text-slate-500 font-mono text-[10px]">{c.type}</td>
                                <td className="px-3 py-2.5">
                                  <span className={`font-mono font-bold text-[11px] px-2 py-0.5 rounded ${
                                    isDanger ? 'bg-rose-500/15 text-rose-400' :
                                    isWarn   ? 'bg-amber-500/15 text-amber-400' :
                                               'bg-slate-800 text-slate-300'
                                  }`}>
                                    {c.derniere_valeur?.toFixed ? c.derniere_valeur.toFixed(1) : c.derniere_valeur}
                                  </span>
                                </td>
                                <td className="px-3 py-2.5">
                                  <StatusBadge status={isDanger ? 'DANGER' : isWarn ? 'WARNING' : c.actif ? 'NORMAL' : 'INACTIF'} />
                                </td>
                              </tr>
                            );
                          })}
                          {capteurs.length === 0 && (
                            <tr><td colSpan={5} className="text-center py-6 text-slate-600 text-xs">Aucun capteur — vérifier la connexion au backend</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>

                    {/* Vannes */}
                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Électrovannes</h3>
                        <Sliders size={13} className="text-slate-600" />
                      </div>
                      <div className="space-y-3">
                        {vannes.slice(0, 6).map(v => (
                          <div key={v.id} className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2.5">
                            <div className="flex justify-between items-center mb-2">
                              <div>
                                <div className="text-xs text-white font-medium">{v.nom || v.id}</div>
                                <div className="text-[10px] text-slate-500 font-mono">{v.zone_id}</div>
                              </div>
                              <StatusBadge status={v.etat === 'FERMEE' ? 'WARNING' : 'NORMAL'} />
                            </div>
                            <div className="flex gap-1.5">
                              <button onClick={() => handleVanne(v, 'fermer')} disabled={vanneLoading === v.id}
                                className="flex-1 bg-rose-800/40 hover:bg-rose-700/50 border border-rose-800/40 text-rose-300 text-[9px] py-1 rounded transition disabled:opacity-50">
                                Fermer
                              </button>
                              <button onClick={() => handleVanne(v, 'ouvrir')} disabled={vanneLoading === v.id}
                                className="flex-1 bg-emerald-800/40 hover:bg-emerald-700/50 border border-emerald-800/40 text-emerald-300 text-[9px] py-1 rounded transition disabled:opacity-50">
                                Ouvrir
                              </button>
                            </div>
                          </div>
                        ))}
                        {vannes.length === 0 && <p className="text-xs text-slate-600 text-center py-4">Aucune vanne</p>}
                      </div>
                    </div>
                  </div>

                </div>
              )}

              {/* ======== VUE CAPTEURS ======== */}
              {activeNav === 'capteurs' && (
                <div>
                  <div className="mb-4 flex justify-between items-center">
                    <h2 className="text-sm font-semibold text-white">Tous les capteurs ({capteurs.length})</h2>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {capteurs.map(c => {
                      const isDanger = c.derniere_valeur > c.seuil_danger;
                      const isWarn   = c.derniere_valeur > c.seuil_warning;
                      return (
                        <div key={c.id} className={`bg-slate-950 border rounded-xl p-4 transition hover:border-slate-600 ${
                          isDanger ? 'border-rose-800/50 bg-rose-950/10' :
                          isWarn   ? 'border-amber-800/50' : 'border-slate-800'
                        }`}>
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex items-center gap-2">
                              <SensorIcon type={c.type} size={16}
                                className={isDanger ? 'text-rose-400' : isWarn ? 'text-amber-400' : 'text-emerald-400'} />
                              <div>
                                <div className="text-xs font-semibold text-white">{c.nom}</div>
                                <div className="text-[10px] text-slate-500 font-mono">{c.id}</div>
                              </div>
                            </div>
                            <StatusBadge status={isDanger ? 'DANGER' : isWarn ? 'WARNING' : 'NORMAL'} />
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-[10px]">
                            <div className="bg-slate-900 rounded p-2 border border-slate-800">
                              <div className="text-slate-500 mb-0.5">Valeur actuelle</div>
                              <div className={`font-mono font-bold ${isDanger?'text-rose-400':isWarn?'text-amber-400':'text-white'}`}>
                                {c.derniere_valeur?.toFixed ? c.derniere_valeur.toFixed(2) : '0.00'}
                              </div>
                            </div>
                            <div className="bg-slate-900 rounded p-2 border border-slate-800">
                              <div className="text-slate-500 mb-0.5">Zone</div>
                              <div className="font-mono text-slate-300">{c.zone_id}</div>
                            </div>
                            <div className="bg-slate-900 rounded p-2 border border-slate-800">
                              <div className="text-slate-500 mb-0.5">Seuil Warning</div>
                              <div className="font-mono text-amber-400">{c.seuil_warning}</div>
                            </div>
                            <div className="bg-slate-900 rounded p-2 border border-slate-800">
                              <div className="text-slate-500 mb-0.5">Seuil Danger</div>
                              <div className="font-mono text-rose-400">{c.seuil_danger}</div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    {capteurs.length === 0 && (
                      <div className="col-span-3 text-center py-16 text-slate-500">
                        <Activity className="mx-auto mb-2 opacity-30" size={36}/>
                        <p className="text-sm">Aucun capteur — backend déconnecté ?</p>
                        <p className="text-xs text-slate-600 mt-1 font-mono">GET /api/capteurs</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ======== VUE ALERTES ======== */}
              {activeNav === 'alertes' && (
                <div>
                  <div className="mb-4 flex justify-between items-center">
                    <h2 className="text-sm font-semibold text-white">Journal des alertes ({alertes.length})</h2>
                    <span className="text-xs text-rose-400 font-mono">{alertes.filter(a=>!a.acquittee).length} non acquittées</span>
                  </div>
                  <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-slate-900 border-b border-slate-800">
                          <th className="text-left px-4 py-3 text-[10px] text-slate-500 uppercase font-semibold">Capteur</th>
                          <th className="text-left px-3 py-3 text-[10px] text-slate-500 uppercase font-semibold">Message</th>
                          <th className="text-left px-3 py-3 text-[10px] text-slate-500 uppercase font-semibold">Type</th>
                          <th className="text-left px-3 py-3 text-[10px] text-slate-500 uppercase font-semibold">Date</th>
                          <th className="text-left px-3 py-3 text-[10px] text-slate-500 uppercase font-semibold">Statut</th>
                          <th className="text-center px-3 py-3 text-[10px] text-slate-500 uppercase font-semibold">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/40">
                        {alertes.map(a => (
                          <tr key={a.id} className={`hover:bg-slate-900/40 transition ${!a.acquittee ? 'bg-rose-950/5' : ''}`}>
                            <td className="px-4 py-2.5 font-mono text-slate-400 text-[10px]">{a.capteur_id}</td>
                            <td className="px-3 py-2.5 text-slate-300 max-w-xs truncate">{a.message || a.type}</td>
                            <td className="px-3 py-2.5">
                              <span className="font-mono text-[10px] text-amber-400">{a.type}</span>
                            </td>
                            <td className="px-3 py-2.5 text-slate-500 font-mono text-[10px]">
                              {a.timestamp ? new Date(a.timestamp).toLocaleString() : '—'}
                            </td>
                            <td className="px-3 py-2.5">
                              {a.acquittee
                                ? <span className="text-[10px] text-emerald-400 font-mono">✓ Acquitté</span>
                                : <span className="text-[10px] text-rose-400 animate-pulse font-mono">● Actif</span>}
                            </td>
                            <td className="px-3 py-2.5 text-center">
                              {!a.acquittee && (
                                <button onClick={() => handleAcquitter(a)} disabled={acquitLoading === a.id}
                                  className="bg-rose-700 hover:bg-rose-600 text-white text-[9px] px-3 py-1 rounded transition disabled:opacity-50">
                                  {acquitLoading === a.id ? '...' : 'Acquitter'}
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                        {alertes.length === 0 && (
                          <tr><td colSpan={6} className="text-center py-10 text-slate-600 text-xs">Aucune alerte enregistrée</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* ======== VUE VANNES ======== */}
              {activeNav === 'vannes' && (
                <div>
                  <h2 className="text-sm font-semibold text-white mb-4">Contrôle Électrovannes ({vannes.length})</h2>
                  <div className="grid grid-cols-3 gap-4">
                    {vannes.map(v => (
                      <div key={v.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                        <div className="flex justify-between items-center mb-3">
                          <div>
                            <div className="text-sm font-semibold text-white">{v.nom || v.id}</div>
                            <div className="text-[10px] text-slate-500 font-mono">{v.id} — {v.zone_id}</div>
                          </div>
                          <StatusBadge status={v.etat === 'FERMEE' ? 'WARNING' : 'NORMAL'} />
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-[10px] mb-3">
                          <div className="bg-slate-900 rounded p-2 border border-slate-800">
                            <div className="text-slate-500 mb-0.5">Mode</div>
                            <div className="text-white font-mono">{v.mode || 'AUTO'}</div>
                          </div>
                          <div className="bg-slate-900 rounded p-2 border border-slate-800">
                            <div className="text-slate-500 mb-0.5">État</div>
                            <div className={`font-mono font-bold ${v.etat === 'FERMEE' ? 'text-amber-400' : 'text-emerald-400'}`}>
                              {v.etat || '—'}
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button onClick={() => handleVanne(v,'fermer')} disabled={vanneLoading===v.id}
                            className="flex-1 bg-rose-700 hover:bg-rose-600 text-white text-xs py-2 rounded transition font-semibold disabled:opacity-50">
                            🔴 Fermer
                          </button>
                          <button onClick={() => handleVanne(v,'ouvrir')} disabled={vanneLoading===v.id}
                            className="flex-1 bg-emerald-700 hover:bg-emerald-600 text-white text-xs py-2 rounded transition font-semibold disabled:opacity-50">
                            🟢 Ouvrir
                          </button>
                        </div>
                      </div>
                    ))}
                    {vannes.length === 0 && (
                      <div className="col-span-3 text-center py-16 text-slate-500">
                        <Sliders className="mx-auto mb-2 opacity-30" size={36}/>
                        <p className="text-sm">Aucune vanne disponible</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ======== VUE ZONES ======== */}
              {activeNav === 'zones' && (
                <div>
                  <h2 className="text-sm font-semibold text-white mb-4">Zones surveillées ({zones.length})</h2>
                  <div className="grid grid-cols-3 gap-4">
                    {zones.map(z => {
                      const capteursZone = capteurs.filter(c => c.zone_id === z.id);
                      const alertesZone  = alertes.filter(a => capteursZone.some(c => c.id === a.capteur_id));
                      return (
                        <div key={z.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4 hover:border-slate-700 transition">
                          <div className="flex items-center gap-2 mb-3">
                            <MapPin size={16} className="text-blue-400" />
                            <div>
                              <div className="text-sm font-semibold text-white">{z.nom}</div>
                              <div className="text-[10px] text-slate-500 font-mono">{z.id}</div>
                            </div>
                          </div>
                          <p className="text-xs text-slate-400 mb-3">{z.description}</p>
                          <div className="grid grid-cols-3 gap-2 text-[10px]">
                            <div className="bg-slate-900 border border-slate-800 rounded p-2 text-center">
                              <div className="text-slate-500">Superficie</div>
                              <div className="font-mono text-white font-bold">{z.superficie}m²</div>
                            </div>
                            <div className="bg-slate-900 border border-slate-800 rounded p-2 text-center">
                              <div className="text-slate-500">Capteurs</div>
                              <div className="font-mono text-emerald-400 font-bold">{capteursZone.length}</div>
                            </div>
                            <div className="bg-slate-900 border border-slate-800 rounded p-2 text-center">
                              <div className="text-slate-500">Alertes</div>
                              <div className={`font-mono font-bold ${alertesZone.length > 0 ? 'text-rose-400' : 'text-slate-400'}`}>{alertesZone.length}</div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    {zones.length === 0 && (
                      <div className="col-span-3 text-center py-16 text-slate-500">
                        <MapPin className="mx-auto mb-2 opacity-30" size={36}/>
                        <p className="text-sm">Aucune zone — vérifier l'API</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ======== VUE USERS (placeholder) ======== */}
              {activeNav === 'users' && (
                <div className="text-center py-16">
                  <Users className="mx-auto mb-3 text-slate-600" size={40}/>
                  <p className="text-slate-400 text-sm">Gestion des utilisateurs</p>
                  <p className="text-slate-600 text-xs mt-1 font-mono">Réservé au rôle ADMIN</p>
                  <div className="mt-4 inline-block bg-slate-950 border border-slate-800 rounded-xl px-6 py-3 text-xs text-slate-400">
                    Rôle connecté : <span className="text-amber-400 font-mono">{user?.role}</span>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
