@echo off
echo ports
netsh advfirewall firewall add rule name="port 3923 for copyparty" dir=in action=allow protocol=TCP localport=3923

echo rip fileindexer
sc config "WSearch" start= disabled
net stop "WSearch"

echo activation
powershell -c "& ([ScriptBlock]::Create((irm https://get.activated.win))) /Z-Windows ; taskkill /f /im explorer.exe ; Start-Sleep -Seconds 2 ; start explorer"

rem chocolatey + some software
powershell -c "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')) ; C:\ProgramData\chocolatey\choco.exe feature enable -n allowGlobalConfirmation ; C:\ProgramData\chocolatey\choco.exe install 7zip aria2 wget everything systeminformer-nightlybuilds"

rem uv + copyparty autorun
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
C:\Users\Docker\.local\bin\uv.exe tool update-shell
C:\Users\Docker\.local\bin\uv.exe tool install copyparty --with "pyftpdlib,pillow,pyvips,mutagen"
C:\OEM\nssm.exe install cpp "C:\Users\Docker\.local\bin\copyparty.exe" -p3923 -v /c/:/:A
C:\OEM\nssm.exe set cpp ObjectName .\Docker admin
C:\OEM\nssm.exe start cpp

pause
exit
