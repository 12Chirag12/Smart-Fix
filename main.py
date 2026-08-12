"""SmartFix AI desktop prototype.

Run with: python main.py
"""

from __future__ import annotations

import threading
from typing import Any

try:
    import customtkinter as ctk
except ImportError as error:
    raise SystemExit(
        "customtkinter is not installed. Run: pip install -r requirements.txt"
    ) from error

from diagnosis_engine import diagnose_system, get_health_summary
from system_collector import collect_system_info


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SmartFixApp(ctk.CTk):
    """Main GUI for scanning, diagnosis, and recommendations."""

    def __init__(self) -> None:
        super().__init__()
        self.title("SmartFix AI - Windows Troubleshooting Prototype")
        self.geometry("1180x760")
        self.minsize(1000, 680)
        self.configure(fg_color="#08111f")

        self.system_info: dict[str, Any] | None = None
        self.issues: list[dict[str, str]] = []
        self.is_scanning = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_dashboard()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color="#0d1b2a")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="SMARTFIX AI",
            font=ctk.CTkFont(family="Segoe UI", size=25, weight="bold"),
            text_color="#55c2ff",
        ).grid(row=0, column=0, padx=25, pady=(35, 4), sticky="w")
        ctk.CTkLabel(
            sidebar,
            text="Windows Health Assistant",
            font=ctk.CTkFont(size=12),
            text_color="#8fa7bf",
        ).grid(row=1, column=0, padx=25, pady=(0, 32), sticky="w")

        self.scan_button = self._sidebar_button(
            sidebar, "Scan My PC", self.start_scan, row=2, accent=True
        )
        self._sidebar_button(
            sidebar, "Diagnose Problems", self.run_diagnosis, row=3
        )
        self._sidebar_button(
            sidebar, "View System Info", self.show_system_information, row=4
        )
        self._sidebar_button(sidebar, "Exit", self.destroy, row=8)

        ctk.CTkLabel(
            sidebar,
            text="Prototype v0.1\nRead-only diagnosis",
            justify="left",
            text_color="#607b96",
            font=ctk.CTkFont(size=11),
        ).grid(row=7, column=0, padx=25, pady=20, sticky="sw")

    def _sidebar_button(
        self,
        parent: ctk.CTkFrame,
        text: str,
        command: Any,
        row: int,
        accent: bool = False,
    ) -> ctk.CTkButton:
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=180,
            height=42,
            corner_radius=9,
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold" if accent else "normal"),
            fg_color="#087fdb" if accent else "transparent",
            hover_color="#0b6fb8" if accent else "#172c42",
            border_width=0 if accent else 1,
            border_color="#24425e",
        )
        button.grid(row=row, column=0, padx=25, pady=7)
        return button

    def _build_dashboard(self) -> None:
        content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        content.grid(row=0, column=1, padx=28, pady=24, sticky="nsew")
        content.grid_columnconfigure((0, 1, 2), weight=1)
        content.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            content,
            text="System Health Dashboard",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color="#eef7ff",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        self.status_label = ctk.CTkLabel(
            content,
            text="Ready to scan",
            height=30,
            corner_radius=15,
            fg_color="#132a3e",
            text_color="#9cc9e8",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.status_label.grid(row=0, column=2, padx=(15, 0), sticky="e")

        self.card_values: dict[str, ctk.CTkLabel] = {}
        for column, (name, color) in enumerate(
            (("CPU", "#43b5ff"), ("RAM", "#8c7cff"), ("DISK", "#35d0a0"))
        ):
            card = ctk.CTkFrame(
                content,
                height=120,
                corner_radius=14,
                fg_color="#102235",
                border_width=1,
                border_color="#1d3b55",
            )
            card.grid(row=1, column=column, padx=(0 if column == 0 else 8, 8), pady=22, sticky="ew")
            card.grid_propagate(False)
            ctk.CTkLabel(
                card,
                text=name,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#8ea6bc",
            ).pack(anchor="w", padx=20, pady=(18, 2))
            value = ctk.CTkLabel(
                card,
                text="-- %",
                font=ctk.CTkFont(size=31, weight="bold"),
                text_color=color,
            )
            value.pack(anchor="w", padx=20)
            self.card_values[name.lower()] = value

        ctk.CTkLabel(
            content,
            text="Diagnosis & Recommendations",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color="#e4f1fa",
        ).grid(row=2, column=0, columnspan=3, pady=(0, 10), sticky="w")

        results = ctk.CTkFrame(content, corner_radius=14, fg_color="#102235")
        results.grid(row=3, column=0, columnspan=3, sticky="nsew")
        results.grid_columnconfigure((0, 1), weight=1)
        results.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            results,
            text="DETECTED PROBLEMS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ff9b9b",
        ).grid(row=0, column=0, padx=20, pady=(17, 7), sticky="w")
        ctk.CTkLabel(
            results,
            text="RECOMMENDED FIXES",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#6ee7bd",
        ).grid(row=0, column=1, padx=20, pady=(17, 7), sticky="w")

        self.problems_text = self._result_box(results, 0)
        self.fixes_text = self._result_box(results, 1)
        self._set_text(
            self.problems_text,
            "No scan results yet.\n\nClick 'Scan My PC' to collect a system snapshot.",
        )
        self._set_text(
            self.fixes_text,
            "SmartFix only recommends actions in this prototype.\n\nNo repair command is executed automatically.",
        )

    def _result_box(self, parent: ctk.CTkFrame, column: int) -> ctk.CTkTextbox:
        box = ctk.CTkTextbox(
            parent,
            corner_radius=10,
            fg_color="#0a1827",
            border_width=1,
            border_color="#1d3b55",
            text_color="#cbdbe8",
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
        )
        box.grid(
            row=1,
            column=column,
            padx=(18, 8) if column == 0 else (8, 18),
            pady=(0, 18),
            sticky="nsew",
        )
        return box

    @staticmethod
    def _set_text(widget: ctk.CTkTextbox, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def start_scan(self) -> None:
        """Run collection outside the GUI thread to avoid freezing the window."""
        if self.is_scanning:
            return
        self.is_scanning = True
        self.scan_button.configure(state="disabled", text="Scanning...")
        self.status_label.configure(text="  Scan in progress...  ", text_color="#ffd166")
        self._set_text(self.problems_text, "Collecting Windows system information...")
        thread = threading.Thread(target=self._scan_worker, daemon=True)
        thread.start()

    def _scan_worker(self) -> None:
        try:
            snapshot = collect_system_info()
            issues = diagnose_system(snapshot)
            self.after(0, lambda: self._scan_complete(snapshot, issues))
        except Exception as error:  # Final GUI safety net for unexpected OS errors.
            self.after(0, lambda: self._scan_failed(str(error)))

    def _scan_complete(
        self, snapshot: dict[str, Any], issues: list[dict[str, str]]
    ) -> None:
        self.system_info = snapshot
        self.issues = issues
        self.is_scanning = False
        self.scan_button.configure(state="normal", text="Scan My PC")
        self._update_health_cards()
        self._display_diagnosis()

        summary = get_health_summary(issues)
        color = "#6ee7bd" if not issues else "#ffd166"
        if any(item["severity"] == "High" for item in issues):
            color = "#ff8a8a"
        self.status_label.configure(text=f"  {summary}  ", text_color=color)

    def _scan_failed(self, error_message: str) -> None:
        self.is_scanning = False
        self.scan_button.configure(state="normal", text="Scan My PC")
        self.status_label.configure(text="  Scan failed  ", text_color="#ff8a8a")
        self._set_text(
            self.problems_text,
            f"The scan could not be completed.\n\nDetails: {error_message}",
        )

    def _update_health_cards(self) -> None:
        if not self.system_info:
            return
        values = {
            "cpu": self.system_info.get("cpu", {}).get("usage_percent"),
            "ram": self.system_info.get("memory", {}).get("usage_percent"),
            "disk": self.system_info.get("disk", {}).get("usage_percent"),
        }
        for name, value in values.items():
            display = f"{value:.1f} %" if isinstance(value, (int, float)) else "N/A"
            self.card_values[name].configure(text=display)

    def run_diagnosis(self) -> None:
        if not self.system_info:
            self.status_label.configure(
                text="  Please scan first  ", text_color="#ffd166"
            )
            return
        self.issues = diagnose_system(self.system_info)
        self._display_diagnosis()

    def _display_diagnosis(self) -> None:
        if not self.issues:
            self._set_text(
                self.problems_text,
                "[OK] No threshold-based problems detected.\n\nCPU, RAM, disk, and local network status are within the prototype rules.",
            )
            self._set_text(
                self.fixes_text,
                "No immediate action is recommended.\n\nContinue normal system maintenance and run another scan if performance changes.",
            )
            return

        problems: list[str] = []
        fixes: list[str] = []
        for number, issue in enumerate(self.issues, start=1):
            problems.append(
                f"{number}. {issue['problem']}\n"
                f"   Severity: {issue['severity']}\n"
                f"   Possible cause: {issue['possible_cause']}\n"
            )
            fixes.append(
                f"{number}. {issue['recommendation']}\n\n"
                f"   AI insight (simulated): {issue['ai_explanation']}\n"
            )
        self._set_text(self.problems_text, "\n".join(problems))
        self._set_text(self.fixes_text, "\n".join(fixes))

    def show_system_information(self) -> None:
        """Show the full collected snapshot in a separate, read-only window."""
        if not self.system_info:
            self.status_label.configure(
                text="  Please scan first  ", text_color="#ffd166"
            )
            return

        window = ctk.CTkToplevel(self)
        window.title("SmartFix AI - System Information")
        window.geometry("790x650")
        window.configure(fg_color="#08111f")
        window.transient(self)

        ctk.CTkLabel(
            window,
            text="Collected System Information",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#eef7ff",
        ).pack(anchor="w", padx=25, pady=(22, 10))
        text_box = ctk.CTkTextbox(
            window,
            fg_color="#0a1827",
            text_color="#cbdbe8",
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        text_box.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        text_box.insert("1.0", self._format_system_info())
        text_box.configure(state="disabled")

    def _format_system_info(self) -> str:
        assert self.system_info is not None
        data = self.system_info
        system = data.get("system", {})
        cpu = data.get("cpu", {})
        memory = data.get("memory", {})
        disk = data.get("disk", {})
        network = data.get("network", {})
        services = data.get("services", {})

        lines = [
            f"SCAN TIME: {data.get('collection_time', 'Unknown')}",
            "",
            "SYSTEM",
            f"  Computer: {system.get('computer_name', 'Unavailable')}",
            f"  Windows: {system.get('windows_version', 'Unavailable')}",
            f"  Architecture: {system.get('architecture', 'Unavailable')}",
            f"  Processor: {system.get('processor', 'Unavailable')}",
            "",
            "CPU",
            f"  Usage: {cpu.get('usage_percent', 'Unavailable')}%",
            f"  Physical / logical cores: {cpu.get('physical_cores', '?')} / {cpu.get('logical_cores', '?')}",
            "",
            "MEMORY",
            f"  Usage: {memory.get('usage_percent', 'Unavailable')}%",
            f"  Used / total: {memory.get('used_gb', '?')} GB / {memory.get('total_gb', '?')} GB",
            f"  Available: {memory.get('available_gb', '?')} GB",
            "",
            "WINDOWS DISK",
            f"  Drive: {disk.get('drive', 'Unavailable')}",
            f"  Usage: {disk.get('usage_percent', 'Unavailable')}%",
            f"  Free / total: {disk.get('free_gb', '?')} GB / {disk.get('total_gb', '?')} GB",
            "",
            "NETWORK",
            f"  Local network available: {'Yes' if network.get('available') else 'No'}",
            f"  Active interfaces: {', '.join(network.get('active_interfaces', [])) or 'None'}",
            f"  IPv4 addresses: {', '.join(network.get('ipv4_addresses', [])) or 'None'}",
            "",
            "SELECTED WINDOWS SERVICES",
        ]
        if services.get("items"):
            for item in services["items"].values():
                lines.append(
                    f"  {item.get('display_name', 'Unknown')}: {item.get('status', 'unknown')}"
                )
        else:
            lines.append("  Service status is unavailable on this system.")

        lines.extend(["", "TOP PROCESSES BY MEMORY"])
        for process in data.get("processes", []):
            lines.append(
                f"  PID {str(process.get('pid', '?')):>6}  "
                f"Memory {process.get('memory_percent', 0):>5.1f}%  "
                f"CPU {process.get('cpu_percent', 0):>5.1f}%  "
                f"{process.get('name', 'Unknown')}"
            )

        errors = data.get("collection_errors", [])
        if errors:
            lines.extend(["", "NON-FATAL COLLECTION WARNINGS"])
            lines.extend(f"  - {error}" for error in errors)

        return "\n".join(lines)


def main() -> None:
    app = SmartFixApp()
    app.mainloop()


if __name__ == "__main__":
    main()
