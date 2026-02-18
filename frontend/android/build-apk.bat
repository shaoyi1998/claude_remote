@echo off
chcp 65001 >nul
set "JAVA_HOME=D:\Program Files\Android\Android Studio\jbr"
set "ANDROID_SDK_ROOT=%LOCALAPPDATA%\Android\Sdk"
D:
cd "D:\pycharm项目\claude_code远程\frontend\android"
call gradlew.bat assembleDebug --no-daemon
