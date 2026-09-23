"""
=========================================================
MeVaChi CRM
Aman Singh Workbook SYNC Importer
=========================================================

Workbook:
    excel/Aman.xlsx

Imported sheets:
    Visits
    Sale Acheiveds Revenue
    Invoice
    Drawings
    Leads
    Sheet9 -> Meetings

Ignored:
    Sites
    Rajat
    bbd

IMPORTANT
---------
This is a SYNC importer, not a blind fresh import.

For every Excel row:
    1. Safely match an existing Aman Singh CRM record.
    2. If matched and values changed -> UPDATE.
    3. If matched and nothing changed -> UNCHANGED.
    4. If no reliable CRM match -> NEW.
    5. If multiple CRM records could match -> NEEDS REVIEW.
       No record is updated/created in that case.
    6. Duplicate rows inside the current Excel workbook are not imported.
    7. Blank Excel cells NEVER erase existing CRM values.

FIRST RUN:
    PREVIEW_ONLY = True

Only after the preview looks correct:
    PREVIEW_ONLY = False

Run:
    python -m migration.import_aman
"""

import os
import traceback
from collections import Counter
from datetime import datetime

import pandas as pd

from migration.database import app, db, get_model
from migration.utils import (
    clean_text,
    clean_phone,
    clean_int,
    clean_decimal,
    clean_date,
    is_empty,
)


# =========================================================
# SETTINGS
# =========================================================

EXCEL_FOLDER = "excel"
WORKBOOK_NAME = "Aman.xlsx"

RECORD_OWNER = "Aman"

# SAFE FIRST RUN.
# True  = analyse only, rollback all DB changes.
# False = actually INSERT / UPDATE records.
PREVIEW_ONLY = False

# Existing matched records will be updated when True.
APPLY_UPDATES = True

LOG_FOLDER = "migration/logs"

SKIP_SHEETS = {
    "Sites",
    "Rajat",
    "bbd",
}

SHEET_VISITS = "Visits"
SHEET_SALES = "Sale Acheiveds Revenue"
SHEET_INVOICE = "Invoice"
SHEET_DRAWINGS = "Drawings"
SHEET_LEADS = "Leads"
SHEET_MEETINGS = "Sheet9"


# =========================================================
# REPORT STATE
# =========================================================

stats = {}
errors = []
review_rows = []
changes = []
duplicate_rows = []


def init_sheet(sheet):
    if sheet not in stats:
        stats[sheet] = {
            "new": 0,
            "updated": 0,
            "unchanged": 0,
            "skipped": 0,
            "review": 0,
            "duplicate": 0,
        }


def stat(sheet, key):
    init_sheet(sheet)
    stats[sheet][key] += 1


def add_error(sheet, row_no, message):
    errors.append({
        "sheet": sheet,
        "row": row_no,
        "message": str(message),
    })


def add_review(sheet, row_no, reason, identity="", candidates=None):
    stat(sheet, "review")

    item = {
        "sheet": sheet,
        "row": row_no,
        "reason": str(reason),
        "identity": identity or "",
        "candidates": candidates or [],
    }

    review_rows.append(item)


def add_duplicate(sheet, row_no, identity, first_row):
    stat(sheet, "duplicate")

    duplicate_rows.append({
        "sheet": sheet,
        "row": row_no,
        "identity": identity,
        "first_row": first_row,
    })


# =========================================================
# REPORT
# =========================================================

