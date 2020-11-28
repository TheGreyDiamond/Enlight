const {
  app,
  BrowserWindow,
  screen,
  ipcMain,
  BrowserView,
} = require("electron");
var Config = require("config-js");
const fs = require("fs");
const { win32 } = require("path");
const sysInf = require("systeminformation");
const dgram = require("dgram");
var server = dgram.createSocket("udp4");
const express = require("express");
const { time } = require("console");
const { nanoid } = require("nanoid");
const restApp = express();

const restPort = 33334;
const PORT = 33333;
const MULTICAST_ADDR = "192.168.178.50";

var aWin2 = undefined;

var preLoadedAmount = 0;

var networkInterfaces = [];

/// !!!-----------!!!
/// PAGE LOOKUP TABLE
var preloadedPageLookup = {};

var pageLookup = {};
pageLookup["index"] = "index.html";
pageLookup["session"] = "sessions.html";
pageLookup["header"] = "header.html";

/// !!!-----------!!!
//  Session state data
// -1 Unset/Unknown
// 0 Not connected
// 1 Connecting
// 2 Connected as host
// 3 Connected as Client
// 4 Connection failed

var sessionState = -1;
var sessionStateGoal = -1;

var mySession = {
  name: "Unnamed Session",
  joinable: false,
  passwordProtected: false,
  passwordHash: "",
  members: 1,
  memberList: [],
  usedUIDs: [],
};

var mainConn = "";
var mainNetworkInterface = undefined;

for (const [key, value] of Object.entries(pageLookup)) {
  // check if the property/key is defined in the object itself, not in parent
  if (pageLookup.hasOwnProperty(key)) {
    fs.readFile("ui_templates/" + value, "utf8", function (err, data) {
      preLoadedAmount++;
      if (err) {
        return console.log(err);
      }
      preloadedPageLookup[key] = data;
    });
  }
}

function prepBroadcast() {
  server.bind(PORT, function () {
    server.setBroadcast(true);
    server.setMulticastTTL(128);
    server.addMembership(MULTICAST_ADDR);
  });
  runy = true;
  while (runy) {
    //console.log("INTERFACE EMPTY", networkInterfaces)
    if (networkInterfaces.length >= 1) {
      runy = false;
    }
  }
  console.log("Waiting done");

  var Ibroad = 0;
  var names = [];
  while (Ibroad < networkInterfaces.length) {
    names.push(networkInterfaces[Ibroad].ifaceName);
    Ibroad++;
  }
  last = fs.readFileSync("usrStore/lastNetwork.data");
  mainConn = last.toString();
  ind = names.indexOf(mainConn);
  mainNetworkInterface = networkInterfaces[ind];
  //console.info("!!!!!!!!!!!!!!!!!!!!!", mainConn, names, mainNetworkInterface)
}

function broadcastNew() {
  var message = new Buffer(
    "ENLIGHT_NEW_SESSION$" + String(mainNetworkInterface.ip4)
  );
  server.send(message, 0, message.length, PORT, MULTICAST_ADDR);
  console.log("Sent " + message + " to the wire...");
}

function loadPage(name) {
  load = preloadedPageLookup[name];
  if (load == undefined) {
    load = fs.readFileSync("ui_templates/" + pageLookup[name]).toString();
    console.warn("Loading fallback for page " + name);
  }
  return load;
}

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

  main = loadPage("index");
  header = loadPage("header");
  //
  //header = fs.readFileSync("ui_templates/header.html").toString();
  toLoad = header + main;
  fs.writeFileSync("ui_templates/temp.html", toLoad);
  //win.loadURL("data:text/html;charset=utf-8," + encodeURI(toLoad));
  win.loadFile("ui_templates/temp.html");
  return win;
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
  if (Object.keys(pageLookup).length == preLoadedAmount) {
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
  } else {
    console.warn("Had to reschedule load finish");
    setTimeout(doneLoading, 200);
  }
}

