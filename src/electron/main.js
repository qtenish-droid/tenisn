const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;

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

function startBackend() {
  if (backendProcess) return;
  // Spawn Python FastAPI backend. Expect user to have Python on PATH.
  backendProcess = spawn(process.execPath.replace('node.exe','python.exe'), ['-m', 'backend.main'], {
    cwd: path.join(__dirname, '..', '..'),
    stdio: ['ignore', 'pipe', 'pipe']
  });

  backendProcess.stdout.on('data', (d) => console.log('[backend]', d.toString()));
  backendProcess.stderr.on('data', (d) => console.error('[backend]', d.toString()));
  backendProcess.on('exit', (code) => {
    console.log('Backend exited', code);
    backendProcess = null;
  });
}

function stopBackend() {
  if (!backendProcess) return;
  backendProcess.kill();
  backendProcess = null;
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

// Minimal IPC example — renderer can ask for backend status
ipcMain.handle('backend:status', async () => {
  return { running: !!backendProcess };
});

// NOTE: For production, replace the spawn path logic with explicit Python runtime management.
