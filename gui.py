#!/usr/bin/env python3
"""
gui.py
------
Tkinter desktop interface for the AES Text Encryptor project.

Student Index Number: 10335136

Run with:
    python gui.py
or:
    python main.py gui
"""

from __future__ import annotations

import secrets
import tkinter as tk
from tkinter import messagebox, ttk

import aes_text_cipher as cipher

STUDENT_INDEX = "10335136"
APP_TITLE = "AES Text Encryptor"

# Colour palette
BG = "#eef2f7"
CARD = "#ffffff"
NAVY = "#102a43"
TEXT = "#102a43"
MUTED = "#627d98"
BORDER = "#d9e2ec"
TEAL = "#0f766e"
TEAL_DARK = "#115e59"
FIELD = "#f8fbfd"
SOFT = "#e6f4f1"

FONT = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI Semibold", 10)
FONT_TITLE = ("Segoe UI Semibold", 22)
FONT_MONO = ("Consolas", 10)


class AesTextEncryptorApp:
    """The main application window."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{APP_TITLE} | Index No. {STUDENT_INDEX}")
        self.root.configure(bg=BG)
        self.root.minsize(760, 640)

        self.password_var = tk.StringVar()
        self.show_password_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready.")
        self._buttons: list[tk.Button] = []
        self._busy_widgets: list[tk.Widget] = []
        self._busy = False

        self._configure_styles()
        self._build_ui()
        self._center_window()

        self.root.bind("<Control-Return>", self._encrypt_shortcut)
        self.root.bind("<Control-Shift-Return>", self._decrypt_shortcut)
        self.root.bind("<Escape>", lambda _event: self._clear())
        self.password_entry.focus_set()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Vertical.TScrollbar",
            background=BORDER,
            troughcolor=CARD,
            bordercolor=CARD,
            arrowcolor=MUTED,
        )

    def _build_ui(self) -> None:
        self._build_header()

        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=28, pady=(14, 8))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)
        content.grid_rowconfigure(5, weight=1)

        self._build_password_card(content)
        self._build_input_section(content)
        self._build_actions(content)
        self._build_output_section(content)
        self._build_footer(content)

    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=NAVY, height=104)
        header.pack(fill="x")
        header.pack_propagate(False)

        inner = tk.Frame(header, bg=NAVY)
        inner.pack(fill="both", expand=True, padx=30, pady=17)

        tk.Label(
            inner,
            text=APP_TITLE,
            bg=NAVY,
            fg="#ffffff",
            font=FONT_TITLE,
            anchor="w",
        ).pack(anchor="w")

        subtitle = (
            "AES-256-GCM authenticated encryption  |  "
            f"Student Index No. {STUDENT_INDEX}"
        )
        tk.Label(
            inner,
            text=subtitle,
            bg=NAVY,
            fg="#bcccdc",
            font=FONT_SMALL,
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

    def _build_password_card(self, parent: tk.Frame) -> None:
        card = tk.Frame(
            parent,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)

        inner = tk.Frame(card, bg=CARD)
        inner.grid(row=0, column=0, sticky="ew", padx=16, pady=12)
        inner.grid_columnconfigure(0, weight=1)

        tk.Label(
            inner,
            text="Password",
            bg=CARD,
            fg=TEXT,
            font=FONT_BOLD,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            inner,
            text="At least 8 characters. It is never stored or sent anywhere.",
            bg=CARD,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
        ).grid(row=0, column=1, columnspan=2, sticky="e")

        self.password_entry = tk.Entry(
            inner,
            textvariable=self.password_var,
            show="*",
            font=FONT,
            bg=FIELD,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=TEAL,
        )
        self.password_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), ipady=7)

        show_check = tk.Checkbutton(
            inner,
            text="Show",
            variable=self.show_password_var,
            command=self._toggle_password,
            bg=CARD,
            fg=TEXT,
            activebackground=CARD,
            activeforeground=TEXT,
            selectcolor=CARD,
            font=FONT_SMALL,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        show_check.grid(row=1, column=1, padx=(0, 8))

        generate_button = self._make_button(
            inner,
            "Generate",
            self._generate_password,
            primary=False,
        )
        generate_button.grid(row=1, column=2, sticky="e")

        self.show_check = show_check
        self.generate_button = generate_button
        self._busy_widgets.extend(
            [self.password_entry, show_check, generate_button]
        )

    def _build_input_section(self, parent: tk.Frame) -> None:
        label_row = tk.Frame(parent, bg=BG)
        label_row.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        tk.Label(
            label_row,
            text="Input",
            bg=BG,
            fg=TEXT,
            font=FONT_BOLD,
            anchor="w",
        ).pack(side="left")
        tk.Label(
            label_row,
            text="Plaintext to encrypt, or paste an AES256GCM1 token to decrypt",
            bg=BG,
            fg=MUTED,
            font=FONT_SMALL,
        ).pack(side="left", padx=(10, 0))

        self.input_text = self._make_text_area(parent)
        self.input_text.master.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self._busy_widgets.append(self.input_text)

    def _build_actions(self, parent: tk.Frame) -> None:
        row = tk.Frame(parent, bg=BG)
        row.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        encrypt_button = self._make_button(
            row, "Encrypt", self._encrypt, primary=True
        )
        encrypt_button.pack(side="left")

        decrypt_button = self._make_button(
            row, "Decrypt", self._decrypt, primary=False
        )
        decrypt_button.pack(side="left", padx=(8, 0))

        clear_button = self._make_button(
            row, "Clear", self._clear, primary=False
        )
        clear_button.pack(side="right")

        copy_button = self._make_button(
            row, "Copy result", self._copy_output, primary=False
        )
        copy_button.pack(side="right", padx=(0, 8))

        self._buttons = [encrypt_button, decrypt_button, copy_button, clear_button]
        self._busy_widgets.extend(self._buttons)

    def _build_output_section(self, parent: tk.Frame) -> None:
        label_row = tk.Frame(parent, bg=BG)
        label_row.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        tk.Label(
            label_row,
            text="Result",
            bg=BG,
            fg=TEXT,
            font=FONT_BOLD,
            anchor="w",
        ).pack(side="left")
        tk.Label(
            label_row,
            text="Treat encrypted tokens like passwords; share them only with the password",
            bg=BG,
            fg=MUTED,
            font=FONT_SMALL,
        ).pack(side="left", padx=(10, 0))

        self.output_text = self._make_text_area(parent)
        self.output_text.master.grid(row=5, column=0, sticky="nsew")
        self.output_text.configure(state="disabled", bg=FIELD)

    def _build_footer(self, parent: tk.Frame) -> None:
        status = tk.Label(
            parent,
            textvariable=self.status_var,
            bg=BG,
            fg=TEAL_DARK,
            font=FONT_SMALL,
            anchor="w",
        )
        status.grid(row=6, column=0, sticky="ew", pady=(8, 0))

        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=28, pady=(0, 8))
        tk.Label(
            footer,
            text=f"Student Index Number: {STUDENT_INDEX}",
            bg=BG,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
        ).pack(side="left")
        tk.Label(
            footer,
            text="AES-256-GCM  |  PBKDF2-HMAC-SHA256  |  600,000 iterations",
            bg=BG,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="e",
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------
    def _make_button(
        self,
        parent: tk.Misc,
        text: str,
        command,
        *,
        primary: bool,
    ) -> tk.Button:
        background = TEAL if primary else CARD
        foreground = "#ffffff" if primary else TEXT
        active_background = TEAL_DARK if primary else SOFT
        active_foreground = "#ffffff" if primary else TEXT

        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=background,
            fg=foreground,
            activebackground=active_background,
            activeforeground=active_foreground,
            disabledforeground="#9fb3c8",
            font=FONT_BOLD,
            relief="flat",
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=TEAL if primary else BORDER,
        )

        if not primary:
            button.bind(
                "<Enter>", lambda _event: button.configure(bg=SOFT)
            )
            button.bind(
                "<Leave>", lambda _event: button.configure(bg=CARD)
            )
        return button

    def _make_text_area(self, parent: tk.Misc) -> tk.Text:
        frame = tk.Frame(parent, bg=CARD)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        text = tk.Text(
            frame,
            height=5,
            wrap="word",
            undo=True,
            font=FONT_MONO,
            bg=FIELD,
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground="#b2f5ea",
            selectforeground=TEXT,
            relief="flat",
            bd=0,
            padx=12,
            pady=10,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=TEAL,
        )
        text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=text.yview,
            style="Vertical.TScrollbar",
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scrollbar.set)
        return text

    def _center_window(self) -> None:
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = min(900, max(760, screen_width - 120))
        height = min(760, max(640, screen_height - 80))
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _toggle_password(self) -> None:
        self.password_entry.configure(
            show="" if self.show_password_var.get() else "*"
        )

    def _generate_password(self) -> None:
        password = secrets.token_urlsafe(18)
        self.password_var.set(password)
        self.show_password_var.set(True)
        self._toggle_password()
        self.password_entry.focus_set()
        self.password_entry.select_range(0, tk.END)
        self.status_var.set(
            "Generated a strong random password. Save it before encrypting."
        )

    def _get_input(self) -> str:
        return self.input_text.get("1.0", "end-1c")

    def _set_output(self, value: str) -> None:
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", value)
        self.output_text.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for widget in self._busy_widgets:
            widget.configure(state=state)
        self.root.configure(cursor="watch" if busy else "")
        self.root.update_idletasks()

    def _encrypt(self) -> None:
        if self._busy:
            return
        plaintext = self._get_input()
        if plaintext == "":
            messagebox.showwarning(
                "Nothing to encrypt",
                "Type the text you want to encrypt first.",
                parent=self.root,
            )
            self.input_text.focus_set()
            return

        self._set_busy(True)
        self.status_var.set("Deriving key and encrypting...")
        self.root.update_idletasks()
        try:
            token = cipher.encrypt_text(plaintext, self.password_var.get())
        except cipher.CipherError as exc:
            self.status_var.set("Encryption failed.")
            messagebox.showerror("Encryption failed", str(exc), parent=self.root)
            return
        finally:
            self._set_busy(False)

        self._set_output(token)
        self.status_var.set(
            f"Encrypted successfully. Token length: {len(token)} characters."
        )

    def _decrypt(self) -> None:
        if self._busy:
            return
        token = self._get_input().strip()
        if token == "":
            messagebox.showwarning(
                "Nothing to decrypt",
                "Paste an AES256GCM1 token into the input box first.",
                parent=self.root,
            )
            self.input_text.focus_set()
            return

        self._set_busy(True)
        self.status_var.set("Deriving key and decrypting...")
        self.root.update_idletasks()
        try:
            plaintext = cipher.decrypt_text(token, self.password_var.get())
        except cipher.CipherError as exc:
            self.status_var.set("Decryption failed.")
            messagebox.showerror("Decryption failed", str(exc), parent=self.root)
            return
        finally:
            self._set_busy(False)

        self._set_output(plaintext)
        self.status_var.set(
            f"Decrypted successfully. Plaintext length: {len(plaintext)} characters."
        )

    def _copy_output(self) -> None:
        value = self.output_text.get("1.0", "end-1c")
        if not value:
            messagebox.showinfo(
                "Nothing to copy",
                "There is no result yet. Encrypt or decrypt something first.",
                parent=self.root,
            )
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.status_var.set("Result copied to the clipboard.")

    def _clear(self) -> None:
        if self._busy:
            return
        self.password_var.set("")
        self.show_password_var.set(False)
        self._toggle_password()
        self.input_text.delete("1.0", tk.END)
        self._set_output("")
        self.status_var.set("Cleared. Ready.")
        self.password_entry.focus_set()

    def _encrypt_shortcut(self, _event: tk.Event) -> str:
        self._encrypt()
        return "break"

    def _decrypt_shortcut(self, _event: tk.Event) -> str:
        self._decrypt()
        return "break"


def run_gui() -> int:
    """Create the window and run the Tk event loop."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise cipher.CipherError(f"Could not open a window: {exc}") from exc

    AesTextEncryptorApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run_gui())
    except cipher.CipherError as exc:
        print(f"Error: {exc}")
