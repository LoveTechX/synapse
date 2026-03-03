"""
PHASE 5: Interactive CLI Interface
Rich command-line interface for user control and queries.
Commands: explain, preview, auto, manual, history, status, etc.
"""

import os
from typing import Optional, List
from storage.decision_log import (
    get_decision_log,
    get_decisions_by_file,
    print_log_summary,
)
from ui.preview_mode import preview_mode


class CLIInterface:
    """Interactive CLI for file organizer control."""

    def __init__(self):
        self.running = True
        self.mode = "auto"  # "auto" | "manual" | "preview"

    def show_banner(self) -> None:
        """Show welcome banner."""
        print("\n" + "=" * 70)
        print("🚀 SMART AUTONOMOUS FILE ORGANIZER - Interactive CLI")
        print("=" * 70)
        print("Type 'help' for available commands")
        print("=" * 70 + "\n")

    def show_help(self) -> None:
        """Display help for all commands."""
        help_text = """
╔════════════════════════════════════════════════════════════════════╗
║                           AVAILABLE COMMANDS                       ║
╔════════════════════════════════════════════════════════════════════╗

OPERATIONAL MODES:
  auto              │ Enable automatic mode (files moved silently)
  manual            │ Enable manual mode (all files require approval)
  preview           │ Enable preview mode (show decisions, no moves)
  status            │ Show current operating mode and settings

FILE INTELLIGENCE:
  explain <file>    │ Detailed explanation for why file was handled
  search <pattern>  │ Search decision log for files matching pattern
  history           │ Show recent processing decisions
  summary           │ Display statistics and summary

CONFIGURATION:
  config show       │ Display current configuration
  config threshold  │ Adjust confidence threshold for auto-approval
  config rules      │ Show current rules and mappings

SYSTEM:
  help              │ Show this help message
  exit / quit       │ Exit the application

EXAMPLES:
  >>> explain CPU Scheduling.pdf
  >>> search "operating systems"
  >>> auto
  >>> preview
  >>> summary

╚════════════════════════════════════════════════════════════════════╝
"""
        print(help_text)

    def parse_command(self, user_input: str) -> tuple:
        """
        Parse user input into command and arguments.

        Returns:
            (command, args)
        """
        parts = user_input.strip().split(maxsplit=1)
        if not parts:
            return None, []

        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        return command, args

    def handle_explain(self, file_name: str) -> None:
        """Explain decision for a specific file."""
        if not file_name.strip():
            print("❌ Please provide a filename")
            return

        log = get_decisions_by_file(file_name)

        if not log:
            print(f"❌ No decisions found for '{file_name}'")
            return

        print(f"\n📋 Explanation(s) for: {file_name}")
        print("=" * 70)

        for entry in log:
            timestamp = entry.get("timestamp", "N/A")
            action = entry.get("action", "unknown").upper()
            reason = entry.get("reason", "Unknown reason")
            category = entry.get("category", "N/A")
            subject = entry.get("subject", "N/A")
            destination = entry.get("destination", "N/A")
            confidence = entry.get("confidence")

            print(f"\n📅 {timestamp}")
            print(f"   Action:      {action}")
            print(f"   Category:    {category}")
            if subject and subject != "N/A":
                print(f"   Subject:     {subject}")
            print(f"   Reason:      {reason}")
            if confidence is not None and confidence >= 0:
                print(f"   Confidence:  {confidence*100:.0f}%")
            if destination and destination != "N/A":
                print(f"   Destination: {destination}")
            print("-" * 70)

    def handle_search(self, pattern: str) -> None:
        """Search decision log for matching files."""
        if not pattern.strip():
            print("❌ Please provide a search pattern")
            return

        log = get_decision_log()
        pattern_lower = pattern.lower()

        results = [
            entry
            for entry in log
            if pattern_lower in entry.get("file", "").lower()
            or pattern_lower in entry.get("reason", "").lower()
        ]

        if not results:
            print(f"❌ No matches found for '{pattern}'")
            return

        print(f"\n🔍 Search Results: {len(results)} match(es)")
        print("=" * 70)

        for entry in results:
            file_name = entry.get("file")
            action = entry.get("action")
            timestamp = entry.get("timestamp", "").split("T")[0]
            reason = entry.get("reason", "")[:50]

            icon = "✓" if action == "moved" else "✗" if action == "skipped" else "⊙"
            print(f"{icon} [{timestamp}] {file_name:30s} → {reason}...")

    def handle_history(self, limit: int = 10) -> None:
        """Show recent decision history."""
        log = get_decision_log()

        if not log:
            print("❌ No decision history available")
            return

        recent = log[-limit:] if limit > 0 else log
        recent.reverse()  # Most recent first

        print(f"\n📜 Recent Decisions (last {len(recent)})")
        print("=" * 70)

        for entry in recent:
            file_name = entry.get("file", "unknown")
            action = entry.get("action", "unknown")
            category = entry.get("category", "")
            timestamp = entry.get("timestamp", "")[:19]

            if action == "moved":
                icon, style = "✓", "MOVED"
            elif action == "skipped":
                icon, style = "✗", "SKIPPED"
            elif action == "duplicate":
                icon, style = "⊙", "DUPLICATE"
            else:
                icon, style = "!", "ERROR"

            print(f"{icon} {timestamp} | {style:10s} | {file_name:30s} | {category}")

    def handle_summary(self) -> None:
        """Show statistics summary."""
        print_log_summary()

    def handle_mode_change(self, new_mode: str) -> None:
        """Change operating mode."""
        new_mode = new_mode.lower()

        if new_mode == "auto":
            self.mode = "auto"
            preview_mode.disable()
            print("✓ Switched to AUTO mode - files will be moved silently")

        elif new_mode == "manual":
            self.mode = "manual"
            preview_mode.disable()
            print("✓ Switched to MANUAL mode - all files require user confirmation")

        elif new_mode == "preview":
            self.mode = "preview"
            preview_mode.enable()
            print("✓ Switched to PREVIEW mode - decisions shown without moving files")

        else:
            print(f"❌ Unknown mode: {new_mode}")
            print("   Available: auto | manual | preview")

    def handle_status(self) -> None:
        """Show current status and settings."""
        print("\n" + "=" * 70)
        print("📊 SYSTEM STATUS")
        print("=" * 70)
        print(f"Operating Mode:     {self.mode.upper()}")
        print(
            f"Preview Mode:       {'ENABLED' if preview_mode.is_enabled() else 'DISABLED'}"
        )

        log = get_decision_log()
        print(f"Total Decisions:    {len(log)}")

        if log:
            moved = len([e for e in log if e.get("action") == "moved"])
            skipped = len([e for e in log if e.get("action") == "skipped"])
            duplicates = len([e for e in log if e.get("action") == "duplicate"])
            print(f"  - Moved:         {moved}")
            print(f"  - Skipped:       {skipped}")
            print(f"  - Duplicates:    {duplicates}")

        print("=" * 70 + "\n")

    def process_command(self, command: str, args: str) -> None:
        """Process a user command."""

        if command in {"help", "h", "?"}:
            self.show_help()

        elif command in {"exit", "quit", "q"}:
            self.running = False
            print("\n👋 Goodbye!")

        elif command == "auto":
            self.handle_mode_change("auto")

        elif command == "manual":
            self.handle_mode_change("manual")

        elif command == "preview":
            self.handle_mode_change("preview")

        elif command == "status":
            self.handle_status()

        elif command == "explain":
            self.handle_explain(args)

        elif command == "search":
            self.handle_search(args)

        elif command == "history":
            limit = int(args) if args.isdigit() else 10
            self.handle_history(limit)

        elif command == "summary":
            self.handle_summary()

        elif command == "config":
            if args.lower() == "show":
                print("\n⚙️  Configuration:\n")
                print("Confidence Threshold (auto):     80%")
                print("Confidence Threshold (confirm):  60%")
                print("Confidence Threshold (reject):   40%")
                print("Semantic Model:                  all-mpnet-base-v2")
                print(
                    "Decision Log:                    D:/AUTOMATION/decision_log.json"
                )
                print()
            else:
                print("❌ Unknown config subcommand")

        elif command == "":
            pass  # Empty input

        else:
            print(f"❌ Unknown command: {command}")
            print("   Type 'help' for available commands")

    def run(self) -> None:
        """Start the interactive CLI."""
        self.show_banner()

        while self.running:
            try:
                user_input = input("organizer> ").strip()

                if not user_input:
                    continue

                command, args = self.parse_command(user_input)

                if command:
                    self.process_command(command, args)

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted")
                self.running = False

            except Exception as e:
                print(f"❌ Error: {e}")


# Global CLI instance
def start_cli_interface():
    """Start the interactive CLI."""
    cli = CLIInterface()
    cli.run()