def save_report():
    os.makedirs(LOG_FOLDER, exist_ok=True)

    generated = datetime.now()

    lines = []

    lines.append("=" * 80)
    lines.append("MeVaChi CRM - Aman Singh Workbook SYNC Report")
    lines.append("=" * 80)
    lines.append(f"Generated : {generated}")
    lines.append(f"Workbook  : {WORKBOOK_NAME}")
    lines.append(f"Owner     : {RECORD_OWNER}")
    lines.append(f"Preview   : {PREVIEW_ONLY}")
    lines.append("")

    total_new = 0
    total_updated = 0
    total_unchanged = 0
    total_skipped = 0
    total_review = 0
    total_duplicate = 0

    lines.append("SUMMARY")
    lines.append("-" * 80)

    for sheet, data in stats.items():
        total_new += data["new"]
        total_updated += data["updated"]
        total_unchanged += data["unchanged"]
        total_skipped += data["skipped"]
        total_review += data["review"]
        total_duplicate += data["duplicate"]

        lines.append(
            f"{sheet:<28} "
            f"NEW={data['new']:<4} "
            f"UPDATED={data['updated']:<4} "
            f"UNCHANGED={data['unchanged']:<4} "
            f"SKIPPED={data['skipped']:<4} "
            f"REVIEW={data['review']:<4} "
            f"DUPLICATE={data['duplicate']:<4}"
        )

    lines.append("")
    lines.append(f"TOTAL NEW        : {total_new}")
    lines.append(f"TOTAL UPDATED    : {total_updated}")
    lines.append(f"TOTAL UNCHANGED  : {total_unchanged}")
    lines.append(f"TOTAL SKIPPED    : {total_skipped}")
    lines.append(f"TOTAL REVIEW     : {total_review}")
    lines.append(f"TOTAL DUPLICATE  : {total_duplicate}")
    lines.append(f"TOTAL ERRORS     : {len(errors)}")

    if changes:
        lines.append("")
        lines.append("=" * 80)
        lines.append("UPDATED RECORDS")
        lines.append("=" * 80)

        for item in changes:
            lines.append(
                f"[{item['sheet']}] Row {item['row']} | "
                f"{item['identity']} | "
                f"Changed: {', '.join(item['fields'])}"
            )

    if review_rows:
        lines.append("")
        lines.append("=" * 80)
        lines.append("NEEDS REVIEW - NOT IMPORTED / NOT UPDATED")
        lines.append("=" * 80)

        for item in review_rows:
            candidate_text = ""

            if item["candidates"]:
                candidate_text = (
                    " | Candidates: "
                    + ", ".join(item["candidates"])
                )

            lines.append(
                f"[{item['sheet']}] Row {item['row']} | "
                f"{item['reason']} | "
                f"{item['identity']}"
                f"{candidate_text}"
            )

        lines.append("")
        lines.append(
            "ACTION: These rows were deliberately left untouched. "
            "Only contact Sir about these rows if manual confirmation is required."
        )

    if duplicate_rows:
        lines.append("")
        lines.append("=" * 80)
        lines.append("DUPLICATE ROWS INSIDE CURRENT EXCEL")
        lines.append("=" * 80)

        for item in duplicate_rows:
            lines.append(
                f"[{item['sheet']}] Row {item['row']} duplicates "
                f"row {item['first_row']} | {item['identity']}"
            )

    if errors:
        lines.append("")
        lines.append("=" * 80)
        lines.append("ERRORS")
        lines.append("=" * 80)

        for item in errors:
            lines.append(
                f"[{item['sheet']}] Row {item['row']} : "
                f"{item['message']}"
            )
    else:
        lines.append("")
        lines.append("No errors found.")

    lines.append("")
    lines.append("=" * 80)

    if total_review or errors:
        lines.append(
            "RESULT: MANUAL CHECK REQUIRED "
            "(review/error rows were found)."
        )
    else:
        lines.append(
            "RESULT: NO MANUAL ISSUE FOUND."
        )

    lines.append("=" * 80)

    report = "\n".join(lines)

    print("\n" + report + "\n")

    filename = datetime.now().strftime(
        "migration_aman_%Y%m%d_%H%M%S.log"
    )

    filepath = os.path.join(LOG_FOLDER, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report saved to: {filepath}")

    return report


# =========================================================
# GENERAL HELPERS
# =========================================================

def find_workbook():
    path = os.path.join(EXCEL_FOLDER, WORKBOOK_NAME)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Workbook not found: {path}"
        )

    return path


def read_sheet(excel, sheet_name):
    df = pd.read_excel(
        excel,
        sheet_name=sheet_name,
    )

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    return df


def row_is_completely_empty(row):
    return all(
        is_empty(value)
        for value in row.values
    )


def safe_identity(*values):
    values = [
        clean_text(v)
        for v in values
        if not is_empty(v)
    ]

    return " | ".join(values)


def norm(value):
    """
    Normalised comparison value used ONLY for matching.

    Does not modify the value stored in the CRM.
    """
    if is_empty(value):
        return ""

    text = str(value).strip().lower()

    # Remove common spreadsheet formatting noise.
    text = " ".join(text.split())

    return text


def identity_token(*values):
    return "|".join(
        norm(value)
        for value in values
    )


def candidate_label(record, label_fields):
    parts = []

    for field in label_fields:
        value = getattr(record, field, None)

        if not is_empty(value):
            parts.append(
                f"{field}={value}"
            )

    if not parts:
        parts.append(
            f"id={getattr(record, 'id', 'unknown')}"
        )

    return ", ".join(parts)


def unique_candidates(query):
    """
    Return all unique matching ORM records.

    We deliberately DO NOT use .first() because .first()
    can silently choose the wrong record when multiple
    Aman records match.
    """
    records = query.all()

    unique = []
    seen = set()

    for record in records:
        key = getattr(record, "id", None)

        if key is None:
            key = id(record)

        if key not in seen:
            seen.add(key)
            unique.append(record)

    return unique


def choose_candidate(
    sheet,
    row_no,
    identity,
    query,
    label_fields,
    reason_if_multiple,
):
    """
    Returns:
        existing record
        None when there is no match
        None + review when ambiguous
    """
    candidates = unique_candidates(query)

    if len(candidates) == 0:
        return None

    if len(candidates) > 1:
        labels = [
            candidate_label(
                record,
                label_fields,
            )
            for record in candidates
        ]

        add_review(
            sheet,
            row_no,
            reason_if_multiple,
            identity,
            labels,
        )

        return "__AMBIGUOUS__"

    return candidates[0]


