const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow = null;
let backendProcess = null;
let backendReady = false;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));
}

function spawnBackend() {
  if (backendProcess) return;
  try {
    backendProcess = spawn('python', ['-m', 'backend.main'], {
      cwd: path.join(__dirname, '..', '..'),
      stdio: ['ignore', 'pipe', 'pipe']
    });

    backendProcess.stdout.on('data', (d) => console.log('[backend]', d.toString()));
    backendProcess.stderr.on('data', (d) => console.error('[backend]', d.toString()));
    backendProcess.on('exit', (code) => {
      console.log('Backend exited', code);
      backendProcess = null;
      backendReady = false;
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('backend:health', { running: false });
      }
    });
  } catch (e) {
    console.error('Failed to spawn backend:', e);
    backendProcess = null;
  }
}

function fetchJson(url, timeout = 3000) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve(json);
        } catch (err) {
          reject(err);
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(timeout, () => {
      req.abort();
      reject(new Error('timeout'));
    });
  });
}

async function pollBackendHealth(retries = 10, intervalMs = 800) {
  const url = 'http://127.0.0.1:8001/';
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetchJson(url, 2000);
      backendReady = true;
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('backend:health', { running: true, info: res });
      }
      return true;
    } catch (e) {
      // wait
      await new Promise(r => setTimeout(r, intervalMs));
    }
  }
  backendReady = false;
  if (mainWindow && mainWindow.webContents) {
    mainWindow.webContents.send('backend:health', { running: false });
  }
  return false;
}

function startBackend() {
  if (backendProcess) return;
  spawnBackend();
  // Poll health and inform renderer
  pollBackendHealth().then(ok => {
    console.log('Backend ready:', ok);
  });
}

function stopBackend() {
  if (!backendProcess) return;
  try { backendProcess.kill(); } catch (e) { console.error(e); }
  backendProcess = null;
  backendReady = false;
}

app.whenReady().then(() => {
  createWindow();
  startBackend();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

// IPC: renderer asks if backend process is running (based on spawn state)
ipcMain.handle('backend:status', async () => {
  return { running: !!backendProcess, ready: backendReady };
});

// IPC: proxy hardware probe request to backend service
ipcMain.handle('backend:probe', async () => {
  try {
    const res = await fetchJson('http://127.0.0.1:8001/api/hardware/probe', 5000);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});

// Allow renderer to listen for health events
// Sending 'backend:health' via webContents when state changes above

// NOTE: This is a minimal implementation. For production, add permission checks, controlled IPC, and robust runtime management.
