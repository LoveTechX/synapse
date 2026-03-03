import json
import os
import sys
from datetime import datetime

try:
    from prompt_toolkit import HTML, PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import Completer, Completion, ThreadedCompleter
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.shortcuts import print_formatted_text
    from prompt_toolkit.styles import Style
except ImportError as e:
    raise ImportError(
        "prompt_toolkit is required. Install it with: pip install prompt_toolkit"
    ) from e

from realtime_organizer import initial_scan, undo_last_move
from ai.semantic_memory import search_knowledge
from suggestion_engine import SuggestionEngine


MOVE_HISTORY_PATH = "D:/AUTOMATION/move_history.json"
PROMPT_HISTORY_PATH = "D:/AUTOMATION/jarvis_prompt_history.txt"
RECENT_LIMIT = 10


class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    BOLD = "\033[1m"


def ctext(text, color):
    return f"{color}{text}{Colors.RESET}"


def cprint(text):
    print_formatted_text(ANSI(text))


def print_header(title):
    cprint(ctext(f"\n{title}", Colors.BOLD + Colors.CYAN))
    cprint(ctext("-" * len(title), Colors.CYAN))


def _format_score(item):
    distance = item.get("distance")
    if distance is None:
        return "N/A"
    return f"{float(distance):.4f}"


def _format_snippet(item, max_len=180):
    text = (item.get("chunk_text") or "").replace("\n", " ").strip()
    if len(text) <= max_len:
        return text or "(no snippet)"
    return text[: max_len - 3] + "..."


