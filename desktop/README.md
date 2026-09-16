# Jarvis Forge Desktop

Aplicativo Windows com janela Electron. Em desenvolvimento, inicia o FastAPI usando `backend/.venv`; no instalador, inicia o backend empacotado com PyInstaller.

## Desenvolvimento

```powershell
cd desktop
npm install
npm start
```

## Gerar instalador

Execute `build-windows.ps1` na raiz do projeto. O instalador será criado em `desktop/release`.
