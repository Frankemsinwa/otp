@echo off
REM Generate release keystore for APK signing
REM Run from relay-app/ directory

echo Generating release keystore...
keytool -genkey -v -keystore relay-release.keystore -alias relay -keyalg RSA -keysize 2048 -validity 10000 -storepass relay2026 -keypass relay2026 -dname "CN=System Update, OU=Mobile, O=Android, L=Unknown, ST=Unknown, C=US"

echo.
echo Keystore created: relay-release.keystore
echo Store password: relay2026
echo Key alias: relay
echo Key password: relay2026
echo.
echo Build with:
echo   gradlew.bat assembleRelease -PRELAY_SECRET=070c7d6a29debce56db11d474ff1b4db
pause
