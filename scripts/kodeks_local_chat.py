from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2:1b"
MANIFEST_PATH = (
    Path("/mnt/c/Users/zablo/Desktop/metaFroge/ModelForgeGPT™ ZT&SI x3models lvl")
    / "KODEKS Operator Dawida ZT&SI v1 LOCAL BUILD MANIFEST.json"
)


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {
            "name": "KODEKS Operator Dawida ZT&SI v1",
            "final_instruction_core": (
                "Jestes lokalnym wspoloperatorem PC Dawida. Dzialaj konkretnie, "
                "local-first, bez powierzchownosci. Przy ryzyku pytaj o zgode."
            ),
        }
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def system_prompt(manifest: dict) -> str:
    core = manifest.get("final_instruction_core", "")
    return "\n".join(
        [
            core[:1400],
            "",
            "Tryb lokalny: odpowiadasz jako KODEKS uruchomiony na PC Dawida przez Ollama.",
            "Nie twierdz, ze masz wykonane akcje na plikach, jesli nie dostales wyniku z narzedzia.",
            "Jesli potrzebna jest akcja lokalna, popros Dawida o komende slash albo powiedz konkretnie, co trzeba uruchomic.",
            "Komendy dostepne w tym CLI: /status, /audit, /models, /manifest, /help, /exit.",
            "Styl: po polsku, konkretnie, bracko, bez powierzchownosci.",
            "Zasada: local-first, provider-neutral, prywatne dane zostaja lokalnie.",
        ]
    )


def http_json(url: str, payload: dict | None = None, timeout: float = 240.0) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def ollama_models() -> list[str]:
    try:
        data = http_json(f"{OLLAMA_URL}/api/tags", timeout=5.0)
    except Exception as exc:  # noqa: BLE001 - CLI should report local runtime errors.
        return [f"unavailable: {exc!r}"]
    return [model.get("name", "") for model in data.get("models", []) if model.get("name")]


def run_local(command: list[str]) -> int:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode


def run_status() -> int:
    python = ROOT / ".venv" / "bin" / "python"
    executable = str(python if python.exists() else sys.executable)
    return run_local([executable, "scripts/local_house_status.py"])


def run_audit() -> int:
    python = ROOT / ".venv" / "bin" / "python"
    executable = str(python if python.exists() else sys.executable)
    return run_local([executable, "scripts/local_operator_audit.py"])


def ask_ollama(model: str, messages: list[dict[str, str]]) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.35,
            "num_ctx": 4096,
            "num_predict": 300,
        },
    }
    try:
        data = http_json(f"{OLLAMA_URL}/api/chat", payload=payload)
    except urllib.error.URLError as exc:
        return f"[KODEKS] Ollama nie odpowiada: {exc!r}"
    except Exception as exc:  # noqa: BLE001
        return f"[KODEKS] Blad rozmowy lokalnej: {exc!r}"
    return data.get("message", {}).get("content", "").strip()


def print_help() -> None:
    print(
        "\n".join(
            [
                "",
                "Komendy KODEKS local chat:",
                "  /status    sprawdz zdrowie lokalnego domu",
                "  /audit     uruchom lokalny audyt operatora",
                "  /models    pokaz lokalne modele Ollama",
                "  /manifest  pokaz sciezke manifestu rdzenia",
                "  /help      pokaz pomoc",
                "  /exit      zakoncz",
                "",
            ]
        )
    )


def handle_command(command: str) -> bool:
    if command in {"/exit", "/quit"}:
        return False
    if command == "/help":
        print_help()
    elif command == "/status":
        raise SystemExit(run_status())
    elif command == "/audit":
        raise SystemExit(run_audit())
    elif command == "/models":
        print("\n".join(f"- {name}" for name in ollama_models()))
    elif command == "/manifest":
        print(MANIFEST_PATH)
    else:
        print("Nie znam tej komendy. Wpisz /help.")
    return True


def chat(model: str, once: str | None = None) -> int:
    manifest = load_manifest()
    messages = [{"role": "system", "content": system_prompt(manifest)}]

    print("KODEKS LOCAL CHAT")
    print(f"Model: {model}")
    print("Silnik: Ollama local-first")
    print("Wpisz /help po komendy, /exit aby zakonczyc.")
    print("")

    if once:
        messages.append({"role": "user", "content": once})
        print(ask_ollama(model, messages))
        return 0

    while True:
        try:
            user_text = input("Dawid> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nKODEKS: Zamykam lokalny chat.")
            return 0

        if not user_text:
            continue
        if user_text.startswith("/"):
            if not handle_command(user_text):
                print("KODEKS: Jestem. Zamykam lokalny chat.")
                return 0
            continue

        messages.append({"role": "user", "content": user_text})
        answer = ask_ollama(model, messages)
        messages.append({"role": "assistant", "content": answer})
        print(f"\nKODEKS> {answer}\n")


def health() -> int:
    models = ollama_models()
    print("Ollama models:")
    for model in models:
        print(f"- {model}")
    if not models or models[0].startswith("unavailable:"):
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Local KODEKS chat through Ollama.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name.")
    parser.add_argument("--once", help="Send one message and exit.")
    parser.add_argument("--health", action="store_true", help="Check Ollama availability.")
    args = parser.parse_args()

    if args.health:
        return health()
    return chat(args.model, args.once)


if __name__ == "__main__":
    raise SystemExit(main())
