#!/usr/bin/env python3
"""
Helper script to install Playwright browsers used by the scrapers.

This script is a convenience wrapper around the Playwright CLI. It does
not run any installation unless you pass --install (or --yes). Default is
to print the command so you can review it first.

Examples:
  # Show the command without running it
  python scripts/install_playwright.py --browsers chromium

  # Run the install for chromium (non-interactive)
  python scripts/install_playwright.py --browsers chromium --yes --with-deps

Note: This requires `playwright` to be installed in the same Python
environment (it's already listed in requirements.txt). The script uses
the current Python interpreter to invoke `python -m playwright install`.
"""
import argparse
import shlex
import subprocess
import sys


def build_command(browsers, with_deps: bool):
    cmd = [sys.executable, "-m", "playwright", "install"]
    if browsers:
        # playwright install accepts space-separated browsers
        cmd.extend(browsers)
    if with_deps:
        cmd.append("--with-deps")
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Playwright browsers for scrapers.")
    parser.add_argument(
        "--browsers",
        nargs="+",
        choices=["chromium", "firefox", "webkit"],
        default=["chromium"],
        help="Which browsers to install (default: chromium)",
    )
    parser.add_argument(
        "--with-deps",
        action="store_true",
        help="On Linux, also install system dependencies where supported",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Run non-interactively (confirm install)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command but don't execute it",
    )

    args = parser.parse_args()

    cmd = build_command(args.browsers, args.with_deps)
    printable = shlex.join(cmd)

    print("Playwright install command:")
    print("  ", printable)

    if args.dry_run:
        print("Dry-run: not executing.")
        return 0

    if not args.yes:
        try:
            ans = input("Run this now? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            return 1
        if ans not in ("y", "yes"):
            print("Aborted by user.")
            return 1

    print("Running:", printable)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print("Playwright install failed:", exc)
        return exc.returncode or 2

    print("Playwright browsers installed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