def _load_move_history():
    if not os.path.exists(MOVE_HISTORY_PATH):
        return []
    try:
        with open(MOVE_HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        cprint(ctext(f"Failed to read move history: {e}", Colors.RED))
        return []


def _open_with_default_app(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    if hasattr(os, "startfile"):
        os.startfile(path)  # type: ignore[attr-defined]
        return
    raise OSError("Default file opener is not available on this OS.")


class JarvisCompleter(Completer):
    def __init__(self, engine, commands):
        self.engine = engine
        self.commands = commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        stripped = text.lstrip()
        parts = stripped.split()

        if not parts or (len(parts) == 1 and not stripped.endswith(" ")):
            prefix = parts[0].lower() if parts else ""
            for cmd in self.engine.get_command_suggestions(prefix, self.commands):
                yield Completion(
                    cmd,
                    start_position=-len(prefix),
                    display_meta="command",
                    style="fg:#00d7ff",
                )
            return

        command = parts[0].lower()
        if command not in {"find", "open"}:
            return

        query_start = stripped.find(" ")
        query_text = stripped[query_start + 1 :] if query_start >= 0 else ""
        query_prefix = query_text.lstrip()

        for suggestion in self.engine.get_query_suggestions(command, query_prefix):
            yield Completion(
                suggestion,
                start_position=-len(query_prefix),
                display_meta="semantic",
                style="fg:#5fd787",
            )


class JarvisCLI:
    def __init__(self):
        self.engine = SuggestionEngine()
        self.commands = {
            "find": self.cmd_find,
            "open": self.cmd_open,
            "organize": self.cmd_organize,
            "undo": self.cmd_undo,
            "recent": self.cmd_recent,
            "help": self.cmd_help,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
        }
        self.style = Style.from_dict(
            {
                "prompt": "ansicyan bold",
            }
        )
        self.session = PromptSession(
            history=FileHistory(PROMPT_HISTORY_PATH),
            completer=ThreadedCompleter(
                JarvisCompleter(self.engine, list(self.commands.keys()))
            ),
            complete_while_typing=True,
            auto_suggest=AutoSuggestFromHistory(),
        )

    def parse_and_run(self, raw):
        parts = raw.split()
        cmd = parts[0].lower()
        args = parts[1:]
        handler = self.commands.get(cmd)
        if handler is None:
            cprint(ctext(f"Unknown command: {cmd}", Colors.YELLOW))
            return
        handler(args)

    def cmd_find(self, args):
        query = " ".join(args).strip()
        if not query:
            cprint(ctext("Usage: find <query>", Colors.YELLOW))
            return

        self.engine.record_search(query)
        results = search_knowledge(query)

        print_header("Semantic Search Results")
        if not results:
            cprint(ctext("No results found.", Colors.YELLOW))
            return

        for i, item in enumerate(results, 1):
            cprint(ctext(f"[{i}] {item.get('file_path', 'Unknown file')}", Colors.GREEN))
            cprint(f"    Snippet: {_format_snippet(item)}")
            cprint(
                ctext(
                    f"    Similarity score (distance): {_format_score(item)}",
                    Colors.MAGENTA,
                )
            )

    def cmd_open(self, args):
        query = " ".join(args).strip()
        if not query:
            cprint(ctext("Usage: open <query>", Colors.YELLOW))
            return

        self.engine.record_search(query)
        results = search_knowledge(query, top_k=5)
        if not results:
            cprint(ctext("No matching files found.", Colors.YELLOW))
            return

        best = None
        for item in results:
            file_path = item.get("file_path")
            if file_path and os.path.exists(file_path):
                best = item
                break

        if best is None:
            cprint(ctext("Found matches, but no existing file path to open.", Colors.YELLOW))
            return

        file_path = best["file_path"]
        try:
            _open_with_default_app(file_path)
            self.engine.record_file_access(file_path)
            cprint(ctext(f"Opened: {file_path}", Colors.GREEN))
        except Exception as e:
            cprint(ctext(f"Failed to open file: {e}", Colors.RED))

    def cmd_organize(self, _args):
        print_header("Organizer")
        try:
            initial_scan()
            cprint(ctext("Organize scan completed.", Colors.GREEN))
        except Exception as e:
            cprint(ctext(f"Organizer scan failed: {e}", Colors.RED))

    def cmd_undo(self, _args):
        print_header("Undo Last Move")
        try:
            success = undo_last_move()
            if success:
                cprint(ctext("Undo completed.", Colors.GREEN))
            else:
                cprint(ctext("No move undone.", Colors.YELLOW))
        except Exception as e:
            cprint(ctext(f"Undo failed: {e}", Colors.RED))

    def cmd_recent(self, _args):
        print_header("Recent Moves")
        history = _load_move_history()
        if not history:
            cprint(ctext("No move history found.", Colors.YELLOW))
            return

        recent_entries = history[-RECENT_LIMIT:][::-1]
        for i, entry in enumerate(recent_entries, 1):
            timestamp = entry.get("timestamp", "Unknown time")
            src = entry.get("file_path", "Unknown source")
            dst = entry.get("destination", "Unknown destination")
            category = entry.get("category", "N/A")
            subject = entry.get("subject", "N/A")

            cprint(ctext(f"[{i}] {timestamp}", Colors.GREEN))
            cprint(f"    From: {src}")
            cprint(f"    To:   {dst}")
            cprint(ctext(f"    Category: {category} | Subject: {subject}", Colors.MAGENTA))

    def cmd_help(self, _args):
        print_header("Commands")
        cprint("  find <query>   - Search semantic memory")
        cprint("  open <query>   - Open best-matching file")
        cprint("  organize       - Run organizer initial scan")
        cprint("  undo           - Undo last moved file")
        cprint("  recent         - Show last 10 moved files")
        cprint("  help           - Show this help")
        cprint("  exit / quit    - Close Jarvis")

    @staticmethod
    def cmd_exit(_args):
        cprint(ctext("Exiting Jarvis.", Colors.CYAN))
        raise SystemExit(0)

    def run(self):
        cprint(
            ctext(
                "Jarvis interactive CLI ready. Press Tab for suggestions and arrows to navigate.",
                Colors.CYAN,
            )
        )
        cprint(ctext("Type 'help' for commands.", Colors.CYAN))

        while True:
            try:
                raw = self.session.prompt(
                    HTML("<prompt>Jarvis &gt; </prompt>"),
                    style=self.style,
                ).strip()
                if not raw:
                    continue
                self.parse_and_run(raw)
            except KeyboardInterrupt:
                cprint("")
                cprint(ctext("Interrupted. Type 'exit' to quit.", Colors.YELLOW))
            except EOFError:
                cprint("")
                self.cmd_exit([])
            except SystemExit:
                raise
            except Exception as e:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cprint(ctext(f"[{timestamp}] Command failed: {e}", Colors.RED))


def run():
    app = JarvisCLI()
    app.run()


if __name__ == "__main__":
    try:
        run()
    except SystemExit:
        pass
    except Exception as e:
        cprint(ctext(f"Fatal error: {e}", Colors.RED))
        sys.exit(1)
