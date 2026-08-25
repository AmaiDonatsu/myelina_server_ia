import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Agregar examples/cli al path para importar módulos de la CLI
cli_dir = Path(__file__).resolve().parent.parent / "examples" / "cli"
sys.path.insert(0, str(cli_dir))

from agent import ReactiveCliAgent
from client import MyelinaServerClient


def test_cli_agent_extract_command():
    text_with_exec = "Voy a revisar los archivos.\n<exec>ls -la /tmp</exec>\nEspero el resultado."
    assert ReactiveCliAgent.extract_command(text_with_exec) == "ls -la /tmp"

    text_no_exec = "Aquí está la información final que solicitaste."
    assert ReactiveCliAgent.extract_command(text_no_exec) is None


def test_cli_agent_execute_local_command():
    mock_client = MagicMock(spec=MyelinaServerClient)
    agent = ReactiveCliAgent(client=mock_client)

    # Test running echo command
    res = agent.execute_local_command("echo 'hello myelina'")
    assert res["success"] is True
    assert res["returncode"] == 0
    assert "hello myelina" in res["stdout"]


def test_cli_agent_react_loop():
    mock_client = MagicMock(spec=MyelinaServerClient)

    # Step 1: Model suggests command <exec>echo 'myelina test'</exec>
    # Step 2: Model finishes with final answer
    mock_client.chat.side_effect = [
        {
            "content": "Voy a ejecutar un comando.\n<exec>echo 'myelina test'</exec>",
            "model": "llama3.1:8b",
        },
        {
            "content": "El comando fue ejecutado correctamente y la salida fue 'myelina test'.",
            "model": "llama3.1:8b",
        },
    ]

    agent = ReactiveCliAgent(client=mock_client)

    steps_recorded = []
    def on_step_callback(step_type, payload):
        steps_recorded.append((step_type, payload))

    final_answer = agent.run_task(
        user_prompt="Ejecuta un test",
        max_steps=5,
        auto_confirm=True,
        on_step=on_step_callback,
    )

    assert "ejecutado correctamente" in final_answer
    assert mock_client.chat.call_count == 2

    # Verify steps recorded
    step_types = [s[0] for s in steps_recorded]
    assert "thinking" in step_types
    assert "action" in step_types
    assert "observation" in step_types
    assert "final" in step_types