function init() {
  win = createWindow();
  aWin2 = createStartupInfo();
  setInterval(function () {
    sysInf.networkInterfaces(function (data) {
      networkInterfaces = data;
    });
  }, 2 * 60 * 1000); // Update network interface every 2 mins

  sysInf.networkInterfaces(function (data) {
    networkInterfaces = data;
  });

  var langs = new Config("./lang/langs_v1.js");

  sessionState = 0; // Init with no connection
  setTimeout(function () {
    console.log("Starting restfulServer API interface");
    restApp.listen(restPort, () => {
      console.log(`Restful is running on http://localhost:${restPort}`);
    });

    restApp.get("/", (req, res) => {
      res.send("Hello World! The RestFul API of Enlight is up and working!");
    });

    restApp.get("/api/v1/ping", (req, res) => {
      res.json({ state: "Succes", uptime: time.time() });
    });

    restApp.get("/api/v1/session/info", (req, res) => {
      res.json({
        state: "Succes",
        name: mySession.name,
        joinAble: mySession.joinable,
        passwordProtected: mySession.passwordProtected,
        memberAmount: mySession.members,
      });
    });

    restApp.get("/api/v1/session/join", (req, res) => {
      if (mySession.joinable) {
        if (mySession.passwordProtected == false) {
          uid = nanoid();
          while (mySession.usedUIDs.includes(uid)) {
            uid = nanoid();
          }

          mySession.usedUIDs.push(uid);
          dev = {
            type: "client",
            ip: req.connection.remoteAddress,
            uid: uid,
          };
          mySession.memberList.push();
          mySession.members++;
          res.json({ state: "Succes", uid: uid });
        } else {
          res.json({
            state: "Failed",
            message: "Passwords are not yet implemented",
            code: -1,
          });
        }
      } else {
        res.json({
          state: "Failed",
          message: "Session is not joinable.",
          code: 1,
        });
      }
      //name: mySession.name, joinAble: mySession.joinable, passwordProtected: mySession.passwordProtected});
    });
  }, 20);

  // Handling sessioning
  setInterval(function () {
    if (sessionStateGoal == 2) {
      broadcastNew();
      sessionState = 2;
    }
  }, 400);

  setTimeout(doneLoading, 2000);
  ipcMain.on("asynchronous-message", (event, arg) => {
    console.log(arg);
    if (arg == "hasBattery") {
      event.reply("asynchronous-reply", sysInf.battery().hasbattery);
    }
  });

  ipcMain.on("synchronous-message", (event, arg) => {
    if (String(arg).includes("hasBattery")) {
      sysInf.battery(function (data) {
        event.returnValue = data.hasbattery;
      });
    } else if (String(arg).includes("getBatteryLevel")) {
      sysInf.battery(function (data) {
        event.returnValue = data.percent;
      });
    } else if (String(arg).includes("loadOverride")) {
      event.returnValue = false;
    } else if (String(arg).includes("getNetworks")) {
      event.returnValue = networkInterfaces;
    } else if (String(arg).includes("set:newNetwork")) {
      fs.writeFile(
        "usrStore/lastNetwork.data",
        String(arg).split("|")[1],
        function (err) {
          if (err) return console.log(err);
          console.log("Saved new main network");
        }
      );
      event.returnValue = "";
    } else if (String(arg).includes("getMainNetwork")) {
      try {
        last = fs.readFileSync("usrStore/lastNetwork.data");
        //console.log(last.toString())
        event.returnValue = last.toString();
        mainConn = last.toString();
      } catch (e) {
        sysInf.networkInterfaces(function (data) {
          fs.writeFileSync("usrStore/lastNetwork.data", data[0].ifaceName);
          event.returnValue = data[0].ifaceName;
        });
      }
    } else if (String(arg).includes("PAGE:change")) {
      newPage = String(arg).split(".")[1];
      main = header = loadPage(newPage);

      header = loadPage("header");
      toLoad = header + main;
      const timestamp = Date.now();
      fs.writeFileSync("ui_templates/temp.html", toLoad);
      const timestamp2 = Date.now();
      win.loadFile("ui_templates/temp.html");
      const timestamp3 = Date.now();
      //win.loadFile("ui_templates/header.html")
      event.returnValue = "";
    } else if (String(arg).includes("SESSION:get.state")) {
      event.returnValue = sessionState;
    } else if (String(arg).includes("SESSION:createNew")) {
      setTimeout(prepBroadcast, 5);
      mySession.name = String(arg).split("|")[1];
      mySession.joinable = true;
      sessionState = 1;
      sessionStateGoal = 2;
      event.returnValue = "";
    } else {
      event.returnValue = "ERR:UNKNOW_CMD";
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