def set_if_changed(existing, field, new_value, changed_fields):
    """
    Blank Excel cells NEVER overwrite CRM values.
    """
    if is_empty(new_value):
        return

    old_value = getattr(existing, field, None)

    if old_value != new_value:
        setattr(existing, field, new_value)
        changed_fields.append(field)


def apply_update(existing, incoming):
    changed_fields = []

    for field, value in incoming.items():
        if field == "record_owner":
            continue

        set_if_changed(
            existing,
            field,
            value,
            changed_fields,
        )

    return changed_fields


def finish_row(
    sheet,
    row_no,
    incoming,
    existing,
    model,
    identity,
):
    """
    Handle NEW / UPDATE / UNCHANGED.

    "__AMBIGUOUS__" is never passed here.
    """

    if existing is not None:
        if APPLY_UPDATES:
            changed_fields = apply_update(
                existing,
                incoming,
            )

            if changed_fields:
                stat(sheet, "updated")

                changes.append({
                    "sheet": sheet,
                    "row": row_no,
                    "identity": identity,
                    "fields": changed_fields,
                })
            else:
                stat(sheet, "unchanged")

        else:
            stat(sheet, "unchanged")

        return

    db.session.add(
        model(**incoming)
    )

    stat(sheet, "new")


# =========================================================
# DUPLICATE DETECTION
# =========================================================

def prepare_duplicate_map(df, identity_function):
    """
    Build identity -> first Excel row.

    Only rows with a non-empty identity are considered.
    """
    occurrences = {}

    for index, row in df.iterrows():
        row_no = index + 2

        try:
            identity = identity_function(row)
        except Exception:
            continue

        if not identity:
            continue

        occurrences.setdefault(
            identity,
            []
        ).append(row_no)

    return {
        identity: rows
        for identity, rows in occurrences.items()
        if len(rows) > 1
    }


def is_excel_duplicate(
    duplicate_map,
    seen_identities,
    identity,
    sheet,
    row_no,
):
    if not identity:
        return False

    if identity not in duplicate_map:
        return False

    if identity in seen_identities:
        add_duplicate(
            sheet,
            row_no,
            identity,
            duplicate_map[identity][0],
        )
        return True

    seen_identities.add(identity)
    return False


# =========================================================
# VISITS
# =========================================================

def visit_identity(row):
    company = clean_text(row.get("Company"))
    person = clean_text(row.get("Name"))
    contact = clean_phone(row.get("Contact"))
    date = clean_date(row.get("Date"))

    # Strongest available identity
    if company and person and date is not None:
        return identity_token(
            company,
            person,
            date,
        )

    # Company + date is still useful when person is blank
    if company and date is not None:
        return identity_token(
            company,
            date,
        )

    # Company + contact
    if company and contact:
        return identity_token(
            company,
            contact,
        )

    # Person + contact + date
    if person and contact and date is not None:
        return identity_token(
            person,
            contact,
            date,
        )

    return ""


