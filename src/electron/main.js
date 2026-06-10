const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow = null;
let backendProcess = null;
let backendReady = false;

const userDataPath = app.getPath('userData');
const settingsPath = path.join(userDataPath, 'settings.json');

function loadSettings() {
  try {
    if (fs.existsSync(settingsPath)) {
      const raw = fs.readFileSync(settingsPath, 'utf8');
      return JSON.parse(raw);
    }
  } catch (e) {
    console.error('Failed to load settings:', e);
  }
  return null;
}

function saveSettings(obj) {
  try {
    if (!fs.existsSync(userDataPath)) fs.mkdirSync(userDataPath, { recursive: true });
    fs.writeFileSync(settingsPath, JSON.stringify(obj, null, 2), 'utf8');
    return true;
  } catch (e) {
    console.error('Failed to save settings:', e);
    return false;
  }
}

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

function postJson(url, bodyObj, timeout = 5000) {
  return new Promise((resolve, reject) => {
    try {
      const parsed = new URL(url);
      const data = JSON.stringify(bodyObj);
      const options = {
        hostname: parsed.hostname,
        port: parsed.port,
        path: parsed.pathname + (parsed.search || ''),
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(data)
        }
      };
      const req = http.request(options, (res) => {
        let resp = '';
        res.on('data', chunk => resp += chunk);
        res.on('end', () => {
          try { resolve(JSON.parse(resp)); } catch (e) { reject(e); }
        });
      });
      req.on('error', reject);
      req.setTimeout(timeout, () => { req.abort(); reject(new Error('timeout')); });
      req.write(data);
      req.end();
    } catch (e) {
      reject(e);
    }
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

async function performFirstRunProbeIfNeeded() {
  const settings = loadSettings();
  if (settings && settings.probe && settings.firstRunComplete) {
    console.log('First-run probe already completed.');
    return settings;
  }

  console.log('Performing first-run hardware probe...');
  startBackend();
  const ok = await pollBackendHealth(15, 1000);
  if (!ok) {
    console.warn('Backend not ready for probe. Saving minimal settings.');
    const minimal = { firstRunComplete: false, probe: null };
    saveSettings(minimal);
    return minimal;
  }

  try {
    const probe = await fetchJson('http://127.0.0.1:8001/api/hardware/probe', 8000);
    const s = { firstRunComplete: true, probe: probe, updatedAt: new Date().toISOString() };
    saveSettings(s);
    if (mainWindow && mainWindow.webContents) {
      mainWindow.webContents.send('settings:updated', s);
    }
    return s;
  } catch (e) {
    console.error('Probe failed:', e);
    const minimal = { firstRunComplete: false, probe: null };
    saveSettings(minimal);
    return minimal;
  }
}

app.whenReady().then(async () => {
  createWindow();
  // Start backend and perform probe if needed
  await performFirstRunProbeIfNeeded();
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

// IPC: model recommendations
ipcMain.handle('backend:models:recommend', async () => {
  try {
    const res = await fetchJson('http://127.0.0.1:8001/api/models/recommend', 5000);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});

// IPC: install model (POST)
ipcMain.handle('backend:models:install', async (event, body) => {
  try {
    const res = await postJson('http://127.0.0.1:8001/api/models/install', body, 15000);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});

// Settings IPC
ipcMain.handle('settings:get', async () => {
  return loadSettings();
});

ipcMain.handle('settings:rerunProbe', async () => {
  // Force re-run probe
  startBackend();
  const ok = await pollBackendHealth(15, 1000);
  if (!ok) return { ok: false, error: 'backend-not-ready' };
  try {
    const probe = await fetchJson('http://127.0.0.1:8001/api/hardware/probe', 8000);
    const s = { firstRunComplete: true, probe: probe, updatedAt: new Date().toISOString() };
    saveSettings(s);
    if (mainWindow && mainWindow.webContents) {
      mainWindow.webContents.send('settings:updated', s);
    }
    return { ok: true, data: s };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});

// Allow renderer to listen for health events
// Sending 'backend:health' via webContents when state changes above

// NOTE: This is a minimal implementation. For production, add permission checks, controlled IPC, and robust runtime management.
