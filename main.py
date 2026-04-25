from app.input.normalizer import normalize_input
from app.routing.mask_router import choose_mask
from app.engine.process_engine import run_process
from app.output.presenter import render_output
from app.session.store import save_session


def main() -> None:
    raw_text = input("KODEKS > ").strip()

    if not raw_text:
        print("Brak danych wejściowych. Wpisz tekst i uruchom ponownie.")
        return

    normalized = normalize_input(raw_text)
    selected_mask, route_reason = choose_mask(normalized)
    process_result = run_process(normalized, selected_mask)
    output_text = render_output(process_result)
    session_path = save_session(
        raw_input=raw_text,
        normalized_input=normalized,
        selected_mask=selected_mask,
        route_reason=route_reason,
        process_result=process_result,
        output_text=output_text,
    )

    print()
    print("=== WYNIK KODEKS ===")
    print(output_text)
    print()
    print(f"Maska: {selected_mask}")
    print(f"Zapis sesji: {session_path}")


if __name__ == "__main__":
    main()
