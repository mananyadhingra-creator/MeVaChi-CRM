"""
=========================================================
Workbook Inspector
=========================================================
"""

import os
import pandas as pd

from migration.config import (
    EXCEL_FOLDER,
    WORKBOOK_NAME
)

from migration.mappings import (
    SKIP_SHEETS,
    IMPORT_RULES
)


def inspect():

    workbook = os.path.join(
        EXCEL_FOLDER,
        WORKBOOK_NAME
    )

    excel = pd.ExcelFile(workbook)

    print("\n")
    print("=" * 80)
    print("WORKBOOK INSPECTION")
    print("=" * 80)

    for sheet in excel.sheet_names:

        print("\n")

        print("=" * 60)
        print(sheet)
        print("=" * 60)

        if sheet in SKIP_SHEETS:

            print("SKIPPED SHEET")

            continue

        df = pd.read_excel(
            excel,
            sheet_name=sheet
        )

        print(f"Rows    : {len(df)}")
        print(f"Columns : {len(df.columns)}")

        print()

        for i, col in enumerate(df.columns, start=1):

            print(f"{i:02}. {col}")

        if sheet in IMPORT_RULES:

            print()

            print("Target Model :",
                  IMPORT_RULES[sheet]["table"])

        else:

            print()

            print("NO IMPORT RULE FOUND")


if __name__ == "__main__":

    inspect()