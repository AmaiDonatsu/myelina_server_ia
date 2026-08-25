import os
import re
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from client import MyelinaServerClient


class ReactiveCliAgent:
    """
    Agente reactivo con bucle ReAct (Reason + Act + Observe).
    Detecta automáticamente el sistema operativo y carga el catálogo de comandos adecuado.
    """

    def __init__(
        self,
        client: MyelinaServerClient,
        model: Optional[str] = None,
        docs_dir: Optional[Path] = None,
    ):
        self.client = client
        self.model = model
        self.os_type = platform.system()  # 'Linux', 'Windows', 'Darwin'
        self.docs_dir = docs_dir or Path(__file__).resolve().parent / "docs"
        self.system_prompt = self._build_system_prompt()
        self.messages: List[Dict[str, str]] = []
        self.reset_conversation()

    def _detect_os_and_load_docs(self) -> tuple[str, str]:
        """Detecta el SO y lee el archivo de comandos correspondiente."""
        if self.os_type == "Windows":
            doc_file = self.docs_dir / "pws.md"
            os_name = "Windows (PowerShell)"
        else:
            doc_file = self.docs_dir / "ubuntu.md"
            os_name = f"Linux / Ubuntu ({self.os_type})"

        doc_content = ""
        if doc_file.exists():
            doc_content = doc_file.read_text(encoding="utf-8")
        else:
            doc_content = f"# Comandos estándar disponibles para {os_name}"

        return os_name, doc_content

    def _build_system_prompt(self) -> str:
        os_name, doc_content = self._detect_os_and_load_docs()
        cwd = os.getcwd()

        prompt = f"""Eres un Agente Asistente Reactivo para acciones y resolución de tareas en la terminal del sistema.

### Contexto del Entorno:
- Sistema Operativo Detectado: {os_name}
- Directorio de Trabajo Actual: {cwd}

### Protocolo de Actuación (ReAct Loop):
1. **Razonar y Decidir:** Analiza la petición del usuario y determina si requieres ejecutar un comando en la terminal para obtener información o realizar una acción.
2. **Ejecutar:** Si necesitas ejecutar un comando en la terminal, DEBES encerrar el comando EXACTO entre las etiquetas `<exec>` y `</exec>`.
   Ejemplo:
   <exec>ls -la</exec>
   o en Windows:
   <exec>Get-ChildItem -Force</exec>
3. **Una sola acción por turno:** Solo incluye UNA etiqueta `<exec>` por respuesta.
4. **Observar y Evaluar:** Una vez que ejecutes el comando, el entorno te responderá con la salida estándar (STDOUT), el error (STDERR) y el código de salida. Revisa si la acción tuvo éxito o falló.
5. **Concluir:** Si ya tienes la información o la tarea fue completada con éxito, NO uses `<exec>` y proporciona tu respuesta final clara y concisa al usuario.

---
### Catálogo de Comandos del Sistema:
{doc_content}
"""
        return prompt

    def reset_conversation(self) -> None:
        """Reinicia el historial de mensajes al estado inicial con el prompt de sistema."""
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]

    @staticmethod
    def extract_command(text: str) -> Optional[str]:
        """Extrae el comando contenido dentro de <exec>...</exec> si existe."""
        match = re.search(r"<exec>(.*?)</exec>", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def execute_local_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Ejecuta un comando en el sistema operativo local y captura el resultado."""
        try:
            # En Windows PowerShell o Linux Bash
            executable = None
            if self.os_type == "Windows":
                # Usar powershell si está disponible
                executable = "powershell.exe"

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                executable=executable,
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Error: Tiempo de espera agotado ({timeout}s) ejecutando el comando.",
            }
        except Exception as exc:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Error inesperado al ejecutar el comando: {str(exc)}",
            }

    def run_task(
        self,
        user_prompt: str,
        max_steps: int = 6,
        auto_confirm: bool = True,
        on_step: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> str:
        """
        Ejecuta el ciclo reactivo hasta completar la tarea o agotar max_steps.
        on_step(step_type, payload): Permite a la interfaz CLI mostrar progresos en tiempo real.
        """
        self.messages.append({"role": "user", "content": user_prompt})

        step = 0
        final_answer = ""

        while step < max_steps:
            step += 1

            if on_step:
                on_step("thinking", {"step": step})

            # 1. Consultar al modelo con el historial actual
            try:
                response = self.client.chat(
                    messages=self.messages,
                    model=self.model,
                    temperature=0.2,
                )
                assistant_content = response.get("content", "")
            except Exception as exc:
                error_msg = f"Error en inferencia de IA: {str(exc)}"
                if on_step:
                    on_step("error", {"message": error_msg})
                return error_msg

            # 2. Registrar respuesta del modelo en el historial
            self.messages.append({"role": "assistant", "content": assistant_content})

            # 3. Extraer posible comando <exec>
            command = self.extract_command(assistant_content)

            if not command:
                # El modelo no solicitó ejecutar ningún comando -> Es la respuesta final
                final_answer = assistant_content
                if on_step:
                    on_step("final", {"content": final_answer})
                break

            # 4. Si hay comando, notificar
            if on_step:
                on_step("action", {"step": step, "command": command, "reasoning": assistant_content})

            # 5. Ejecutar comando (o pedir confirmación)
            exec_result = self.execute_local_command(command)

            if on_step:
                on_step("observation", {"step": step, "result": exec_result})

            # 6. Formatear la observación para que el modelo la analice en el siguiente ciclo
            stdout_text = exec_result["stdout"] or "(sin salida estándar)"
            stderr_text = f"\nSTDERR:\n{exec_result['stderr']}" if exec_result["stderr"] else ""

            observation_content = (
                f"[Resultado de ejecución - Código: {exec_result['returncode']}]\n"
                f"STDOUT:\n{stdout_text}{stderr_text}"
            )

            self.messages.append({"role": "user", "content": observation_content})

        if not final_answer:
            final_answer = "Se alcanzó el límite máximo de pasos sin que el modelo finalizara completamente."

        return final_answer
