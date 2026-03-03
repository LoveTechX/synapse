"""
PHASE 2: Preview Mode System
Safe preview of predicted actions without making changes.
Users can review and approve each file move before execution.
Under revised confidence routing, all medium or low confidence
predictions land here (low confidence entries include a strong warning).
This removes silent skips and keeps a human in the loop.
"""

import os
from typing import Optional, Dict, Any

# For audit logging of preview approvals/rejections
from storage.decision_log import log_decision


class PreviewMode:
    """Preview planned file moves without executing them."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.preview_queue = []

    def enable(self) -> None:
        """Enable preview mode."""
        self.enabled = True
        print("✓ Preview mode ENABLED - files will NOT be moved")

    def disable(self) -> None:
        """Disable preview mode."""
        self.enabled = False
        print("✓ Preview mode DISABLED - files will be moved automatically")

    def toggle(self) -> None:
        """Toggle preview mode on/off."""
        self.enabled = not self.enabled
        status = "ENABLED" if self.enabled else "DISABLED"
        print(f"✓ Preview mode {status}")

    def is_enabled(self) -> bool:
        """Check if preview mode is active."""
        return self.enabled

    def add_to_queue(
        self,
        file_name: str,
        file_path: str,
        destination: str,
        category: str,
        subject: str,
        reason: str,
        confidence: Optional[float] = None,
        warning: bool = False,
    ) -> None:
        """Queue a file for preview.

        Parameters
        ----------
        warning: bool
            True if the item is low confidence and should be displayed with a
            strong warning during review.  This flag is propagated from the
            confidence routing logic in ``realtime_organizer``.
        """
        self.preview_queue.append(
            {
                "file_name": file_name,
                "file_path": file_path,
                "destination": destination,
                "category": category,
                "subject": subject,
                "reason": reason,
                "confidence": confidence,
                "approved": False,
                "skipped": False,
                "warning": warning,
            }
        )

    def show_preview(self, entry: Dict[str, Any]) -> bool:
        """
        Display a preview of the proposed move and ask for approval.
        Returns True if user approves, False if user skips.
        """
        file_name = entry["file_name"]
        destination = entry["destination"]
        category = entry["category"]
        subject = entry["subject"]
        reason = entry["reason"]
        confidence = entry["confidence"]
        extraction_status = entry.get("extraction_status", "unknown")
        warning = entry.get("warning", False)

        print("\n" + "=" * 70)
        print("🔍 PREVIEW MODE - File Move Review")
        print("=" * 70)
        print(f"File:           {file_name}")
        print(f"Category:       {category}")
        if subject and subject.lower() != "general":
            print(f"Subject:        {subject}")
        if confidence is not None and confidence >= 0:
            print(f"Confidence:     {confidence:.1%}")
        print(f"Extraction:     {extraction_status.upper()}")
        print(f"Destination:    {destination}")
        if warning:
            print("\n!!! LOW CONFIDENCE — STRONG USER REVIEW RECOMMENDED !!!\n")
        print("-" * 70)
        print(f"Reason:         {reason}")
        print("=" * 70)

        while True:
            choice = input("✓ Move this file? (Y/N/Show details): ").strip().lower()
            if choice in {"y", "yes"}:
                entry["approved"] = True
                print("✓ Approved - file will be moved")
                return True
            elif choice in {"n", "no"}:
                print("✗ Skipped - file will NOT be moved")
                entry["skipped"] = True
                # Log rejection from preview explicitly
                try:
                    log_decision(
                        file_path=entry.get("file_path"),
                        action="preview_rejected",
                        reason="User rejected move in preview",
                        category=entry.get("category"),
                        subject=entry.get("subject"),
                        destination=entry.get("destination"),
                        confidence=entry.get("confidence"),
                        details={"mode": "preview"},
                    )
                except Exception:
                    pass
                return False
            elif choice in {"d", "details"}:
                self._show_detailed_info(entry)
            else:
                print("Please enter Y, N, or D")

    def _show_detailed_info(self, entry: Dict[str, Any]) -> None:
        """Show more detailed information about the decision."""
        print("\n" + "-" * 70)
        print("📋 Detailed Information:")
        print(f"File Path:      {entry['file_path']}")
        print(f"File Size:      {self._get_file_size(entry['file_path'])}")
        print(f"Detected via:   {entry['reason']}")
        # extraction status may provide insight when content parsing was imperfect
        ex_stat = entry.get("extraction_status", "unknown").upper()
        print(f"Extraction status: {ex_stat}")
        if entry.get("error"):
            print(f"Extraction error: {entry.get('error')}")
        if entry.get("confidence") is not None and entry["confidence"] >= 0:
            confidence_pct = entry["confidence"] * 100
            confidence_bar = "█" * int(confidence_pct / 10) + "░" * (
                10 - int(confidence_pct / 10)
            )
            print(f"Match Quality:  [{confidence_bar}] {confidence_pct:.1f}%")
        # Show full explanation object when available
        explanation = entry.get("explanation")
        if explanation:
            print("\n🔎 Explanation details:")
            detected = explanation.get("detected_keywords") or []
            print(f"  Detected Keywords: {', '.join(detected) if detected else 'None'}")
            sem = explanation.get("semantic_confidence")
            if sem is None:
                print("  Semantic Confidence: N/A")
            else:
                print(f"  Semantic Confidence: {sem:.3f}")
            print(f"  Reason: {explanation.get('reason', 'N/A')}")
        print("-" * 70 + "\n")

    @staticmethod
    def _get_file_size(file_path: str) -> str:
        """Get human-readable file size."""
        try:
            size_bytes = os.path.getsize(file_path)
            for unit in ["B", "KB", "MB", "GB"]:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} TB"
        except:
            return "Unknown"

    def review_all(self) -> Dict[str, list]:
        """
        Review all queued files one by one.
        Returns: {"approved": [...], "skipped": [...]}
        """
        if not self.preview_queue:
            print("📌 No files to preview")
            return {"approved": [], "skipped": []}

        print(f"\n📂 Reviewing {len(self.preview_queue)} file(s)...")

        for entry in self.preview_queue:
            approved = self.show_preview(entry)
            # Log preview approval decisions for auditability
            if approved:
                try:
                    log_decision(
                        file_path=entry.get("file_path"),
                        action="preview_approved",
                        reason="User approved move in preview",
                        category=entry.get("category"),
                        subject=entry.get("subject"),
                        destination=entry.get("destination"),
                        confidence=entry.get("confidence"),
                        details={"mode": "preview"},
                    )
                except Exception:
                    pass

        approved = [e for e in self.preview_queue if e.get("approved")]
        skipped = [e for e in self.preview_queue if e.get("skipped")]

        print("\n" + "=" * 70)
        print(f"✓ Approved: {len(approved)} | ✗ Skipped: {len(skipped)}")
        print("=" * 70 + "\n")

        return {
            "approved": approved,
            "skipped": skipped,
        }

    def clear_queue(self) -> None:
        """Clear the preview queue."""
        self.preview_queue = []

    def get_queue_summary(self) -> Dict[str, Any]:
        """Get summary of queued items."""
        return {
            "total": len(self.preview_queue),
            "approved": len([e for e in self.preview_queue if e.get("approved")]),
            "skipped": len([e for e in self.preview_queue if e.get("skipped")]),
            "pending": len(
                [
                    e
                    for e in self.preview_queue
                    if not e.get("approved") and not e.get("skipped")
                ]
            ),
        }


# Global preview mode instance
preview_mode = PreviewMode(enabled=False)
