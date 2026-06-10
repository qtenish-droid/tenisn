const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('tenisn', {
  backendStatus: () => ipcRenderer.invoke('backend:status'),
  probeHardware: () => ipcRenderer.invoke('backend:probe'),
  modelsRecommend: () => ipcRenderer.invoke('backend:models:recommend'),
  modelsInstall: (name, source) => ipcRenderer.invoke('backend:models:install', { name, source }),
  getSettings: () => ipcRenderer.invoke('settings:get'),
  rerunProbe: () => ipcRenderer.invoke('settings:rerunProbe'),
  onBackendHealth: (callback) => {
    ipcRenderer.on('backend:health', (event, status) => callback(status));
  },
  onSettingsUpdated: (callback) => {
    ipcRenderer.on('settings:updated', (event, settings) => callback(settings));
  }
});
