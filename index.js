const { app, BrowserWindow, screen, ipcMain } = require("electron");
const fs = require("fs");
const { win32 } = require("path");
const sysInf = require("systeminformation");

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
  win.setMenuBarVisibility(false);
  win.setAutoHideMenuBar(true);
  win.loadFile("ui_templates/index.html");
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
  return win2;
}

function doneLoading() {
  var fadeOutI = 1;
  aWin2.webContents.executeJavaScript(
    "document.getElementById('current').innerHTML = 'Done';"
  );
  var fadeIntervall = setInterval(function () {
    try {
      if (fadeOutI < 0) {
        clearInterval(fadeIntervall);
        aWin2.webContents.executeJavaScript("window.close()");
      } else {
        aWin2.setOpacity(fadeOutI);
        fadeOutI = fadeOutI - 0.05;
      }
    } catch (e) {
      console.warn("Startup window got destroyed!");
      clearInterval(fadeIntervall);
    }
  }, 20);
  //aWin2.webContents.executeJavaScript("window.close()")
}

function init() {
  createWindow();
  aWin2 = createStartupInfo();
  setTimeout(doneLoading, 2000);
  ipcMain.on("asynchronous-message", (event, arg) => {
    console.log(arg); // prints "ping"
    if (arg == "hasBattery") {
      event.reply("asynchronous-reply", sysInf.battery().hasbattery);
    }
  });

  ipcMain.on("synchronous-message", (event, arg) => {
    //console.log(arg) // prints "ping"
    if (String(arg).includes("hasBattery")) {
      sysInf.battery(function (data) {
        event.returnValue = data.hasbattery;
        //event.returnValue = true
      });
    }else if (String(arg).includes("getBatteryLevel")) {
      sysInf.battery(function (data) {
        //event.returnValue = 2
        event.returnValue = data.percent;
      });
    }else if (String(arg).includes("loadOverride")) {
      event.returnValue = false;
    }else if (String(arg).includes("getNetworks")) {
      sysInf.networkInterfaces(function (data) {
        event.returnValue = data;
      });
    }else if (String(arg).includes("set:newNetwork")) {
      fs.writeFile('usrStore/lastNetwork.data', String(arg).split("|")[1], function (err) {
        if (err) return console.log(err);
        console.log('Saved new main network');
      });
      event.returnValue = "";
    } else if (String(arg).includes("getMainNetwork")) {
      try{
        last = fs.readFileSync("usrStore/lastNetwork.data")
        console.log(last.toString())
        event.returnValue = last.toString();
      }catch(e){
        sysInf.networkInterfaces(function (data) {
          fs.writeFileSync("usrStore/lastNetwork.data", data[0].ifaceName);
          event.returnValue = data[0].ifaceName
        });
       
      }
      
    }else{
      event.returnValue = "ERR:UNKNOW_CMD"
    }
  });
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