def import_visits(df):
    model = get_model("Visit")

    duplicate_map = prepare_duplicate_map(
        df,
        visit_identity,
    )

    seen = set()

    for index, row in df.iterrows():
        row_no = index + 2

        if row_is_completely_empty(row):
            stat(SHEET_VISITS, "skipped")
            continue

        if is_empty(row.get("ABC")):
            stat(SHEET_VISITS, "skipped")
            continue

        incoming = {
            "meeting_id": None,
            "state": clean_text(row.get("State")),
            "region": clean_text(row.get("Region")),
            "abc": clean_text(row.get("ABC")),
            "company_name": clean_text(row.get("Company")),
            "person_name": clean_text(row.get("Name")),
            "designation": clean_text(row.get("Designation")),
            "contact_no": clean_phone(row.get("Contact")),
            "address": clean_text(row.get("Address")),
            "brief": clean_text(row.get("Breif")),
            "visit_date": clean_date(row.get("Date")),
            "leads_generated": clean_int(row.get("Leads Generated")),
            "m2": clean_text(row.get("M2")),
            "m3": clean_text(row.get("M3")),
            "record_owner": RECORD_OWNER,
        }

        identity = safe_identity(
            incoming["company_name"],
            incoming["person_name"],
            incoming["visit_date"],
        )

        duplicate_identity = visit_identity(row)

        if is_excel_duplicate(
            duplicate_map,
            seen,
            duplicate_identity,
            SHEET_VISITS,
            row_no,
        ):
            continue

        existing = None

        # -------------------------------------------------
        # MATCH 1:
        # Company + Person + Date
        # -------------------------------------------------

        if (
            incoming["company_name"]
            and incoming["person_name"]
            and incoming["visit_date"] is not None
        ):
            existing = choose_candidate(
                SHEET_VISITS,
                row_no,
                identity,
                model.query.filter(
                    model.record_owner == RECORD_OWNER,
                    model.company_name == incoming["company_name"],
                    model.person_name == incoming["person_name"],
                    model.visit_date == incoming["visit_date"],
                ),
                [
                    "id",
                    "company_name",
                    "person_name",
                    "visit_date",
                ],
                "Multiple CRM Visits matched company + person + date",
            )

        if existing == "__AMBIGUOUS__":
            continue

        # -------------------------------------------------
        # MATCH 2:
        # Company + Date
        #
        # Safe only if exactly ONE CRM record matches.
        # -------------------------------------------------

        if (
            existing is None
            and incoming["company_name"]
            and incoming["visit_date"] is not None
        ):
            existing = choose_candidate(
                SHEET_VISITS,
                row_no,
                identity,
                model.query.filter(
                    model.record_owner == RECORD_OWNER,
                    model.company_name == incoming["company_name"],
                    model.visit_date == incoming["visit_date"],
                ),
                [
                    "id",
                    "company_name",
                    "person_name",
                    "visit_date",
                ],
                "Multiple CRM Visits matched company + date",
            )

        if existing == "__AMBIGUOUS__":
            continue

        # -------------------------------------------------
        # MATCH 3:
        # Company + Contact
        # -------------------------------------------------

        if (
            existing is None
            and incoming["company_name"]
            and incoming["contact_no"]
        ):
            existing = choose_candidate(
                SHEET_VISITS,
                row_no,
                identity,
                model.query.filter(
                    model.record_owner == RECORD_OWNER,
                    model.company_name == incoming["company_name"],
                    model.contact_no == incoming["contact_no"],
                ),
                [
                    "id",
                    "company_name",
                    "person_name",
                    "contact_no",
                ],
                "Multiple CRM Visits matched company + contact",
            )

        if existing == "__AMBIGUOUS__":
            continue

        # -------------------------------------------------
        # MATCH 4:
        # Person + Contact + Date
        # -------------------------------------------------

        if (
            existing is None
            and incoming["person_name"]
            and incoming["contact_no"]
            and incoming["visit_date"] is not None
        ):
            existing = choose_candidate(
                SHEET_VISITS,
                row_no,
                identity,
                model.query.filter(
                    model.record_owner == RECORD_OWNER,
                    model.person_name == incoming["person_name"],
                    model.contact_no == incoming["contact_no"],
                    model.visit_date == incoming["visit_date"],
                ),
                [
                    "id",
                    "company_name",
                    "person_name",
                    "contact_no",
                    "visit_date",
                ],
                "Multiple CRM Visits matched person + contact + date",
            )

        if existing == "__AMBIGUOUS__":
            continue

        # -------------------------------------------------
        # MATCH 5:
        # Company + Person + Contact
        #
        # Useful when date changed in the new Excel.
        # -------------------------------------------------

        if (
            existing is None
            and incoming["company_name"]
            and incoming["person_name"]
            and incoming["contact_no"]
        ):
            existing = choose_candidate(
                SHEET_VISITS,
                row_no,
                identity,
                model.query.filter(
                    model.record_owner == RECORD_OWNER,
                    model.company_name == incoming["company_name"],
                    model.person_name == incoming["person_name"],
                    model.contact_no == incoming["contact_no"],
                ),
                [
                    "id",
                    "company_name",
                    "person_name",
                    "contact_no",
                    "visit_date",
                ],
                "Multiple CRM Visits matched company + person + contact",
            )

        if existing == "__AMBIGUOUS__":
            continue

        # -------------------------------------------------
        # No reliable match
        # -------------------------------------------------

        if existing is None:

            strong_identity = (
                (
                    incoming["company_name"]
                    and incoming["person_name"]
                    and incoming["visit_date"] is not None
                )
                or (
                    incoming["company_name"]
                    and incoming["contact_no"]
                )
                or (
                    incoming["company_name"]
                    and incoming["visit_date"] is not None
                )
                or (
                    incoming["person_name"]
                    and incoming["contact_no"]
                    and incoming["visit_date"] is not None
                )
            )

            if not strong_identity:
                add_review(
                    SHEET_VISITS,
                    row_no,
                    "Could not establish a reliable Visit identity",
                    identity,
                )
                continue

        finish_row(
            SHEET_VISITS,
            row_no,
            incoming,
            existing,
            model,
            identity,
        )


# =========================================================
# SALES
# =========================================================

def sales_identity(row):
    reference = clean_text(
        row.get("Refrence No.")
    )

    if reference:
        return identity_token(
            "REF",
            reference,
        )

    return identity_token(
        clean_text(row.get("Name")),
        clean_phone(row.get("Contact")),
        clean_text(row.get("Project Type")),
    )


