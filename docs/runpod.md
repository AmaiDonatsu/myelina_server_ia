## Configurar SSH

Esta guía te lleva desde generar tu llave SSH hasta conectarte por primera vez a un pod de RunPod.

### 1. Generar una nueva llave SSH

En tu terminal local:

```sh
ssh-keygen -t ed25519 -C "tu_correo@ejemplo.com"
```

Te va a preguntar dónde guardarla:

```log
Enter a file in which to save the key (/home/tu_usuario/.ssh/id_ed25519):
```

- Si **no tienes** una llave SSH previa, solo dale **Enter** para aceptar la ruta por default.
- Si **ya tienes** una llave SSH que no quieres sobreescribir (por ejemplo, la usas para GitHub u otro servicio), escribe un nombre distinto para esta llave nueva:

```log
Enter a file in which to save the key (/home/tu_usuario/.ssh/id_ed25519): runpod_ssh
```

Después te va a pedir una passphrase (contraseña extra para la llave). Puedes dejarla vacía dando Enter dos veces, o ponerle una si quieres una capa extra de seguridad.

Al terminar, vas a tener **dos archivos** nuevos en `~/.ssh/`:
- `runpod_ssh` (o `id_ed25519`) — tu llave **privada**, nunca la compartas ni la subas a ningún lado
- `runpod_ssh.pub` (o `id_ed25519.pub`) — tu llave **pública**, esta sí se comparte/sube

### 2. Verificar permisos de la llave

SSH es estricto con los permisos de estos archivos, si no, se rehúsa a usarlos:

```sh
chmod 600 ~/.ssh/runpod_ssh
chmod 644 ~/.ssh/runpod_ssh.pub
```

### 3. Copiar tu llave pública

Muestra el contenido de tu llave pública en la terminal:

```sh
cat ~/.ssh/runpod_ssh.pub
```

Vas a ver algo como:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx tu_correo@ejemplo.com
```

Copia **toda la línea completa**.


--------

## En Runpod
- Igual que en github, el primer paso para poder conectarse y trabajar con runpod, es registrando tu clave ssh pública, ya que, ssh el es estándar de la industria para conectarse y usar hardware remoto.


- Primero Navega a account/credentials y seleccionar ssh public keys.
<img src='../media/ssh_runpod.png'/>
y añadir la nueva clave ssh

ahí pegarás la clave pública creada anteriormente.

### Correr un modelo

El primer paso para usar RunPod es probar un template ya listo con todo lo necesario para inferencia.

Un modelo de lenguaje, en su forma más pura, solo sabe hacer una cosa: predecir cuál es el siguiente
"token" (pedazo de texto) más probable, dado el texto que lleva hasta ahora. No tiene ningún concepto
nativo de "esto lo dijo el sistema", "esto lo dijo el usuario", etc. — todo eso es una convención que
se le enseña durante su entrenamiento.

Por eso, cuando queremos usarlo para "chatear", necesitamos una capa que traduzca nuestra estructura
de conversación a algo que el modelo sí entienda. Y aquí está lo interesante: **cada familia de
modelos espera un formato distinto.**

Como desarrolladores, lo más común es preparar nuestros mensajes con el formato clásico de roles:

```json
[
    {
        "role": "system",
        "content": "Eres un asistente muy útil de programación e ingeniero en sistemas..."
    },
    {
        "role": "user",
        "content": "Tux se escapó y asaltó una pescadería, ¿qué hacemos?"
    }
]
```

Pero un modelo como Llama 3.1, por dentro, en realidad espera algo así:

```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Eres un asistente muy útil de programación...<|eot_id|><|start_header_id|>user<|end_header_id|>

Tux se escapó y asaltó una pescadería...<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

Y otro modelo, como Qwen, espera un formato completamente distinto (ChatML), con sus propios tokens
especiales. Si le mandaras el formato de Llama a Qwen (o viceversa), el modelo se confundiría —
nunca vio esos tokens en su entrenamiento.

**Aquí es donde entra Ollama**: se encarga de detectar qué modelo tienes cargado y traducir
automáticamente tu JSON de roles al formato exacto que ese modelo espera, sin que tú tengas que
preocuparte por memorizar el formato de cada familia de modelos.

---

Para comenzar a trabajar con ollama desde runpod primero:

- En la sección hub, buscar el template ollama

<img src="../media/ollama_template.png" />

ir a configure pod
<img src="../media/configure.png" />


- Seleccionar una gpu

<img src="../media/select_gpu.png" />


- Ultimas configuraciones y deploy
<img src="../media/deploy.png" />


## De vuelta en la terminal 

-  conectar vía ssh
```sh
ssh tu_codigo@ssh.runpod.io -i ~/.ssh/runpod_ssh
```

-  Verifica que Ollama esté corriendo
```sh
ollama list
``` 
- no bloquear terminal
```sh
ollama serve &
```
-  
```sh
export OLLAMA_MODELS=/workspace/ollama_models
mkdir -p /workspace/ollama_models
```

- descargar modelo  
```sh
ollama pull llama3.1:8b
```

- correr llama para probar
```sh
ollama run llama3.1:8b
```

