#!/usr/bin/env python3
import os
import sys
import argparse
import platform
import getpass
from typing import Dict, Any

from client import MyelinaServerClient
from agent import ReactiveCliAgent


# Códigos de escape ANSI para colores en terminal
class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def print_banner(os_name: str, server_url: str, model: str):
    print(f"{Colors.CYAN}{Colors.BOLD}╔═══════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║           Myelina Reactive CLI Agent (v1.0)               ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print(f"  {Colors.BOLD}Sistema Operativo:{Colors.RESET}  {Colors.GREEN}{os_name}{Colors.RESET}")
    print(f"  {Colors.BOLD}Servidor Backend:{Colors.RESET}   {Colors.BLUE}{server_url}{Colors.RESET}")
    print(f"  {Colors.BOLD}Modelo de IA:{Colors.RESET}       {Colors.YELLOW}{model or 'llama3.1:8b (predeterminado)'}{Colors.RESET}")
    print(f"  {Colors.DIM}Escribe '/help' para ver comandos internos o '/exit' para salir.{Colors.RESET}\n")


def ensure_authentication(client: MyelinaServerClient) -> bool:
    """Verifica si existe un token configurado o asiste al usuario para iniciar sesión."""
    if client.api_key:
        return True

    print(f"{Colors.YELLOW}-!- No se encontró una clave de API configurada.{Colors.RESET}")
    print("Opciones de autenticación:")
    print("  1. Introducir un Token / API Key existente (myelina_...)")
    print("  2. Iniciar sesión con usuario y contraseña (se creará un token automático)")
    print("  3. Salir")

    choice = input(f"\n{Colors.BOLD}Selecciona una opción [1/2/3]: {Colors.RESET}").strip()

    if choice == "1":
        key = input(f"{Colors.BOLD}Ingresa tu API Key: {Colors.RESET}").strip()
        if not key:
            print(f"{Colors.RED}Clave inválida.{Colors.RESET}")
            return False
        client.api_key = key
        return True

    elif choice == "2":
        username = input(f"{Colors.BOLD}Usuario / Email: {Colors.RESET}").strip()
        password = getpass.getpass(f"{Colors.BOLD}Contraseña: {Colors.RESET}")
        try:
            print(f"{Colors.DIM}Iniciando sesión en {client.base_url}...{Colors.RESET}")
            client.login(username, password)
            print(f"{Colors.GREEN}✓ Sesión iniciada con éxito.{Colors.RESET}")

            # Crear token persistente
            token_label = f"cli_{platform.node()}_{platform.system().lower()}"
            print(f"{Colors.DIM}Generando API Key persistente '{token_label}'...{Colors.RESET}")
            token_data = client.create_api_key(label=token_label)
            print(f"{Colors.GREEN}✓ API Key creada: {token_data.get('prefix')}{Colors.RESET}")
            return True
        except Exception as exc:
            print(f"{Colors.RED}X Error al autenticar: {str(exc)}{Colors.RESET}")
            return False

    return False


def create_step_printer(auto_confirm: bool = True):
    """Retorna un callback visual para imprimir el ciclo de razonamiento y ejecución."""
    def on_step(step_type: str, payload: Dict[str, Any]):
        if step_type == "thinking":
            step = payload.get("step", 1)
            print(f"\n{Colors.CYAN}{Colors.BOLD}[Paso {step}] Razonando...{Colors.RESET}")

        elif step_type == "action":
            command = payload.get("command", "")
            print(f"{Colors.YELLOW}{Colors.BOLD}⚡ [Comando sugerido]:{Colors.RESET} {Colors.BOLD}{command}{Colors.RESET}")

            if not auto_confirm:
                confirm = input(f"{Colors.YELLOW}¿Ejecutar este comando en el sistema? [Y/n]: {Colors.RESET}").strip().lower()
                if confirm in ("n", "no"):
                    print(f"{Colors.DIM}(Ejecución cancelada por el usuario){Colors.RESET}")
                    # Inyectar cancelación como fallo de ejecución
                    return

        elif step_type == "observation":
            res = payload.get("result", {})
            code = res.get("returncode", 0)
            status_color = Colors.GREEN if res.get("success") else Colors.RED
            print(f"{status_color}[Salida - Código {code}]:{Colors.RESET}")

            stdout = res.get("stdout", "")
            if stdout:
                # Limitar salida si es gigantesca
                lines = stdout.splitlines()
                if len(lines) > 20:
                    preview = "\n".join(lines[:20]) + f"\n... ({len(lines)-20} líneas más truncadas)"
                else:
                    preview = stdout
                print(f"{Colors.DIM}{preview}{Colors.RESET}")

            if res.get("stderr"):
                print(f"{Colors.RED}X Error: {res['stderr']}{Colors.RESET}")

        elif step_type == "final":
            content = payload.get("content", "")
            print(f"\n{Colors.GREEN}{Colors.BOLD} [Respuesta Final]:{Colors.RESET}")
            print(f"{content}\n")

        elif step_type == "error":
            print(f"{Colors.RED}X Error: {payload.get('message')}{Colors.RESET}\n")

    return on_step


def interactive_loop(agent: ReactiveCliAgent, auto_confirm: bool = True):
    """Bucle REPL interactivo con el usuario."""
    step_printer = create_step_printer(auto_confirm=auto_confirm)

    while True:
        try:
            user_input = input(f"{Colors.BOLD}{Colors.MAGENTA}myelina-cli > {Colors.RESET}").strip()
            if not user_input:
                continue

            # Comandos internos del CLI
            if user_input in ("/exit", "/quit", "exit", "quit"):
                print(f"{Colors.CYAN}¡Hasta pronto!{Colors.RESET}")
                break

            elif user_input in ("/help", "help"):
                print(f"\n{Colors.BOLD}Comandos Disponibles:{Colors.RESET}")
                print("  /help     - Muestra este menú de ayuda")
                print("  /status   - Comprueba la conexión con el servidor y modelos")
                print("  /os       - Muestra el sistema operativo y catálogo de comandos cargado")
                print("  /reset    - Reinicia el contexto de conversación del agente")
                print("  /clear    - Limpia la pantalla de la terminal")
                print("  /exit     - Salir de la aplicación CLI\n")
                continue

            elif user_input == "/reset":
                agent.reset_conversation()
                print(f"{Colors.GREEN}✓ Contexto de conversación reiniciado.{Colors.RESET}\n")
                continue

            elif user_input == "/clear":
                os.system("cls" if os.name == "nt" else "clear")
                continue

            elif user_input == "/status":
                status = agent.client.check_status()
                models = agent.client.list_models()
                print(f"\n{Colors.BOLD}Estado del Servidor:{Colors.RESET} {status}")
                print(f"{Colors.BOLD}Modelos Disponibles:{Colors.RESET} {[m.get('name') for m in models]}\n")
                continue

            elif user_input == "/os":
                os_name, doc = agent._detect_os_and_load_docs()
                print(f"\n{Colors.BOLD}SO Detectado:{Colors.RESET} {os_name}")
                print(f"{Colors.DIM}Líneas de documentación de comandos: {len(doc.splitlines())}{Colors.RESET}\n")
                continue

            # Ejecutar ciclo
            agent.run_task(
                user_prompt=user_input,
                max_steps=6,
                auto_confirm=auto_confirm,
                on_step=step_printer,
            )

        except KeyboardInterrupt:
            print(f"\n{Colors.DIM}(Operación cancelada con Ctrl+C){Colors.RESET}")
        except EOFError:
            print(f"\n{Colors.CYAN}Saliendo...{Colors.RESET}")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Myelina Reactive CLI Agent — Asistente reactivo de terminal para acciones en el SO."
    )
    parser.add_argument(
        "--server",
        default=os.getenv("MYELINA_SERVER_URL", "http://localhost:8000/api/v1"),
        help="URL base del servidor Myelina (por defecto: http://localhost:8000/api/v1)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("MYELINA_API_KEY"),
        help="Token / API Key para autenticación (ej: myelina_...)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("MYELINA_MODEL", "llama3.1:8b"),
        help="Nombre del modelo de IA (por defecto: llama3.1:8b)",
    )
    parser.add_argument(
        "-p", "--prompt",
        help="Ejecuta una sola instrucción y finaliza sin abrir el modo interactivo",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        default=True,
        help="Ejecuta los comandos de forma automática sin pedir confirmación (por defecto: True)",
    )
    parser.add_argument(
        "--ask-confirm",
        action="store_true",
        help="Pide confirmación manual [Y/n] antes de ejecutar cada comando",
    )

    args = parser.parse_args()

    client = MyelinaServerClient(base_url=args.server, api_key=args.token)

    # Detección de SO
    os_name = "Windows (PowerShell)" if platform.system() == "Windows" else f"Linux / Ubuntu ({platform.system()})"

    if not args.prompt:
        print_banner(os_name, client.base_url, args.model)

    # Asegurar autenticación
    if not ensure_authentication(client):
        sys.exit(1)

    agent = ReactiveCliAgent(client=client, model=args.model)
    auto_confirm = not args.ask_confirm

    # Modo ejecución única de prompt (-p / --prompt)
    if args.prompt:
        step_printer = create_step_printer(auto_confirm=auto_confirm)
        agent.run_task(
            user_prompt=args.prompt,
            max_steps=6,
            auto_confirm=auto_confirm,
            on_step=step_printer,
        )
        return

    # Modo REPL interactivo
    interactive_loop(agent, auto_confirm=auto_confirm)


if __name__ == "__main__":
    main()
