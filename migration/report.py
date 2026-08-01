"""
=========================================================
Migration Report
=========================================================
"""

import os
from datetime import datetime

from migration.config import LOG_FOLDER, SAVE_LOG


class MigrationReport:

    def __init__(self):

        self.start_time = datetime.now()

        self.stats = {}

        self.errors = []

    # --------------------------------------------------

    def imported(self, sheet):

        if sheet not in self.stats:
            self.stats[sheet] = {
                "imported": 0,
                "skipped": 0
            }

        self.stats[sheet]["imported"] += 1

    # --------------------------------------------------

    def skipped(self, sheet):

        if sheet not in self.stats:
            self.stats[sheet] = {
                "imported": 0,
                "skipped": 0
            }

        self.stats[sheet]["skipped"] += 1

    # --------------------------------------------------

    def error(self, sheet, row, message):

        self.errors.append({

            "sheet": sheet,
            "row": row,
            "message": str(message)

        })

    # --------------------------------------------------

    def generate(self):

        end_time = datetime.now()

        duration = end_time - self.start_time

        lines = []

        lines.append("=" * 60)
        lines.append("MeVaChi CRM Migration Report")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Started : {self.start_time}")
        lines.append(f"Finished: {end_time}")
        lines.append(f"Duration: {duration}")
        lines.append("")

        total_imported = 0
        total_skipped = 0

        lines.append("IMPORT SUMMARY")
        lines.append("-" * 60)

        for sheet, data in self.stats.items():

            imported = data["imported"]
            skipped = data["skipped"]

            total_imported += imported
            total_skipped += skipped

            lines.append(
                f"{sheet:<30} Imported: {imported:<5} Skipped: {skipped}"
            )

        lines.append("")
        lines.append(f"TOTAL IMPORTED : {total_imported}")
        lines.append(f"TOTAL SKIPPED  : {total_skipped}")
        lines.append("")

        if self.errors:

            lines.append("=" * 60)
            lines.append("ERRORS")
            lines.append("=" * 60)

            for err in self.errors:

                lines.append(
                    f"[{err['sheet']}] Row {err['row']} : {err['message']}"
                )

        else:

            lines.append("No errors found.")

        report = "\n".join(lines)

        print(report)

        if SAVE_LOG:

            os.makedirs(LOG_FOLDER, exist_ok=True)

            filename = datetime.now().strftime(
                "migration_%Y%m%d_%H%M%S.log"
            )

            filepath = os.path.join(
                LOG_FOLDER,
                filename
            )

            with open(filepath, "w", encoding="utf-8") as f:

                f.write(report)

        return report