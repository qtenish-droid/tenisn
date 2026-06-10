const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('tenisn', {
  backendStatus: () => ipcRenderer.invoke('backend:status')
});
