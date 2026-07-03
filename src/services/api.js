// ============================================================
// src/services/api.js
// Configuration Axios — Étudiant 3 (Frontend)
// Branché sur le backend FastAPI — Étudiant 2
// ============================================================

import axios from 'axios';

// ⚠️ Remplace par l'IP réelle du backend si pas en local
export const API_BASE_URL = 'http://127.0.0.1:8000';
export const WS_BASE_URL  = 'ws://127.0.0.1:8000';

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
  getAlertes:  ()      => api.get('/api/alertes'),
  getAlertesActives: () => api.get('/api/alertes/actives'),
  getVannes:   ()      => api.get('/api/vannes'),
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
    api.post(`/api/vannes/${id}/mode`, null, { params: { mode } }),
};
