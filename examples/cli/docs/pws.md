# Catálogo de Comandos y Guía de Sistema — Windows PowerShell (pwsh)

Este documento define los comandos y cmdlets estándar de PowerShell disponibles para el Agente CLI cuando se ejecuta en entorno Windows.

---

## 1. Navegación y Gestión de Archivos y Carpetas

| Cmdlet / Comando | Alias | Descripción | Ejemplo de Uso |
|---|---|---|---|
| `Get-Location` | `pwd`, `gl` | Muestra la ruta del directorio actual | `Get-Location` |
| `Get-ChildItem -Force` | `ls`, `dir`, `gci` | Lista elementos incluyendo ocultos | `Get-ChildItem -Path . -Force` |
| `Set-Location <ruta>` | `cd`, `sl` | Cambia el directorio de trabajo | `Set-Location -Path "C:\Proyectos"` |
| `New-Item -ItemType Directory` | `mkdir`, `md` | Crea una nueva carpeta | `New-Item -ItemType Directory -Path ".\logs"` |
| `New-Item -ItemType File` | `ni`, `touch` | Crea un archivo nuevo vacío | `New-Item -ItemType File -Path ".\test.txt"` |
| `Copy-Item -Recurse` | `cp`, `copy` | Copia archivos o carpetas recursivamente | `Copy-Item -Path .\src -Destination .\dist -Recurse` |
| `Move-Item` | `mv`, `move` | Mueve o renombra archivos/carpetas | `Move-Item -Path old.txt -Destination new.txt` |
| `Remove-Item -Recurse -Force` | `rm`, `del` | Elimina elementos de forma recursiva | `Remove-Item -Path .\temp -Recurse -Force` |
| `Test-Path <ruta>` | - | Verifica si un archivo o carpeta existe | `Test-Path ".\config.json"` |

---

## 2. Lectura, Edición y Búsqueda en Archivos

| Cmdlet / Comando | Alias | Descripción | Ejemplo de Uso |
|---|---|---|---|
| `Get-Content <archivo>` | `cat`, `gc` | Lee y muestra el contenido de un archivo | `Get-Content -Path .\package.json` |
| `Get-Content -Head <N>` | `head` | Muestra las primeras N líneas | `Get-Content -Path .\server.log -Head 20` |
| `Get-Content -Tail <N>` | `tail` | Muestra las últimas N líneas | `Get-Content -Path .\server.log -Tail 30` |
| `Select-String -Pattern "<txt>"` | `grep`, `sls` | Busca texto en archivos (con número de línea) | `Select-String -Path ".\*.py" -Pattern "SECRET"` |
| `Set-Content -Path <f> -Value <v>` | - | Sobrescribe el contenido de un archivo | `Set-Content -Path ".\.env" -Value "DEBUG=True"` |
| `Add-Content -Path <f> -Value <v>` | - | Agrega texto al final de un archivo | `Add-Content -Path ".\log.txt" -Value "Nuevo evento"` |

---

## 3. Información del Sistema y Procesos

| Cmdlet / Comando | Descripción | Ejemplo de Uso |
|---|---|---|
| `Get-ComputerInfo` | Información detallada del sistema y versión de Windows | `Get-ComputerInfo | Select-Object WindowsProductName, OsVersion` |
| `whoami` | Muestra el usuario actual | `whoami` |
| `Get-Process` | Lista los procesos activos en ejecución | `Get-Process | Sort-Object CPU -Descending | Select-Object -First 10` |
| `Get-Volume` | Muestra el espacio libre y total de unidades de disco | `Get-Volume` |
| `Get-Service` | Lista el estado de los servicios del sistema | `Get-Service | Where-Object Status -eq "Running"` |
| `Get-ChildItem Env:` | Muestra las variables de entorno | `Get-ChildItem Env:` |

---

## 4. Red y Utilidades

| Cmdlet / Comando | Descripción | Ejemplo de Uso |
|---|---|---|
| `Test-NetConnection -ComputerName <host> -Port <port>` | Verifica conectividad a host y puerto | `Test-NetConnection -ComputerName "localhost" -Port 8000` |
| `Invoke-RestMethod -Uri <url>` | Realiza peticiones HTTP REST y parsea JSON | `Invoke-RestMethod -Uri "http://localhost:8000/health"` |
| `Get-NetIPAddress` | Muestra las direcciones IP de la máquina | `Get-NetIPAddress -AddressFamily IPv4` |
| `git status` | Estado del repositorio Git | `git status` |

---

## Reglas para el Agente en PowerShell
1. No utilices comandos interactivos que requieran confirmación manual o TTY sin flags no interactivos.
2. Para ejecutar un comando, envuélvelo en etiquetas `<exec>comando</exec>`.
