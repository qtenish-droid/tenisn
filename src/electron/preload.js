const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('tenisn', {
  backendStatus: () => ipcRenderer.invoke('backend:status'),
  probeHardware: () => ipcRenderer.invoke('backend:probe'),
  onBackendHealth: (callback) => {
    ipcRenderer.on('backend:health', (event, status) => callback(status));
  }
});
