import { Capacitor } from '@capacitor/core';
import { PushNotifications } from '@capacitor/push-notifications';
import api from './api';
import { notificationService } from './notifications';

const PUSH_TOKEN_KEY = 'purecontrol_push_token';
let listenersReady = false;
let registrationPromise = null;

const isNative = () => Capacitor.isNativePlatform?.() === true;

const saveToken = async (token) => {
  if (!token) return false;
  localStorage.setItem(PUSH_TOKEN_KEY, token);
  await api.post('/api/push/register', {
    token,
    plateforme: Capacitor.getPlatform?.() || 'android',
  });
  return true;
};

const ensureListeners = () => {
  if (listenersReady || !isNative()) return;
  listenersReady = true;

  PushNotifications.addListener('registration', ({ value }) => {
    saveToken(value).catch((error) => {
      console.warn('FCM token non enregistre:', error);
    });
  });

  PushNotifications.addListener('registrationError', (error) => {
    console.warn('Erreur registration FCM:', error);
  });

  PushNotifications.addListener('pushNotificationReceived', (notification) => {
    const data = notification.data || {};
    notificationService.notifyAlert({
      type: 'alerte',
      niveau: data.niveau,
      capteur_id: data.capteur_id,
      source: 'FCM',
      message: data.body || notification.body,
    }).catch(() => {});
  });

  PushNotifications.addListener('pushNotificationActionPerformed', () => {
    window.location.href = '/';
  });
};

export const pushNotificationService = {
  async initialize() {
    if (!isNative()) return false;
    ensureListeners();

    try {
      const permission = await PushNotifications.checkPermissions();
      if (permission.receive !== 'granted') return false;
      return this.register();
    } catch {
      return false;
    }
  },

  async enable() {
    if (!isNative()) return false;
    ensureListeners();

    try {
      const permission = await PushNotifications.requestPermissions();
      if (permission.receive !== 'granted') return false;
      return this.register();
    } catch {
      return false;
    }
  },

  async register() {
    if (!isNative()) return false;

    const existingToken = localStorage.getItem(PUSH_TOKEN_KEY);
    if (existingToken) {
      saveToken(existingToken).catch(() => {});
    }

    if (!registrationPromise) {
      registrationPromise = PushNotifications.register()
        .then(() => true)
        .catch((error) => {
          registrationPromise = null;
          console.warn('FCM register impossible:', error);
          return false;
        });
    }

    return registrationPromise;
  },

  async unregister() {
    const token = localStorage.getItem(PUSH_TOKEN_KEY);
    if (!token) return;

    try {
      await api.post('/api/push/unregister', {
        token,
        plateforme: Capacitor.getPlatform?.() || 'android',
      });
    } catch {}
  },
};
