import { Capacitor } from '@capacitor/core';
import { LocalNotifications } from '@capacitor/local-notifications';

const NOTIF_ENABLED_KEY = 'purecontrol_notifications_enabled';
const LAST_NOTIF_KEY = 'purecontrol_last_notification';
const CHANNEL_ID = 'purecontrol_alertes';
const LEVELS = ['NORMAL', 'WARNING', 'DANGER', 'CRITIQUE'];

const isNative = () => Capacitor.isNativePlatform?.() === true;

const getAlertFromPayload = (payload) => {
  if (!payload) return null;
  if (Array.isArray(payload.alertes) && payload.alertes.length > 0) {
    return payload.alertes[0];
  }
  return payload.niveau ? payload : null;
};

const levelRank = (niveau) => {
  const idx = LEVELS.indexOf(String(niveau || 'NORMAL').toUpperCase());
  return idx >= 0 ? idx : 0;
};

export const notificationService = {
  isEnabled() {
    return localStorage.getItem(NOTIF_ENABLED_KEY) === 'true';
  },

  async initialize() {
    if (!isNative()) return this.isEnabled();
    try {
      const permission = await LocalNotifications.checkPermissions();
      const granted = permission.display === 'granted';
      localStorage.setItem(NOTIF_ENABLED_KEY, granted ? 'true' : 'false');
      return granted;
    } catch {
      return false;
    }
  },

  async enable() {
    if (!isNative()) {
      if ('Notification' in window) {
        const result = await Notification.requestPermission();
        localStorage.setItem(NOTIF_ENABLED_KEY, result === 'granted' ? 'true' : 'false');
        return result === 'granted';
      }
      return false;
    }

    const permission = await LocalNotifications.requestPermissions();
    const granted = permission.display === 'granted';
    localStorage.setItem(NOTIF_ENABLED_KEY, granted ? 'true' : 'false');

    if (granted) {
      await LocalNotifications.createChannel({
        id: CHANNEL_ID,
        name: 'Alertes PURECONTROL',
        description: 'Notifications des alertes capteurs en temps reel',
        importance: 5,
        visibility: 1,
        lights: true,
        vibration: true,
      });
    }

    return granted;
  },

  async notifyAlert(payload) {
    const alert = getAlertFromPayload(payload);
    if (!alert || !this.isEnabled()) return false;

    const niveau = String(alert.niveau || payload.niveau || 'NORMAL').toUpperCase();
    if (levelRank(niveau) < levelRank('WARNING')) return false;

    const capteurId = alert.capteur_id || payload.capteur_id || 'capteur inconnu';
    const key = `${capteurId}:${niveau}`;
    const now = Date.now();

    try {
      const last = JSON.parse(localStorage.getItem(LAST_NOTIF_KEY) || '{}');
      if (last.key === key && now - Number(last.time || 0) < 60000) return false;
      localStorage.setItem(LAST_NOTIF_KEY, JSON.stringify({ key, time: now }));
    } catch {
      localStorage.setItem(LAST_NOTIF_KEY, JSON.stringify({ key, time: now }));
    }

    const title = `Alerte ${niveau}`;
    const body = `Capteur ${capteurId} : intervention requise.`;

    if (!isNative()) {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body });
        return true;
      }
      return false;
    }

    await LocalNotifications.schedule({
      notifications: [{
        id: Math.floor(now % 2147483647),
        title,
        body,
        channelId: CHANNEL_ID,
        schedule: { at: new Date(now + 100) },
      }],
    });
    return true;
  },
};
