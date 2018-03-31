#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Conan Exiles Server Manager.

by David Maus/neslane at www.gef-gaming.de
"""

# ---------------------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------------------

import os
import sys
from PyQt5 import uic, QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from ui import resources
from datetime import datetime, time
from time import sleep
import psutil
import subprocess
from configparser import ConfigParser
import pysteamcmd
import pathlib
import webbrowser
import re
from glob import glob
from modules import design, functions, getSteamWorkshopMods


# ---------------------------------------------------------------------------------------
# Global
# ---------------------------------------------------------------------------------------

__author__  = "David MAus"
__version__ = "0.1.0"
__license__ = "MIT"
__title__   = 'Conan Server Manager ' +  __version__ + ' - by GEF-GAMING.DE'

# ---------------------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------------------

sys.dont_write_bytecode = True
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# ---------------------------------------------------------------------------------------
# Get & Set Pathes
# ---------------------------------------------------------------------------------------


def getCurrentExecFolder():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.dirname(__file__))


def getCurrentRootFolder():
    if getattr(sys, 'frozen', False):
        currentRootFolder = os.path.dirname(sys.executable)
        return os.path.join(currentRootFolder)
    else:
        currentRootFolder = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(currentRootFolder, '../')


def resource_path(relative_path):
    """Get Absolute Path."""
    base_path = getattr(sys, '_MEIPASS',
                        os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


uiFilePath          = resource_path("ui/interface.ui")
uiDownloadFilePath  = resource_path("ui/interfaceDownload.ui")
iconFilePath        = resource_path("ui/main.ico")
currentExecFolder   = getCurrentExecFolder()
currentRootFolder   = getCurrentRootFolder()
settingsPath        = os.path.join(currentRootFolder, 'data', 'settings.ini')


# ---------------------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------------------


class mainWindow(QtWidgets.QDialog):
    """Make Main Window."""

    def __init__(self):
        """Initialize Main Window."""

        super(mainWindow, self).__init__()

        # Load UI File
        uic.loadUi(uiFilePath, self)

        # Set Values
        self.linePath.setText(ConanServerPath)
        self.lineServerName.setText(ServerName)
        self.lineServerRestart.setText(ServerRestart)
        self.lineMaxPlayers.setText(MaxPlayers)
        self.lineServerPort.setText(ServerPort)
        self.lineSteamPort.setText(SteamPort)
        self.lineAdminPW.setText(AdminPW)
        self.lineCollection.setText(collection)

        if(collectionDisable == True):
            self.checkDisableMods.setChecked(True)
        else:
            self.checkDisableMods.setChecked(False)

        # Button Mapping
        self.buttonPath.clicked.connect(self.saveFileDialog)
        self.buttonSave.clicked.connect(self.saveConfig)

        self.buttonStartServer.clicked.connect(self.startServerClicked)

        self.buttonStopServer.clicked.connect(self.stopServer)
        self.buttonInstallServer.clicked.connect(lambda: installServer())

        # eventFilter
        self.headerLogo.installEventFilter(self)



    def saveFileDialog(self):
        my_dir = QFileDialog.getExistingDirectory(self, "Open a folder", ConanServerPath, QFileDialog.ShowDirsOnly)
        if(my_dir == ''):
            my_dir = ConanServerPath

        else:
            self.linePath.setText(my_dir)
            self.saveConfig()

    def resetServerRestartFlag(self):
        global stopRestartFlag
        stopRestartFlag = False

    def startServerClicked(self):
        global ServerRestart
        if (ServerRestart == '0' or ServerRestart == ''):
            self.startServer()
        else:
            self.startServerRestart()

    def startServer(self):
        conanExePath = os.path.join(ConanServerPath, 'ConanSandboxServer.exe')
        conanParameters = ' -MaxPlayers=' \
                          + MaxPlayers \
                          + ' -Port=' \
                          + ServerPort \
                          + ' -QueryPort=' \
                          + SteamPort \
                          + ' -ServerName="' \
                          + ServerName \
                          + '" -AdminPassword=' \
                          + AdminPW

        self.StartServerThread_T = StartServerThread(conanExePath, conanParameters)

        self.StartServerThread_T.start()


    def startServerRestart(self):
        global stopRestartFlag
        stopRestartFlag = False
        self.startServerRestartAuto()


    def startServerRestartAuto(self):
        conanExePath = os.path.join(ConanServerPath, 'ConanSandboxServer.exe')
        conanParameters = ' -MaxPlayers=' \
                          + MaxPlayers \
                          + ' -Port=' \
                          + ServerPort \
                          + ' -QueryPort=' \
                          + SteamPort \
                          + ' -ServerName="' \
                          + ServerName \
                          + '" -AdminPassword=' \
                          + AdminPW
        global ServerRestart
        self.StartServerThread_T = StartServerThread(conanExePath, conanParameters)
        self.waiterThread_T = waiterThread(ServerRestart)

        sleep(1)
        global stopRestartFlag
        if stopRestartFlag:
            pass
        else:
            self.StartServerThread_T.start()
            self.waiterThread_T.start()
            self.waiterThread_T.finished.connect(self.stopServerAndRestart)


    def stopServer(self):


        self.StartServerThread_T.stop()

        self.waiterThread_T.stop()


        global stopRestartFlag
        stopRestartFlag = True

    def stopServerAndRestart(self):
        self.StartServerThread_T.stop()
        self.StartServerThread_T.terminate()
        self.waiterThread_T.stop()
        self.waiterThread_T.terminate()

        self.startServerRestartAuto()

    def saveConfig(self):
        my_dir = self.linePath.text()
        ServerName = self.lineServerName.text()
        ServerRestart = self.lineServerRestart.text()
        MaxPlayers = self.lineMaxPlayers.text()
        ServerPort = self.lineServerPort.text()
        SteamPort = self.lineSteamPort.text()
        AdminPW = self.lineAdminPW.text()
        collection = self.lineCollection.text()


        if(self.checkDisableMods.isChecked()):
            collectionDisable = 'True'
        else:
            collectionDisable = 'False'


        writeSettings(my_dir, ServerName, ServerRestart, MaxPlayers, ServerPort, SteamPort, AdminPW, collection, collectionDisable)
        readSettings()

    def eventFilter(self, target, event):
        """Start Main Function."""
        if target == self.headerLogo and event.type() == QtCore.QEvent.MouseButtonPress:
            self.openURL()

        return False

    def openURL(self):
        """Start Main Function."""
        webbrowser.open_new_tab('http://www.gef-gaming.de/forum')


# ---------------------------------------------------------------------------------------
# Main Functions
# ---------------------------------------------------------------------------------------


def readSettings():
    global ConanServerPath
    global ServerName
    global ServerRestart
    global MaxPlayers
    global ServerPort
    global SteamPort
    global AdminPW
    global collection
    global collectionDisable

    if os.path.isfile(settingsPath):

        config = ConfigParser()
        config.read(settingsPath, encoding='utf8')

        ConanServerPath = config['SETTINGS']['ConanServerPath']
        ServerName = config['SETTINGS']['ServerName']
        ServerRestart = config['SETTINGS']['ServerRestart']
        MaxPlayers = config['SETTINGS']['MaxPlayers']
        ServerPort = config['SETTINGS']['ServerPort']
        SteamPort = config['SETTINGS']['SteamPort']
        AdminPW = config['SETTINGS']['AdminPW']
        collection = config['SETTINGS']['collection']
        collectionDisable = config.getboolean('SETTINGS', 'collectionDisable')



    else:
        ConanServerPath = ''
        ServerName = ''
        ServerRestart = ''
        MaxPlayers = ''
        ServerPort = ''
        SteamPort = ''
        AdminPW = ''
        collection = ''
        collectionDisable = ''

        open(settingsPath, "w+").close()
        config = ConfigParser()
        config.read(settingsPath, encoding='utf8')
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'ConanServerPath', ConanServerPath)
        config.set('SETTINGS', 'ServerName', ServerName)
        config.set('SETTINGS', 'ServerRestart', ServerRestart)
        config.set('SETTINGS', 'MaxPlayers', MaxPlayers)
        config.set('SETTINGS', 'ServerPort', ServerPort)
        config.set('SETTINGS', 'SteamPort', SteamPort)
        config.set('SETTINGS', 'AdminPW', AdminPW)
        config.set('SETTINGS', 'collection', collection)
        config.set('SETTINGS', 'collectionDisable', collectionDisable)

        with open(settingsPath, 'w', encoding='utf8') as configfile:
            config.write(configfile)


def writeSettings(ConanServerPathNEW, ServerNameNEW, ServerRestartNEW, MaxPlayersNEW, ServerPortNEW, SteamPortNEW, AdminPWNEW, collectionNEW, collectionDisableNEW):

    config = ConfigParser()
    config.read(settingsPath, encoding='utf8')

    config['SETTINGS']['ConanServerPath'] = ConanServerPathNEW
    config['SETTINGS']['ServerName'] = ServerNameNEW
    config['SETTINGS']['ServerRestart'] = ServerRestartNEW
    config['SETTINGS']['MaxPlayers'] = MaxPlayersNEW
    config['SETTINGS']['ServerPort'] = ServerPortNEW
    config['SETTINGS']['SteamPort'] = SteamPortNEW
    config['SETTINGS']['AdminPW'] = AdminPWNEW
    config['SETTINGS']['collection'] = collectionNEW
    config['SETTINGS']['collectionDisable'] = collectionDisableNEW

    with open(settingsPath, 'w', encoding='utf8') as configfile:
        config.write(configfile)

    global ConanServerPath
    global ServerName
    global ServerRestart
    global MaxPlayers
    global ServerPort
    global SteamPort
    global AdminPW
    global collection
    global collectionDisable

    ConanServerPath = ConanServerPathNEW
    ServerName = ServerNameNEW
    ServerRestart = ServerRestartNEW
    MaxPlayers = MaxPlayersNEW
    ServerPort = ServerPortNEW
    SteamPort = SteamPortNEW
    AdminPW = AdminPWNEW
    collection = collectionNEW
    collectionDisable = collectionDisableNEW

    readSettings()


def installServer():
    steamcmd_path = os.path.join(ConanServerPath, '_steamcmd_')
    gameserver_path = os.path.join(ConanServerPath)

    pathlib.Path(ConanServerPath).mkdir(parents=False, exist_ok=True)
    pathlib.Path(steamcmd_path).mkdir(parents=False, exist_ok=True)
    pathlib.Path(gameserver_path).mkdir(parents=False, exist_ok=True)

    steamcmd = pysteamcmd.Steamcmd(steamcmd_path)
    steamcmd.install()
    steamcmd.install_gamefiles(gameid=443030, game_install_dir=gameserver_path, user='anonymous', password=None, validate=True)


    if(collectionDisable == False and collection):

        if('http' in collection):
            collectionID = re.compile(r'(\d+)$').search(collection).group(1)
        else:
            collectionID = collection
        steamModlist = getSteamWorkshopMods.getSteamModsFromCollection(collectionID).getCollectionInfo()
        for mod in steamModlist:
            modID = mod[0]
            steamcmd.install_mods(gameid=440900, game_install_dir=gameserver_path, user='anonymous', password=None, validate=True, modID=modID)

        modListFolder = os.path.join(gameserver_path, 'ConanSandbox', 'Mods')
        modListTXT = os.path.join(modListFolder, 'modlist.txt')
        modRootFolder = os.path.join(gameserver_path, 'steamapps', 'workshop', 'content', '440900')
        if os.path.exists(modListFolder):
            if os.path.isfile(modListTXT):
                pass
            else:
                open(modListTXT, "w+").close()
        else:
            os.mkdir(modListFolder)
            open(modListTXT, "w+").close()

        with open(modListTXT, 'w', encoding='utf8') as modListTXTIO:
            for mod in steamModlist:
                modItemFolder = os.path.join(modRootFolder, mod[0])
                modFileName = os.listdir(modItemFolder)
                modFileName = ''.join(modFileName)
                modFullPath = os.path.join(modItemFolder, modFileName)
                print(modFullPath)
                modListTXTIO.write("*{}\n".format(modFullPath))
    else:
        modListFolder = os.path.join(gameserver_path, 'ConanSandbox', 'Mods')
        modListTXT = os.path.join(modListFolder, 'modlist.txt')

        if os.path.exists(modListFolder):
            if os.path.isfile(modListTXT):
                open(modListTXT, "w").close()
            else:
                pass
        else:
            pass



class waiterThread(QThread):

    def __init__(self, ServerRestart, parent=None):
        QThread.__init__(self)
        self.ServerRestart = ServerRestart
        self.runs = True

    def __del__(self):
        self.wait()

    def stop(self):
        self.runs = False

    def run(self):
        if self.runs:
            ServerRestart = int(self.ServerRestart)
            ServerRestart = int(ServerRestart) * 60
            sleep(ServerRestart)



class StartServerThread(QThread):

    def __init__(self, conanExePath, conanParameters, parent=None):
        QThread.__init__(self)
        self.conanExePath = conanExePath
        self.conanParameters = conanParameters
        self.runs = True

    def __del__(self):
        self.wait()

    def stop(self):
        self.runs = False
        ServerExeName01 = 'ConanSandboxServer'
        ServerExeName02 = 'ConanSandboxServer-Win64-Test'
        for proc in psutil.process_iter():
            # check whether the process name matches
            if ServerExeName01 in proc.name():
                proc.kill()
            if ServerExeName02 in proc.name():
                proc.kill()

    def run(self):
        if self.runs:
            ServerExeName01 = 'ConanSandboxServer'
            ServerExeName02 = 'ConanSandboxServer-Win64-Test'
            for proc in psutil.process_iter():
                # check whether the process name matches
                if ServerExeName01 in proc.name():
                    proc.kill()
                if ServerExeName02 in proc.name():
                    proc.kill()

            conanExePath = str(self.conanExePath)
            conanParameters = str(self.conanParameters)
            installServer()
            serverexec = subprocess.Popen(conanExePath + conanParameters)


def startWindow():
    """Start Main Window UI."""

    m = mainWindow()

    # Show Window
    m.show()

    # Return to stay alive
    return m


def main():
    """Main entry point of the app."""
    # Read Settings
    readSettings()

    # Initialize Qt
    app = QtWidgets.QApplication(sys.argv)

    # Set design and colors
    design.QDarkPalette().set_app(app)

    # Initialize and start Window
    window = startWindow()

    # Set Window Title
    window.setWindowTitle(__title__)

    # Set Window Icon
    window.setWindowIcon(QtGui.QIcon(iconFilePath))

    # Close Window on exit
    sys.exit(app.exec_())


if __name__ == "__main__":
    """This is executed when run from the command line."""
    main()
