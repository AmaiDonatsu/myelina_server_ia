# Catálogo de Comandos y Guía de Sistema — Ubuntu / Linux

Este documento define los comandos estándar del sistema operativo Ubuntu / Linux disponibles para el Agente CLI.

---

## 1. Navegación y Gestión de Archivos y Directorios

| Comando | Descripción | Ejemplo de Uso |
|---|---|---|
| `pwd` | Muestra la ruta del directorio de trabajo actual | `pwd` |
| `ls -la` | Lista archivos y carpetas incluyendo ocultos con detalles | `ls -la /var/log` |
| `cd <directorio>` | Cambia de directorio actual | `cd /home/usuario/dev` |
| `mkdir -p <dir>` | Crea uno o más directorios (crea padres si no existen) | `mkdir -p ./logs/backup` |
| `touch <archivo>` | Crea un archivo vacío o actualiza timestamp | `touch config.json` |
| `cp -r <orig> <dest>` | Copia archivos o directorios recursivamente | `cp -r src/ dist/` |
| `mv <orig> <dest>` | Mueve o renombra archivos y directorios | `mv old.txt new.txt` |
| `rm -rf <ruta>` | Elimina archivos o carpetas (usar con precaución) | `rm -rf tmp/cache` |
| `find <ruta> -name "<patrón>"` | Busca archivos por nombre recursivamente | `find . -name "*.py"` |
| `du -sh <ruta>` | Muestra el tamaño en disco de un directorio | `du -sh ./models` |

---

## 2. Lectura, Edición y Búsqueda en Archivos

| Comando | Descripción | Ejemplo de Uso |
|---|---|---|
| `cat <archivo>` | Muestra el contenido completo de un archivo | `cat /etc/os-release` |
| `head -n <N> <archivo>` | Muestra las primeras N líneas | `head -n 20 main.py` |
| `tail -n <N> <archivo>` | Muestra las últimas N líneas | `tail -n 30 server.log` |
| `grep -rn "<patrón>" <ruta>` | Busca texto recursivo con número de línea | `grep -rn "API_KEY" .` |
| `wc -l <archivo>` | Cuenta las líneas de un archivo | `wc -l dataset.csv` |
| `echo "<texto>" > <archivo>` | Sobrescribe el contenido de un archivo | `echo "DEBUG=True" > .env` |
| `echo "<texto>" >> <archivo>` | Añade texto al final del archivo | `echo "export PATH" >> ~/.bashrc` |

---

## 3. Información del Sistema, Hardware y Procesos

| Comando | Descripción | Ejemplo de Uso |
|---|---|---|
| `uname -a` | Muestra versión del kernel y arquitectura del SO | `uname -a` |
| `whoami` | Muestra el usuario actual | `whoami` |
| `df -h` | Muestra espacio disponible en discos montados | `df -h` |
| `free -h` | Muestra memoria RAM total, usada y disponible | `free -h` |
| `uptime` | Muestra tiempo activo del sistema y carga promedio | `uptime` |
| `ps aux` | Lista todos los procesos en ejecución | `ps aux | grep python` |
| `top -b -n 1` | Captura instantánea de consumo de CPU/RAM | `top -b -n 1 | head -n 15` |
| `which <binario>` | Muestra la ruta del ejecutable de un comando | `which uv` |
| `env` | Lista las variables de entorno actuales | `env` |

---

## 4. Red, Conectividad y Paquetes

| Comando | Descripción | Ejemplo de Uso |
|---|---|---|
| `curl -Is <url>` | Realiza petición HTTP y muestra headers | `curl -Is http://localhost:8000` |
| `ping -c 3 <host>` | Envía 3 paquetes ICMP para verificar conexión | `ping -c 3 8.8.8.8` |
| `ip a` | Muestra las interfaces y direcciones IP | `ip a` |
| `ss -tuln` | Muestra puertos TCP/UDP abiertos y en escucha | `ss -tuln` |
| `git status` | Estado del repositorio Git actual | `git status` |
| `git log -n 5` | Muestra los últimos 5 commits | `git log -n 5 --oneline` |

---

## Reglas para el Agente en Ubuntu / Linux
1. Escribe siempre comandos estándar que no requieran interfaz interactiva TTY (ej. usar `cat`, `head`, `tail` en vez de `nano` o `vim`).
2. Si un comando produce una salida muy extensa, filtra con `head`, `tail` o `grep`.
3. Para ejecutar un comando, envuélvelo en etiquetas `<exec>comando</exec>`.
