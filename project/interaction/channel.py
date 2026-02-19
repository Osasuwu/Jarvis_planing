from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime


class InteractionChannel(ABC):
    @abstractmethod
    def display(self, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def prompt_text(self, prompt: str, allow_interrupt: bool = False) -> str:
        raise NotImplementedError

    @abstractmethod
    def prompt_yes_no(self, prompt: str) -> bool:
        raise NotImplementedError


class CLIChannel(InteractionChannel):
    def display(self, message: str) -> None:
        print(message)

    def prompt_text(self, prompt: str, allow_interrupt: bool = False) -> str:
        value = input(prompt).strip()
        if allow_interrupt and value.lower() == "/interrupt":
            raise KeyboardInterrupt("Human interrupted the meeting.")
        return value

    def prompt_yes_no(self, prompt: str) -> bool:
        while True:
            response = input(prompt).strip().lower()
            if response in {"y", "yes"}:
                return True
            if response in {"n", "no"}:
                return False
            print("Please answer 'y' or 'n'.")


class MinimalUIChannel(InteractionChannel):
    def __init__(self) -> None:
        try:
            import tkinter as tk
            from tkinter import font as tkfont
            from tkinter import scrolledtext
        except ImportError as exc:
            raise RuntimeError("Tkinter is not available in this Python environment.") from exc

        self._tk = tk
        self._tkfont = tkfont
        self._root = tk.Tk()
        self._root.title("Waterfall Kickoff - Planner UI")
        self._root.geometry("1080x720")
        self._root.minsize(900, 620)
        self._root.configure(bg="#f5f7fb")

        self._colors = {
            "bg": "#f5f7fb",
            "panel": "#ffffff",
            "panel_alt": "#eef3fb",
            "text": "#18212f",
            "muted": "#4a5c75",
            "primary": "#2156f3",
            "primary_active": "#1446d9",
            "success": "#2e7d32",
            "danger": "#b3261e",
            "border": "#d7deeb",
            "status_bg": "#e9f2ff",
        }

        self._base_font = self._tkfont.nametofont("TkDefaultFont").copy()
        self._base_font.configure(size=10)
        self._mono_font = self._tkfont.Font(family="Consolas", size=10)

        self._header = tk.Frame(self._root, bg=self._colors["bg"])
        self._header.pack(fill=tk.X, padx=12, pady=(12, 6))

        self._title = tk.Label(
            self._header,
            text="Waterfall Kickoff Assistant",
            anchor="w",
            font=("Segoe UI", 14, "bold"),
            bg=self._colors["bg"],
            fg=self._colors["text"],
        )
        self._title.pack(fill=tk.X)

        self._subtitle = tk.Label(
            self._header,
            text="Track discussion output and submit stakeholder responses.",
            anchor="w",
            justify=tk.LEFT,
            font=self._base_font,
            bg=self._colors["bg"],
            fg=self._colors["muted"],
        )
        self._subtitle.pack(fill=tk.X, pady=(2, 0))

        self._body = tk.Frame(
            self._root,
            bg=self._colors["panel"],
            bd=1,
            relief=tk.SOLID,
            highlightthickness=0,
        )
        self._body.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        self._log = scrolledtext.ScrolledText(
            self._body,
            wrap=tk.WORD,
            height=24,
            font=self._mono_font,
            padx=8,
            pady=8,
            bg="#fcfdff",
            fg=self._colors["text"],
            insertbackground=self._colors["text"],
            relief=tk.FLAT,
            borderwidth=0,
        )
        self._log.pack(fill=tk.BOTH, expand=True)
        self._log.configure(state=tk.DISABLED)

        self._prompt_frame = tk.Frame(
            self._root,
            bg=self._colors["panel_alt"],
            bd=1,
            relief=tk.SOLID,
            highlightthickness=0,
        )
        self._prompt_frame.pack(fill=tk.X, padx=12, pady=(0, 4))

        self._prompt_title = tk.Label(
            self._prompt_frame,
            text="Current prompt",
            anchor="w",
            font=("Segoe UI", 10, "bold"),
            bg=self._colors["panel_alt"],
            fg=self._colors["text"],
        )
        self._prompt_title.pack(fill=tk.X, padx=8, pady=(6, 0))

        self._prompt_label = tk.Label(
            self._prompt_frame,
            text="Waiting for first prompt...",
            anchor="w",
            justify=tk.LEFT,
            wraplength=1020,
            font=self._base_font,
            bg=self._colors["panel_alt"],
            fg=self._colors["text"],
        )
        self._prompt_label.pack(fill=tk.X, padx=8, pady=(2, 8))

        self._input_frame = tk.Frame(self._root, bg=self._colors["bg"])
        self._input_frame.pack(fill=tk.X, padx=12, pady=(0, 6))

        self._response_label = tk.Label(
            self._input_frame,
            text="Your response (Ctrl+Enter to submit)",
            anchor="w",
            font=self._base_font,
            bg=self._colors["bg"],
            fg=self._colors["muted"],
        )
        self._response_label.pack(fill=tk.X)

        self._entry = scrolledtext.ScrolledText(
            self._input_frame,
            wrap=tk.WORD,
            height=4,
            font=self._base_font,
            padx=6,
            pady=6,
            bg="#ffffff",
            fg=self._colors["text"],
            insertbackground=self._colors["text"],
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=0,
        )
        self._entry.pack(fill=tk.X, pady=(2, 0))
        self._entry.bind("<Control-Return>", lambda _event: self._submit())

        self._button_bar = tk.Frame(self._root, bg=self._colors["bg"])
        self._button_bar.pack(fill=tk.X, padx=12, pady=(0, 8))

        self._submit_button = tk.Button(
            self._button_bar,
            text="Submit",
            width=12,
            command=self._submit,
            bg=self._colors["primary"],
            fg="#ffffff",
            activebackground=self._colors["primary_active"],
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=6,
            pady=4,
        )
        self._submit_button.pack(side=tk.LEFT)

        self._yes_button = tk.Button(
            self._button_bar,
            text="Quick Yes",
            width=10,
            command=lambda: self._queue_response("yes"),
            bg="#e9f7ee",
            fg=self._colors["success"],
            activebackground="#d5f0df",
            activeforeground=self._colors["success"],
            relief=tk.FLAT,
            padx=6,
            pady=4,
        )
        self._yes_button.pack(side=tk.LEFT, padx=(6, 0))

        self._no_button = tk.Button(
            self._button_bar,
            text="Quick No",
            width=10,
            command=lambda: self._queue_response("no"),
            bg="#ffeceb",
            fg=self._colors["danger"],
            activebackground="#ffd8d6",
            activeforeground=self._colors["danger"],
            relief=tk.FLAT,
            padx=6,
            pady=4,
        )
        self._no_button.pack(side=tk.LEFT, padx=(6, 0))

        self._interrupt_button = tk.Button(
            self._button_bar,
            text="Interrupt",
            width=10,
            command=lambda: self._queue_response("/interrupt"),
            bg="#f1f4fa",
            fg=self._colors["text"],
            activebackground="#dfe6f3",
            relief=tk.FLAT,
            padx=6,
            pady=4,
        )
        self._interrupt_button.pack(side=tk.LEFT, padx=(6, 0))

        self._clear_button = tk.Button(
            self._button_bar,
            text="Clear Log",
            width=10,
            command=self._clear_log,
            bg="#f1f4fa",
            fg=self._colors["text"],
            activebackground="#dfe6f3",
            relief=tk.FLAT,
            padx=6,
            pady=4,
        )
        self._clear_button.pack(side=tk.RIGHT)

        self._status = tk.Label(
            self._root,
            text="Status: Ready",
            anchor="w",
            bg=self._colors["status_bg"],
            fg=self._colors["muted"],
            padx=8,
            pady=4,
            font=self._base_font,
            bd=1,
            relief=tk.SOLID,
        )
        self._status.pack(fill=tk.X, side=tk.BOTTOM)

        self._pending_response: str | None = None
        self._allow_interrupt = False
        self._expecting_yes_no = False
        self._waiting_for_input = False
        self._closed = False
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_input_state(enabled=False)

        self.display("Minimal UI initialized. Use /interrupt to stop the meeting at any response prompt.")

    def _on_close(self) -> None:
        self._closed = True
        try:
            self._root.destroy()
        except self._tk.TclError:
            pass

    def _set_status(self, text: str) -> None:
        self._status.config(text=f"Status: {text}")

    def _set_input_state(self, enabled: bool, yes_no_enabled: bool = False, interrupt_enabled: bool = False) -> None:
        state = self._tk.NORMAL if enabled else self._tk.DISABLED
        self._entry.configure(state=state)
        self._submit_button.configure(state=self._tk.NORMAL if enabled else self._tk.DISABLED)
        self._yes_button.configure(state=self._tk.NORMAL if (enabled and yes_no_enabled) else self._tk.DISABLED)
        self._no_button.configure(state=self._tk.NORMAL if (enabled and yes_no_enabled) else self._tk.DISABLED)
        self._interrupt_button.configure(state=self._tk.NORMAL if (enabled and interrupt_enabled) else self._tk.DISABLED)

    def _append_log(self, text: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log.configure(state=self._tk.NORMAL)
        self._log.insert(self._tk.END, f"[{timestamp}] {text}\n")
        self._log.see(self._tk.END)
        self._log.configure(state=self._tk.DISABLED)

    def _clear_log(self) -> None:
        self._log.configure(state=self._tk.NORMAL)
        self._log.delete("1.0", self._tk.END)
        self._log.configure(state=self._tk.DISABLED)
        self._set_status("Log cleared")
        if self._waiting_for_input:
            self._append_log("Transcript cleared by user.")

    def _read_entry_text(self) -> str:
        return self._entry.get("1.0", self._tk.END).strip()

    def _reset_entry(self) -> None:
        self._entry.delete("1.0", self._tk.END)

    def _queue_response(self, response: str) -> None:
        if not self._waiting_for_input or self._closed:
            return
        normalized = response.strip()
        if normalized.lower() == "/interrupt" and not self._allow_interrupt:
            return
        self._pending_response = normalized
        self._reset_entry()

    def _submit(self) -> None:
        if self._closed:
            return
        if not self._waiting_for_input:
            return
        value = self._read_entry_text()
        if not value:
            self._set_status("Enter a response before submitting")
            return
        if value.lower() == "/interrupt" and not self._allow_interrupt:
            self._set_status("Interrupt is not available for this prompt")
            return
        self._queue_response(value)

    def _process_events(self) -> None:
        if self._closed:
            return
        try:
            self._root.update_idletasks()
            self._root.update()
        except self._tk.TclError:
            self._closed = True

    def display(self, message: str) -> None:
        if self._closed:
            return
        self._append_log(message)
        self._process_events()

    def prompt_text(self, prompt: str, allow_interrupt: bool = False) -> str:
        if self._closed:
            raise KeyboardInterrupt("UI closed by user.")

        self._prompt_label.config(text=prompt)
        self._append_log(prompt)
        self._allow_interrupt = allow_interrupt
        self._waiting_for_input = True
        self._pending_response = None
        quick_yes_no = self._expecting_yes_no
        self._set_input_state(enabled=True, yes_no_enabled=quick_yes_no, interrupt_enabled=allow_interrupt)
        if quick_yes_no:
            self._response_label.config(text="Your response (use Quick Yes/No or type y/n)")
        else:
            self._response_label.config(text="Your response (Ctrl+Enter to submit)")
        self._set_status("Waiting for your response")
        self._entry.configure(state=self._tk.NORMAL)
        self._entry.focus_set()

        while self._pending_response is None and not self._closed:
            self._process_events()
            time.sleep(0.03)

        if self._closed:
            self._waiting_for_input = False
            self._allow_interrupt = False
            raise KeyboardInterrupt("UI closed by user.")

        response = self._pending_response.strip()
        self._waiting_for_input = False
        self._allow_interrupt = False
        self._set_input_state(enabled=False, yes_no_enabled=False, interrupt_enabled=False)
        self._response_label.config(text="Your response (Ctrl+Enter to submit)")
        self._set_status("Response submitted")
        self._append_log(f"> {response}")
        if allow_interrupt and response.lower() == "/interrupt":
            raise KeyboardInterrupt("Human interrupted the meeting.")
        return response

    def prompt_yes_no(self, prompt: str) -> bool:
        while True:
            self._expecting_yes_no = True
            try:
                response = self.prompt_text(f"{prompt} [y/n]: ", allow_interrupt=False).lower()
            finally:
                self._expecting_yes_no = False
            if response in {"y", "yes"}:
                return True
            if response in {"n", "no"}:
                return False
            self.display("Please answer 'y' or 'n'.")
