import tkinter as tk
from tkinter import messagebox

from app.engine.process_engine import run_process
from app.input.normalizer import normalize_input
from app.output.presenter import render_output
from app.routing.mask_router import choose_mask
from app.session.store import save_session


def analyze_text() -> None:
    raw_text = input_text.get("1.0", tk.END).strip()

    if not raw_text:
        messagebox.showwarning("KODEKS", "Wpisz tekst do analizy.")
        return

    try:
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
    except Exception as exc:
        messagebox.showerror("KODEKS", f"Nie udało się wykonać analizy:\n{exc}")
        return

    result_text.configure(state="normal")
    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, output_text)
    result_text.insert(tk.END, f"\n\nMaska: {selected_mask}")
    result_text.insert(tk.END, f"\nZapis sesji: {session_path}")
    result_text.configure(state="disabled")


root = tk.Tk()
root.title("KODEKS")
root.geometry("900x650")

main_frame = tk.Frame(root, padx=12, pady=12)
main_frame.pack(fill=tk.BOTH, expand=True)

input_label = tk.Label(main_frame, text="Input użytkownika")
input_label.pack(anchor="w")

input_text = tk.Text(main_frame, height=10, wrap=tk.WORD)
input_text.pack(fill=tk.BOTH, expand=True, pady=(4, 10))

analyze_button = tk.Button(main_frame, text="Analizuj", command=analyze_text)
analyze_button.pack(anchor="w", pady=(0, 10))

result_label = tk.Label(main_frame, text="Wynik")
result_label.pack(anchor="w")

result_text = tk.Text(main_frame, height=18, wrap=tk.WORD, state="disabled")
result_text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

root.mainloop()
