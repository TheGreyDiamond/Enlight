const { app, BrowserWindow } = require('electron')
const ejs = require("eja");

function createWindow () {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true
    }
  })
  win.setFullScreen(true);

  win.loadFile('ui_templates/index.html')
}

function createStartupInfo(){
    const win2 = new BrowserWindow({
        width: 400,
        height: 200,
        frame: false,
        webPreferences: {
          nodeIntegration: true
        }
      })
      win2.setFullScreen(false);
      win2.setAlwaysOnTop(true);
    
      win2.loadFile('ui_templates/startUp.html')
      win2.show()
}

function init(){
    createWindow();
    createStartupInfo();
}

app.whenReady().then(init)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})