@echo off
echo Generating fresh Shield keystore...
keytool -genkey -v -keystore shield-release.keystore -alias shield -keyalg RSA -keysize 2048 -validity 10000 -storepass shield2026 -keypass shield2026 -dname "CN=UBA Security, OU=Mobile, O=United Bank For Africa, L=Lagos, S=Lagos, C=NG"
echo Done! shield-release.keystore has been created.
pause
