// ============================================================
// src/services/api.js
// Configuration Axios — Étudiant 3 (Frontend)
// Branché sur le backend FastAPI — Étudiant 2
// ============================================================

import axios from 'axios';

// ⚠️ Remplace par l'IP réelle du backend si pas en local
const DEFAULT_API_URL = 'https://projet-de-fin-d-etudes.onrender.com';

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_URL
).replace(/\/$/, '');

export const WS_BASE_URL = (
  import.meta.env.VITE_WS_BASE_URL ||
  API_BASE_URL.replace(/^https?:\/\//, API_BASE_URL.startsWith('https') ? 'wss://' : 'ws://')
).replace(/\/$/, '');

const apiUrl = (path) => `${API_BASE_URL}${path}`;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000,
});

// Injecte automatiquement le token JWT dans chaque requête
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('purecontrol_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Gestion globale des erreurs 401 → déconnexion auto
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('purecontrol_token');
      localStorage.removeItem('purecontrol_role');
      localStorage.removeItem('purecontrol_user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;

// ---- Helpers Auth ----
export const authService = {
  async login(email, mot_de_passe) {
    const res = await api.post('/auth/login', { email, mot_de_passe });
    localStorage.setItem('purecontrol_token', res.data.access_token);
    localStorage.setItem('purecontrol_role', res.data.utilisateur.role);
    localStorage.setItem('purecontrol_user', JSON.stringify(res.data.utilisateur));
    return res.data.utilisateur;
  },
  async registerWithGoogle(id_token) {
    const res = await api.post('/auth/register/google', { id_token });
    localStorage.setItem('purecontrol_token', res.data.access_token);
    localStorage.setItem('purecontrol_role', res.data.utilisateur.role);
    localStorage.setItem('purecontrol_user', JSON.stringify(res.data.utilisateur));
    return res.data.utilisateur;
  },
  logout() {
    localStorage.removeItem('purecontrol_token');
    localStorage.removeItem('purecontrol_role');
    localStorage.removeItem('purecontrol_user');
    window.location.href = '/login';
  },
  getUser() {
    try { return JSON.parse(localStorage.getItem('purecontrol_user')); } catch { return null; }
  },
  getRole() { return localStorage.getItem('purecontrol_role'); },
  isLoggedIn() { return !!localStorage.getItem('purecontrol_token'); },
};

// ---- Helpers Dashboard ----
export const dashboardService = {
  getStats:    ()      => api.get('/api/dashboard/stats'),
  getZones:    ()      => api.get('/api/zones'),
  getCapteurs: ()      => api.get('/api/capteurs'),
  getCapteur:  (id)    => api.get(`/api/capteurs/${id}`),
  getHistoriqueCapteur: (id, heures = 24) => api.get(`/api/capteurs/${id}/historique`, { params: { heures } }),
  getMaintenance: (minutes = 10) => api.get('/api/capteurs/maintenance', { params: { minutes } }),
  getAlertes:  ()      => api.get('/api/alertes'),
  getAlertesActives: () => api.get('/api/alertes/actives'),
  getVannes:   ()      => api.get('/api/vannes'),
  getAudit: (limite = 100) => api.get('/api/audit', { params: { limite } }),
  getUsers: () => api.get('/api/users'),
};

export const documentService = {
  rapportMensuelUrl: () => apiUrl('/api/rapports/generer'),
  rapportIncidentUrl: (id) => apiUrl(`/api/alertes/${id}/rapport`),
  qrcodeCapteurUrl: (id) => apiUrl(`/api/capteurs/${id}/qrcode`),
};

// ---- Helpers Actions protégées (JWT requis) ----
export const actionService = {
  acquitterAlerte: (id, commentaire = '') =>
    api.post(`/api/alertes/${id}/acquitter`, null, { params: { commentaire } }),
  fermerVanne: (id, zone_id) =>
    api.post(`/api/vannes/${id}/fermer`, null, { params: { zone_id } }),
  ouvrirVanne: (id, zone_id) =>
    api.post(`/api/vannes/${id}/ouvrir`, null, { params: { zone_id } }),
  changerModeVanne: (id, mode) =>
    api.post(`/api/vannes/${id}/mode`, null, { params: { nouveau_mode: mode } }),
  modifierSeuilsCapteur: (id, seuils) =>
    api.patch(`/api/capteurs/${id}/seuils`, seuils),
  simulerMesure: (data) =>
    api.post('/api/simulation/mesure', data),
  modifierUtilisateur: (id, data) =>
    api.patch(`/api/users/${id}`, data),
};
