const { app, BrowserWindow, dialog, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

let backend;
const port = 8765;

function backendCommand() {
  if (app.isPackaged) return { command: path.join(process.resourcesPath, 'backend', 'jarvis-backend.exe'), args: [] };
  const root = path.resolve(__dirname, '../..');
  const python = process.platform === 'win32' ? path.join(root, 'backend', '.venv', 'Scripts', 'python.exe') : path.join(root, 'backend', '.venv', 'bin', 'python');
  return { command: python, args: [path.join(root, 'backend', 'desktop_server.py')] };
}

function waitForBackend() {
  return new Promise((resolve, reject) => {
    const started = Date.now();
    const check = () => {
      const request = http.get(`http://127.0.0.1:${port}/health`, response => { if (response.statusCode === 200) return resolve(); response.resume(); setTimeout(check, 250); });
      request.on('error', () => Date.now() - started > 30000 ? reject(new Error('Backend não iniciou em 30 segundos')) : setTimeout(check, 250));
    };
    check();
  });
}

async function createWindow() {
  const command = backendCommand();
  const cwd = app.isPackaged ? path.join(process.resourcesPath, 'backend') : path.resolve(__dirname, '../../backend');
  backend = spawn(command.command, command.args, { cwd, env: { ...process.env, PORT: String(port), PYTHONPATH: cwd, JARVIS_FORGE_RUNTIME: '1' }, windowsHide: true });
  backend.on('error', error => dialog.showErrorBox('Jarvis Forge', `Não foi possível iniciar o backend: ${error.message}`));
  try { await waitForBackend(); } catch (error) { dialog.showErrorBox('Jarvis Forge', error.message); app.quit(); return; }
  const window = new BrowserWindow({ width: 1440, height: 920, minWidth: 1100, minHeight: 700, backgroundColor: '#0b1018', title: 'Jarvis Forge', webPreferences: { contextIsolation: true, nodeIntegration: false } });
  await window.loadURL(`http://127.0.0.1:${port}`);
  window.on('closed', () => { if (backend) backend.kill(); });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('before-quit', () => { if (backend) backend.kill(); });
