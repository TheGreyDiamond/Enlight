const { app, BrowserWindow, screen } = require("electron");
const fs = require('fs');
const { win32 } = require("path");
const sysInf = require('systeminformation');

var aWin2 = undefined;

function createWindow() {
  const win = new BrowserWindow({
    width: screen.getPrimaryDisplay().size.width,
    height: screen.getPrimaryDisplay().size.height,
    webPreferences: {
      nodeIntegration: true,
    },
  });
  win.setFullScreen(true);
  win.setMenuBarVisibility(false)
  win.setAutoHideMenuBar(true)
  win.loadFile("ui_templates/index.html");
  setInterval(function(){
    // Updating battery
  }, 500)
}

function createStartupInfo() {
  const win2 = new BrowserWindow({
    width: 400,
    height: 200,
    frame: false,
    webPreferences: {
      nodeIntegration: true,
    },
  });

  win2.setFullScreen(false);
  win2.setAlwaysOnTop(true);
  win2.loadFile("ui_templates/startUp.html");
  win2.show();
 return(win2)
}

function doneLoading(){
  var fadeOutI = 1;
  aWin2.webContents.executeJavaScript("document.getElementById('current').innerHTML = 'Done';")
  var fadeIntervall = setInterval(function(){
    try{if(fadeOutI < 0){
      clearInterval(fadeIntervall);
      aWin2.webContents.executeJavaScript("window.close()")
    }else{
      aWin2.setOpacity(fadeOutI)
      fadeOutI = fadeOutI - 0.05
    }
  }catch(e){
    console.warn("Startup window got destroyed!")
    clearInterval(fadeIntervall);
  }
    
    
  }, 20)
  //aWin2.webContents.executeJavaScript("window.close()")

}

function init() {
  createWindow();
  aWin2 = createStartupInfo();
  setTimeout(doneLoading, 2000);
  //sysInf.battery()
  //.then(data => console.log(data))
  //.catch(error => console.error(error));
}

app.whenReady().then(init);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
