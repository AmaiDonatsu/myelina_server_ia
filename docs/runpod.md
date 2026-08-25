Connect with run pod

- 1 conectar vía ssh
```sh
ssh tu_codigo@ssh.runpod.io -i ~/.ssh/tu_ssh
```

- 2 Verifica que Ollama esté corriendo
```sh
ollama list
``` 
- 3 no bloquear terminal
```sh
ollama serve &
```
- 4 
```sh
export OLLAMA_MODELS=/workspace/ollama_models
mkdir -p /workspace/ollama_models
```

- 5 descargar modelo  
```sh
ollama pull llama3.1:8b
```

- 6 correr llama para probar
```sh
ollama run llama3.1:8b
```