def import_sales(df):
    model = get_model("SalesPipeline")

    duplicate_map = prepare_duplicate_map(
        df,
        sales_identity,
    )
    seen = set()

    for index, row in df.iterrows():
        row_no = index + 2

        if row_is_completely_empty(row):
            stat(SHEET_SALES, "skipped")
            continue

        if is_empty(row.get("Project Type")):
            stat(SHEET_SALES, "skipped")
            continue

        incoming = {
            "proposal_id": None,
            "name": clean_text(row.get("Name")),
            "reference_no": clean_text(row.get("Refrence No.")),
            "project_stage": clean_text(row.get("Project Stage")),
            "moc": clean_text(row.get("MOC")),
            "source": clean_text(row.get("Source")),
            "next_action": clean_text(row.get("Next Action")),
            "address": clean_text(row.get("Address")),
            "contact_no": clean_phone(row.get("Contact")),
            "project_type": clean_text(row.get("Project Type")),
            "category": clean_text(row.get("Category")),
            "email_id": clean_text(row.get("Email ID")),
            "site_incharge": clean_text(row.get("Site Incharge")),
            "site_incharge_contact": clean_phone(row.get("Contact.1")),
            "first_contact": clean_date(row.get("First Contact")),
            "last_contact": clean_date(row.get("Last Contact")),
            "followup_date": clean_date(row.get("Followup Date")),
            "no_of_site_visits": clean_int(row.get("No. of Site Visit")),
            "area_covered": clean_decimal(row.get("Area Covered")),
            "total_units": clean_int(row.get("Total Units")),
            "price_of_units": clean_decimal(row.get("Price of Units")),
            "first_year_cmc": clean_decimal(row.get("1st Yr. CMC")),
            "installation": clean_decimal(row.get("Installation")),
            "total_sensor": clean_int(row.get("Total Sensor")),
            "sensor_cost": clean_decimal(row.get("Sensor Cost")),
            "discount": clean_decimal(row.get("Discount")),
            "revenue": clean_decimal(row.get("Revenue (₹)")),
            "amount_received": clean_decimal(row.get("Received(₹)")),
            "amount_due": clean_decimal(row.get("Due(₹)")),
            "total_revenue": clean_decimal(row.get("Total Revenue")),
            "gst_no": clean_text(row.get("GST No.")),
            "cmc_onwards": clean_decimal(row.get("CMC Onwards")),
            "total_cmc": clean_decimal(row.get("Total CMC")),
            "sales_person": None,
            "record_owner": RECORD_OWNER,
        }

        identity = safe_identity(
            incoming["name"],
            incoming["reference_no"],
            incoming["contact_no"],
        )

        duplicate_identity = sales_identity(row)

        if is_excel_duplicate(
            duplicate_map,
            seen,
            duplicate_identity,
            SHEET_SALES,
            row_no,
        ):
            continue

        existing = None

        if incoming["reference_no"]:
            existing = choose_candidate(
                SHEET_SALES,
                row_no,
                identity,
                model.query.filter(
                    model.reference_no == incoming["reference_no"],
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "reference_no", "name"],
                "Multiple CRM Sales records have the same reference number",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and (
            incoming["name"]
            and incoming["contact_no"]
            and incoming["project_type"]
        ):
            existing = choose_candidate(
                SHEET_SALES,
                row_no,
                identity,
                model.query.filter(
                    model.name == incoming["name"],
                    model.contact_no == incoming["contact_no"],
                    model.project_type == incoming["project_type"],
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "name", "contact_no", "project_type"],
                "Multiple CRM Sales records matched name + contact + project type",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and (
            incoming["name"]
            and incoming["contact_no"]
        ):
            existing = choose_candidate(
                SHEET_SALES,
                row_no,
                identity,
                model.query.filter(
                    model.name == incoming["name"],
                    model.contact_no == incoming["contact_no"],
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "name", "contact_no", "project_type"],
                "Multiple CRM Sales records matched name + contact",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and not (
            incoming["reference_no"]
            or (
                incoming["name"]
                and incoming["contact_no"]
            )
        ):
            add_review(
                SHEET_SALES,
                row_no,
                "Could not establish a reliable Sales identity",
                identity,
            )
            continue

        finish_row(
            SHEET_SALES,
            row_no,
            incoming,
            existing,
            model,
            identity,
        )


# =========================================================
# INVOICES
# =========================================================

def invoice_identity(row):
    invoice_no = clean_text(
        row.get("Invoice No.")
    )

    if invoice_no:
        return identity_token(
            "INV",
            invoice_no,
        )

    return identity_token(
        clean_text(row.get("Name")),
        clean_date(row.get("DOI")),
        clean_text(row.get("Product Sold")),
    )


def import_invoices(df):
    model = get_model("Invoice")

    duplicate_map = prepare_duplicate_map(
        df,
        invoice_identity,
    )
    seen = set()

    for index, row in df.iterrows():
        row_no = index + 2

        if row_is_completely_empty(row):
            stat(SHEET_INVOICE, "skipped")
            continue

        if is_empty(row.get("Name")):
            stat(SHEET_INVOICE, "skipped")
            continue

        incoming = {
            "sales_id": None,
            "name": clean_text(row.get("Name")),
            "doi": clean_date(row.get("DOI")),
            "invoice_no": clean_text(row.get("Invoice No.")),
            "gst_no": clean_text(row.get("GST No.")),
            "product_sold": clean_text(row.get("Product Sold")),
            "total_units": clean_int(row.get("Total Units")),
            "price_of_units": clean_decimal(row.get("Price of Units")),
            "first_year_cmc": clean_decimal(row.get("1st Yr. CMC")),
            "installation": clean_decimal(row.get("Installation")),
            "total_sensor": clean_int(row.get("Total Sensor")),
            "sensor_cost": clean_decimal(row.get("Sensor Cost")),
            "revenue": clean_decimal(row.get("Revenue (₹)")),
            "total_revenue": clean_decimal(row.get("Total Revenue")),
            "record_owner": RECORD_OWNER,
        }

        identity = safe_identity(
            incoming["name"],
            incoming["invoice_no"],
            incoming["doi"],
        )

        duplicate_identity = invoice_identity(row)

        if is_excel_duplicate(
            duplicate_map,
            seen,
            duplicate_identity,
            SHEET_INVOICE,
            row_no,
        ):
            continue

        existing = None

        if incoming["invoice_no"]:
            existing = choose_candidate(
                SHEET_INVOICE,
                row_no,
                identity,
                model.query.filter(
                    model.invoice_no == incoming["invoice_no"],
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "invoice_no", "name"],
                "Multiple CRM Invoices have the same invoice number",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and (
            incoming["name"]
            and incoming["doi"] is not None
            and incoming["product_sold"]
        ):
            existing = choose_candidate(
                SHEET_INVOICE,
                row_no,
                identity,
                model.query.filter(
                    model.name == incoming["name"],
                    model.doi == incoming["doi"],
                    model.product_sold == incoming["product_sold"],
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "name", "doi", "product_sold"],
                "Multiple CRM Invoices matched name + date + product",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and (
            incoming["name"]
            and incoming["doi"] is not None
            and incoming["total_revenue"] is not None
        ):
            existing = choose_candidate(
                SHEET_INVOICE,
                row_no,
                identity,
                model.query.filter(
                    model.name == incoming["name"],
                    model.doi == incoming["doi"],
                    model.total_revenue == incoming["total_revenue"],
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "name", "doi", "total_revenue"],
                "Multiple CRM Invoices matched name + date + total revenue",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and not (
            incoming["invoice_no"]
            or (
                incoming["name"]
                and incoming["doi"] is not None
                and incoming["product_sold"]
            )
        ):
            add_review(
                SHEET_INVOICE,
                row_no,
                "Could not establish a reliable Invoice identity",
                identity,
            )
            continue

        finish_row(
            SHEET_INVOICE,
            row_no,
            incoming,
            existing,
            model,
            identity,
        )


# =========================================================
# DRAWINGS
# =========================================================

def drawing_identity(row):
    return identity_token(
        clean_text(row.get("Name")),
        clean_text(row.get("Address")),
    )


def import_drawings(df):
    model = get_model("Drawing")

    duplicate_map = prepare_duplicate_map(
        df,
        drawing_identity,
    )
    seen = set()

    for index, row in df.iterrows():
        row_no = index + 2

        if row_is_completely_empty(row):
            stat(SHEET_DRAWINGS, "skipped")
            continue

        name = clean_text(row.get("Name"))
        address = clean_text(row.get("Address"))

        if not name and not address:
            stat(SHEET_DRAWINGS, "skipped")
            continue

        incoming = {
            "visit_id": None,
            "name": name,
            "address": address,
            "iterations": clean_int(row.get("No. of Iteration")),
            "moca": clean_text(row.get("MODM")),
            "record_owner": RECORD_OWNER,
        }

        identity = safe_identity(
            name,
            address,
        )

        duplicate_identity = drawing_identity(row)

        if is_excel_duplicate(
            duplicate_map,
            seen,
            duplicate_identity,
            SHEET_DRAWINGS,
            row_no,
        ):
            continue

        existing = None

        if name and address:
            existing = choose_candidate(
                SHEET_DRAWINGS,
                row_no,
                identity,
                model.query.filter(
                    model.name == name,
                    model.address == address,
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "name", "address"],
                "Multiple CRM Drawings matched name + address",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and name:
            existing = choose_candidate(
                SHEET_DRAWINGS,
                row_no,
                identity,
                model.query.filter(
                    model.name == name,
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "name", "address"],
                "Multiple CRM Drawings matched name only",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and not name:
            add_review(
                SHEET_DRAWINGS,
                row_no,
                "Drawing has no reliable name for matching",
                identity,
            )
            continue

        finish_row(
            SHEET_DRAWINGS,
            row_no,
            incoming,
            existing,
            model,
            identity,
        )


# =========================================================
# LEADS
# =========================================================

def lead_identity(row):
    name = clean_text(row.get("Name"))
    phone = clean_phone(row.get("Contact"))

    if phone:
        return identity_token(
            name,
            phone,
        )

    return identity_token(
        name,
        clean_text(row.get("Location")),
        clean_text(row.get("Address")),
    )


def import_leads(df):
    model = get_model("Lead")

    duplicate_map = prepare_duplicate_map(
        df,
        lead_identity,
    )
    seen = set()

    for index, row in df.iterrows():
        row_no = index + 2

        if row_is_completely_empty(row):
            stat(SHEET_LEADS, "skipped")
            continue

        name = clean_text(row.get("Name"))

        if not name:
            stat(SHEET_LEADS, "skipped")
            continue

        remarks = clean_text(
            row.get("Unnamed: 5")
        )

        location_parts = []

        location = clean_text(
            row.get("Location")
        )
        address = clean_text(
            row.get("Address")
        )

        if location:
            location_parts.append(location)

        if address and address not in location_parts:
            location_parts.append(address)

        combined_location = (
            ", ".join(location_parts)
            if location_parts
            else None
        )

        phone = clean_phone(
            row.get("Contact")
        )

        incoming = {
            "name": name,
            "reference": None,
            "location": combined_location,
            "phone": phone,
            "responses": remarks,
            "next_action": None,
            "date_of_1st_followup": None,
            "next_to_call": None,
            "recent": None,
            "record_owner": RECORD_OWNER,
        }

        identity = safe_identity(
            name,
            phone,
            combined_location,
        )

        duplicate_identity = lead_identity(row)

        if is_excel_duplicate(
            duplicate_map,
            seen,
            duplicate_identity,
            SHEET_LEADS,
            row_no,
        ):
            continue

        existing = None

        if phone:
            existing = choose_candidate(
                SHEET_LEADS,
                row_no,
                identity,
                model.query.filter(
                    model.name == name,
                    model.phone == phone,
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "name", "phone"],
                "Multiple CRM Leads matched name + phone",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None:
            # Name-only fallback is allowed ONLY when exactly
            # one Aman record exists with that name.
            existing = choose_candidate(
                SHEET_LEADS,
                row_no,
                identity,
                model.query.filter(
                    model.name == name,
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "name", "phone", "location"],
                "Multiple CRM Leads have the same name",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None:
            # No existing CRM match = genuinely new Lead.
            finish_row(
                SHEET_LEADS,
                row_no,
                incoming,
                None,
                model,
                identity,
            )
            continue

        finish_row(
            SHEET_LEADS,
            row_no,
            incoming,
            existing,
            model,
            identity,
        )


# =========================================================
# MEETINGS - Sheet9
# =========================================================

def meeting_identity(row):
    company = clean_text(row.get("Company"))
    name = clean_text(row.get("Name"))
    contact = clean_phone(row.get("Contact"))
    date = clean_date(row.get("Date"))

    if company and contact and date is not None:
        return identity_token(
            company,
            contact,
            date,
        )

    if company and name and date is not None:
        return identity_token(
            company,
            name,
            date,
        )

    if company and contact:
        return identity_token(
            company,
            contact,
        )

    if name and contact and date is not None:
        return identity_token(
            name,
            contact,
            date,
        )

    return ""


def import_meetings(df):
    model = get_model("Meeting")

    duplicate_map = prepare_duplicate_map(
        df,
        meeting_identity,
    )
    seen = set()

    for index, row in df.iterrows():
        row_no = index + 2

        if row_is_completely_empty(row):
            stat(SHEET_MEETINGS, "skipped")
            continue

        company = clean_text(row.get("Company"))
        name = clean_text(row.get("Name"))
        contact = clean_phone(row.get("Contact"))
        address = clean_text(row.get("Address"))
        brief = clean_text(row.get("Breif"))
        meeting_date = clean_date(row.get("Date"))

        if not any([
            company,
            name,
            contact,
            address,
            brief,
            meeting_date,
        ]):
            stat(SHEET_MEETINGS, "skipped")
            continue

        incoming = {
            "meeting_fixed_by": None,
            "source": None,
            "name": name,
            "reference": None,
            "firm_name": company,
            "designation": clean_text(row.get("Designation")),
            "address": address,
            "state": clean_text(row.get("State")),
            "contact_no": contact,
            "email": None,
            "company_info_shared": None,
            "meeting_fixed": None,
            "date_of_meeting": meeting_date,
            "mode_of_meeting": None,
            "meeting_status": None,
            "meeting_conducted_by": None,
            "floor_plan_shared": None,
            "site_visit": None,
            "post_meeting_mail": None,
            "date_of_last_followup": None,
            "date_to_call_next": None,
            "final_remarks": None,
            "reschedule_date": None,
            "reason_for_reschedule": None,
            "remarks": brief,
            "next_action": None,
            "lead_id": None,
            "record_owner": RECORD_OWNER,
        }

        identity = safe_identity(
            company,
            name,
            contact,
            meeting_date,
        )

        duplicate_identity = meeting_identity(row)

        if is_excel_duplicate(
            duplicate_map,
            seen,
            duplicate_identity,
            SHEET_MEETINGS,
            row_no,
        ):
            continue

        existing = None

        if company and contact and meeting_date is not None:
            existing = choose_candidate(
                SHEET_MEETINGS,
                row_no,
                identity,
                model.query.filter(
                    model.firm_name == company,
                    model.contact_no == contact,
                    model.date_of_meeting == meeting_date,
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "firm_name", "contact_no", "date_of_meeting"],
                "Multiple CRM Meetings matched company + contact + date",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and company and name and meeting_date is not None:
            existing = choose_candidate(
                SHEET_MEETINGS,
                row_no,
                identity,
                model.query.filter(
                    model.firm_name == company,
                    model.name == name,
                    model.date_of_meeting == meeting_date,
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "firm_name", "name", "date_of_meeting"],
                "Multiple CRM Meetings matched company + name + date",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and company and contact:
            existing = choose_candidate(
                SHEET_MEETINGS,
                row_no,
                identity,
                model.query.filter(
                    model.firm_name == company,
                    model.contact_no == contact,
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "firm_name", "contact_no", "date_of_meeting"],
                "Multiple CRM Meetings matched company + contact",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None and not company and name and contact and meeting_date is not None:
            existing = choose_candidate(
                SHEET_MEETINGS,
                row_no,
                identity,
                model.query.filter(
                    model.name == name,
                    model.contact_no == contact,
                    model.date_of_meeting == meeting_date,
                    model.record_owner == RECORD_OWNER,
                ),
                ["id", "name", "contact_no", "date_of_meeting"],
                "Multiple CRM Meetings matched name + contact + date",
            )

        if existing == "__AMBIGUOUS__":
            continue

        if existing is None:
            # No match is allowed to become a NEW meeting only
            # when there is a sufficiently strong identity.
            strong_identity = (
                (company and contact)
                or (company and name and meeting_date is not None)
                or (name and contact and meeting_date is not None)
            )

            if not strong_identity:
                add_review(
                    SHEET_MEETINGS,
                    row_no,
                    "Could not establish a reliable Meeting identity",
                    identity,
                )
                continue

        finish_row(
            SHEET_MEETINGS,
            row_no,
            incoming,
            existing,
            model,
            identity,
        )


# =========================================================
# SHEET PROCESSING
# =========================================================

def process_sheet(excel, sheet_name):
    normalized = sheet_name.strip()

    if normalized in SKIP_SHEETS:
        print(f"Skipping: {sheet_name}")
        return

    if normalized == SHEET_VISITS:
        df = read_sheet(excel, sheet_name)
        print(f"\nProcessing Visits: {len(df)} rows")
        import_visits(df)
        return

    if normalized == SHEET_SALES:
        df = read_sheet(excel, sheet_name)
        print(f"\nProcessing Sales: {len(df)} rows")
        import_sales(df)
        return

    if normalized == SHEET_INVOICE:
        df = read_sheet(excel, sheet_name)
        print(f"\nProcessing Invoice: {len(df)} rows")
        import_invoices(df)
        return

    if normalized == SHEET_DRAWINGS:
        df = read_sheet(excel, sheet_name)
        print(f"\nProcessing Drawings: {len(df)} rows")
        import_drawings(df)
        return

    if normalized == SHEET_LEADS:
        df = read_sheet(excel, sheet_name)
        print(f"\nProcessing Leads: {len(df)} rows")
        import_leads(df)
        return

    if normalized == SHEET_MEETINGS:
        df = read_sheet(excel, sheet_name)
        print(f"\nProcessing Sheet9 -> Meetings: {len(df)} rows")
        import_meetings(df)
        return

    print(f"Not imported: {sheet_name}")


# =========================================================
# MAIN
# =========================================================

def main():
    workbook_path = find_workbook()

    excel = pd.ExcelFile(workbook_path)

    print("=" * 80)
    print("AMAN SINGH WORKBOOK SYNC IMPORTER")
    print("=" * 80)
    print("Workbook :", workbook_path)
    print("Owner    :", RECORD_OWNER)
    print("Preview  :", PREVIEW_ONLY)
    print()

    print("Sheets found:")
    for sheet in excel.sheet_names:
        print(" -", sheet)

    with app.app_context():

        for sheet in excel.sheet_names:
            try:
                process_sheet(
                    excel,
                    sheet,
                )

                if PREVIEW_ONLY:
                    # Roll back all staged INSERT/UPDATE operations
                    # while retaining the report counters.
                    db.session.rollback()

                else:
                    db.session.commit()
                    print(f"Committed: {sheet}")

            except Exception as exc:
                db.session.rollback()

                traceback.print_exc()

                add_error(
                    sheet,
                    0,
                    exc,
                )

                print(
                    f"ERROR in {sheet}: {exc}"
                )

        if PREVIEW_ONLY:
            print(
                "\nPREVIEW MODE: "
                "NO DATABASE CHANGES WERE COMMITTED."
            )
        else:
            print(
                "\nSYNC COMPLETE: "
                "successfully processed sheets were committed."
            )

    save_report()


if __name__ == "__main__":
    main()


