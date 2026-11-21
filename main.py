#!/usr/bin/env python3
"""
main.py
-------
Command-line interface for the AES Text Encryptor project.

Student Index Number: 10335136

Usage:
    python main.py encrypt "Hello, world!"
    python main.py decrypt "AES256GCM1:..."
    python main.py menu
    python main.py --help
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path
from typing import Optional, Sequence

import aes_text_cipher as cipher

APP_NAME = "AES Text Encryptor"
__version__ = "1.0.0"
STUDENT_INDEX = "10335136"

BANNER = f"""
============================================================
  {APP_NAME}
  Student Index Number: {STUDENT_INDEX}
  Algorithm: AES-256-GCM + PBKDF2-HMAC-SHA256
============================================================
"""


def _read_password(*, confirm: bool, from_stdin: bool) -> str:
    """Read a password without echoing it, or from stdin for automation."""
    if from_stdin:
        password = sys.stdin.readline()
        if password == "":
            raise cipher.CipherError("No password was received on standard input.")
        return password.rstrip("\r\n")

    if not sys.stdin.isatty():
        raise cipher.CipherError(
            "A hidden password prompt needs an interactive terminal. "
            "Use --password-stdin when piping input."
        )

    password = getpass.getpass("Password: ")
    if confirm:
        confirmation = getpass.getpass("Confirm password: ")
        if password != confirmation:
            raise cipher.CipherError("Passwords do not match.")
    return password


def _emit(text: str, output: Optional[str]) -> None:
    """Write *text* to stdout or to a UTF-8 file."""
    if output:
        path = Path(output)
        path.write_text(text, encoding="utf-8")
        print(f"Saved to {path}", file=sys.stderr)
    else:
        print(text)


def _command_encrypt(args: argparse.Namespace) -> int:
    password = _read_password(
        confirm=not args.password_stdin,
        from_stdin=args.password_stdin,
    )
    token = cipher.encrypt_text(args.text, password)
    _emit(token, args.output)
    return 0


def _command_decrypt(args: argparse.Namespace) -> int:
    password = _read_password(
        confirm=False,
        from_stdin=args.password_stdin,
    )
    plaintext = cipher.decrypt_text(args.token, password)
    _emit(plaintext, args.output)
    return 0


def _interactive_menu() -> int:
    """A small menu that is convenient for a classroom demonstration."""
    print(BANNER)
    try:
        while True:
            print("1) Encrypt text")
            print("2) Decrypt token")
            print("3) Exit")
            choice = input("\nChoose an option [1-3]: ").strip()

            if choice == "1":
                text = input("Text to encrypt: ")
                try:
                    password = _read_password(confirm=True, from_stdin=False)
                    print("\nEncrypted token:\n")
                    print(cipher.encrypt_text(text, password))
                    print()
                except cipher.CipherError as exc:
                    print(f"\nError: {exc}\n", file=sys.stderr)
            elif choice == "2":
                token = input("Token to decrypt: ").strip()
                try:
                    password = _read_password(confirm=False, from_stdin=False)
                    print("\nDecrypted text:\n")
                    print(cipher.decrypt_text(token, password))
                    print()
                except cipher.CipherError as exc:
                    print(f"\nError: {exc}\n", file=sys.stderr)
            elif choice == "3":
                print("\nGoodbye.")
                return 0
            else:
                print("\nPlease choose 1, 2, or 3.\n")
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye.")
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description=(
            f"{APP_NAME} - encrypt and decrypt text with AES-256-GCM. "
            f"Student index number: {STUDENT_INDEX}."
        ),
        epilog=(
            "examples:\n"
            '  python main.py encrypt "Meeting at 10am"\n'
            '  python main.py decrypt "AES256GCM1:..."\n'
            "  python main.py menu\n"
            "  python main.py gui    (or run: python gui.py)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} {__version__} (index {STUDENT_INDEX})",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    encrypt_parser = subparsers.add_parser(
        "encrypt",
        help="encrypt text and print or save the token",
        description="Encrypt text with AES-256-GCM.",
    )
    encrypt_parser.add_argument("text", help="the plaintext to encrypt")
    encrypt_parser.add_argument(
        "-o",
        "--output",
        help="write the token to a UTF-8 file instead of stdout",
    )
    encrypt_parser.add_argument(
        "--password-stdin",
        action="store_true",
        help="read the password from stdin instead of prompting (for scripts)",
    )
    encrypt_parser.set_defaults(handler=_command_encrypt)

    decrypt_parser = subparsers.add_parser(
        "decrypt",
        help="decrypt a token and print or save the text",
        description="Decrypt a token produced by this program.",
    )
    decrypt_parser.add_argument("token", help="the AES256GCM1:... token to decrypt")
    decrypt_parser.add_argument(
        "-o",
        "--output",
        help="write the plaintext to a UTF-8 file instead of stdout",
    )
    decrypt_parser.add_argument(
        "--password-stdin",
        action="store_true",
        help="read the password from stdin instead of prompting (for scripts)",
    )
    decrypt_parser.set_defaults(handler=_command_decrypt)

    menu_parser = subparsers.add_parser(
        "menu",
        help="start the interactive text menu",
        description="Start the interactive text menu.",
    )
    menu_parser.set_defaults(handler=lambda _args: _interactive_menu())

    subparsers.add_parser(
        "gui",
        help="launch the desktop graphical interface",
        description="Launch the Tkinter desktop interface.",
    ).set_defaults(handler=lambda _args: _launch_gui())

    return parser


def _launch_gui() -> int:
    """Import the GUI lazily so the CLI still works on headless machines."""
    try:
        from gui import run_gui
    except ImportError as exc:
        raise cipher.CipherError(
            "The graphical interface could not be loaded. "
            "Make sure Tkinter is installed with your Python distribution."
        ) from exc
    return run_gui()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    try:
        return int(args.handler(args))
    except cipher.CipherError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"File error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
