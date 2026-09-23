"""
=========================================================
MeVaChi CRM
Aman Singh Workbook Importer
=========================================================

Workbook:
    excel/Aman.xlsx

Imports:
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

IMPORTANT:
- This script is intentionally self-contained.
- Do NOT change migration/config.py or migration/mappings.py for this import.
- Blank Excel cells do NOT erase existing database values during updates.
- Existing records are matched and updated when a reliable key exists.
- Unmatched rows are reported for manual review.
- Start with PREVIEW_ONLY = True.
"""

import os
import traceback
from datetime import datetime
from decimal import Decimal

import pandas as pd

from migration.database import (
    app,
    db,
    get_model,
)

from migration.utils import (
    clean_text,
    clean_phone,
    clean_int,
    clean_decimal,
    clean_date,
    is_empty,
)


# =========================================================
# AMAN SETTINGS
# =========================================================

EXCEL_FOLDER = "excel"
WORKBOOK_NAME = "Aman.xlsx"

RECORD_OWNER = "Aman Singh"

# Safe first run:
# True  = only analyse/report, no DB changes
# False = actually insert/update DB
PREVIEW_ONLY = True

# Existing DB rows are updated when matched and Excel has a
# non-empty changed value.
APPLY_UPDATES = True

LOG_FOLDER = "migration/logs"

# Sheets that must NOT be imported.
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
# REPORT
# =========================================================

stats = {}
errors = []
review_rows = []
changes = []


def init_sheet(sheet):
    if sheet not in stats:
        stats[sheet] = {
            "new": 0,
            "updated": 0,
            "unchanged": 0,
            "skipped": 0,
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


def add_review(sheet, row_no, reason, identity=None):
    review_rows.append({
        "sheet": sheet,
        "row": row_no,
        "reason": reason,
        "identity": identity or "",
    })


def save_report():
    os.makedirs(LOG_FOLDER, exist_ok=True)

    started = datetime.now()

    lines = []
    lines.append("=" * 75)
    lines.append("MeVaChi CRM - Aman Singh Migration Report")
    lines.append("=" * 75)
    lines.append(f"Generated : {started}")
    lines.append(f"Workbook  : {WORKBOOK_NAME}")
    lines.append(f"Owner     : {RECORD_OWNER}")
    lines.append(f"Preview   : {PREVIEW_ONLY}")
    lines.append("")

    lines.append("SUMMARY")
    lines.append("-" * 75)

    total_new = 0
    total_updated = 0
    total_unchanged = 0
    total_skipped = 0

    for sheet, data in stats.items():
        total_new += data["new"]
        total_updated += data["updated"]
        total_unchanged += data["unchanged"]
        total_skipped += data["skipped"]

        lines.append(
            f"{sheet:<28} "
            f"New: {data['new']:<5} "
            f"Updated: {data['updated']:<5} "
            f"Unchanged: {data['unchanged']:<5} "
            f"Skipped: {data['skipped']:<5}"
        )

    lines.append("")
    lines.append(f"TOTAL NEW       : {total_new}")
    lines.append(f"TOTAL UPDATED   : {total_updated}")
    lines.append(f"TOTAL UNCHANGED : {total_unchanged}")
    lines.append(f"TOTAL SKIPPED   : {total_skipped}")

    if changes:
        lines.append("")
        lines.append("=" * 75)
        lines.append("UPDATED RECORDS")
        lines.append("=" * 75)

        for item in changes:
            lines.append(
                f"[{item['sheet']}] Row {item['row']} | "
                f"{item['identity']} | "
                f"Changed: {', '.join(item['fields'])}"
            )

    if review_rows:
        lines.append("")
        lines.append("=" * 75)
        lines.append("ROWS REQUIRING MANUAL REVIEW")
        lines.append("=" * 75)

        for item in review_rows:
            lines.append(
                f"[{item['sheet']}] Row {item['row']} | "
                f"{item['reason']} | {item['identity']}"
            )

    if errors:
        lines.append("")
        lines.append("=" * 75)
        lines.append("ERRORS")
        lines.append("=" * 75)

        for item in errors:
            lines.append(
                f"[{item['sheet']}] Row {item['row']} : "
                f"{item['message']}"
            )
    else:
        lines.append("")
        lines.append("No errors found.")

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
# HELPERS
# =========================================================

def find_workbook():
    path = os.path.join(
        EXCEL_FOLDER,
        WORKBOOK_NAME,
    )

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

    # Preserve Unnamed columns because Aman Leads uses
    # Unnamed: 5 as the remarks/responses column.
    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    return df


def row_is_completely_empty(row):
    for value in row.values:
        if not is_empty(value):
            return False
    return True


def set_if_changed(existing, field, new_value, changed_fields):
    """
    Update only when Excel contains a value and that value differs.
    Blank Excel cells do not erase existing DB values.
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


def add_new(model, incoming):
    return model(**incoming)


def safe_identity(*values):
    values = [
        clean_text(v)
        for v in values
        if not is_empty(v)
    ]

    return " | ".join(values)


def finish_row(
    sheet,
    row_no,
    incoming,
    existing,
    model,
    identity,
):
    """
    Handle INSERT / UPDATE / UNCHANGED.
    """
    if existing:
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

    new_record = add_new(model, incoming)
    db.session.add(new_record)
    stat(sheet, "new")


# =========================================================
# VISITS
# =========================================================

def import_visits(df):
    model = get_model("Visit")

    for index, row in df.iterrows():
        row_no = index + 2

        if row_is_completely_empty(row):
            stat(SHEET_VISITS, "skipped")
            continue

        # Same business rule as the earlier importer:
        # ABC is required for a valid Visit row.
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
            incoming["contact_no"],
        )

        query = model.query.filter(
            model.record_owner == RECORD_OWNER,
            model.company_name == incoming["company_name"],
            model.person_name == incoming["person_name"],
            model.visit_date == incoming["visit_date"],
        )

        # If date is missing, include contact in the fallback
        # to reduce accidental matching of unrelated records.
        if incoming["visit_date"] is None:
            query = model.query.filter(
                model.record_owner == RECORD_OWNER,
                model.company_name == incoming["company_name"],
                model.person_name == incoming["person_name"],
                model.contact_no == incoming["contact_no"],
            )

        existing = query.first()

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

def import_sales(df):
    model = get_model("SalesPipeline")

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
            "site_incharge_contact": clean_phone(
                row.get("Contact.1")
            ),
            "first_contact": clean_date(
                row.get("First Contact")
            ),
            "last_contact": clean_date(
                row.get("Last Contact")
            ),
            "followup_date": clean_date(
                row.get("Followup Date")
            ),
            "no_of_site_visits": clean_int(
                row.get("No. of Site Visit")
            ),
            "area_covered": clean_decimal(
                row.get("Area Covered")
            ),
            "total_units": clean_int(
                row.get("Total Units")
            ),
            "price_of_units": clean_decimal(
                row.get("Price of Units")
            ),
            "first_year_cmc": clean_decimal(
                row.get("1st Yr. CMC")
            ),
            "installation": clean_decimal(
                row.get("Installation")
            ),
            "total_sensor": clean_int(
                row.get("Total Sensor")
            ),
            "sensor_cost": clean_decimal(
                row.get("Sensor Cost")
            ),
            "discount": clean_decimal(
                row.get("Discount")
            ),
            "revenue": clean_decimal(
                row.get("Revenue (₹)")
            ),
            "amount_received": clean_decimal(
                row.get("Received(₹)")
            ),
            "amount_due": clean_decimal(
                row.get("Due(₹)")
            ),
            "total_revenue": clean_decimal(
                row.get("Total Revenue")
            ),
            "gst_no": clean_text(row.get("GST No.")),
            "cmc_onwards": clean_decimal(
                row.get("CMC Onwards")
            ),
            "total_cmc": clean_decimal(
                row.get("Total CMC")
            ),
            "sales_person": None,
            "record_owner": RECORD_OWNER,
        }

        identity = safe_identity(
            incoming["name"],
            incoming["reference_no"],
        )

        if incoming["reference_no"]:
            existing = model.query.filter(
                model.reference_no ==
                incoming["reference_no"],
                model.record_owner ==
                RECORD_OWNER,
            ).first()

        else:
            existing = model.query.filter(
                model.name == incoming["name"],
                model.contact_no == incoming["contact_no"],
                model.project_type ==
                incoming["project_type"],
                model.record_owner ==
                RECORD_OWNER,
            ).first()

        if (
            existing is None
            and incoming["name"]
            and incoming["contact_no"]
            and incoming["project_type"]
        ):
            # Fallback only when the exact reference is absent.
            existing = model.query.filter(
                model.name == incoming["name"],
                model.contact_no == incoming["contact_no"],
                model.record_owner ==
                RECORD_OWNER,
            ).first()

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

def import_invoices(df):
    model = get_model("Invoice")

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
            "price_of_units": clean_decimal(
                row.get("Price of Units")
            ),
            "first_year_cmc": clean_decimal(
                row.get("1st Yr. CMC")
            ),
            "installation": clean_decimal(
                row.get("Installation")
            ),
            "total_sensor": clean_int(
                row.get("Total Sensor")
            ),
            "sensor_cost": clean_decimal(
                row.get("Sensor Cost")
            ),
            "revenue": clean_decimal(
                row.get("Revenue (₹)")
            ),
            "total_revenue": clean_decimal(
                row.get("Total Revenue")
            ),
            "record_owner": RECORD_OWNER,
        }

        identity = safe_identity(
            incoming["name"],
            incoming["invoice_no"],
        )

        if incoming["invoice_no"]:
            existing = model.query.filter(
                model.invoice_no ==
                incoming["invoice_no"],
                model.record_owner ==
                RECORD_OWNER,
            ).first()

        else:
            existing = model.query.filter(
                model.name == incoming["name"],
                model.doi == incoming["doi"],
                model.record_owner ==
                RECORD_OWNER,
            ).first()

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

def import_drawings(df):
    model = get_model("Drawing")

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
            "iterations": clean_int(
                row.get("No. of Iteration")
            ),
            "moca": clean_text(row.get("MODM")),
            "record_owner": RECORD_OWNER,
        }

        identity = safe_identity(
            incoming["name"],
            incoming["address"],
        )

        existing = model.query.filter(
            model.name == incoming["name"],
            model.address == incoming["address"],
            model.record_owner ==
            RECORD_OWNER,
        ).first()

        # If one of name/address is missing, use the other
        # value as a fallback rather than creating duplicates.
        if existing is None and incoming["name"]:
            existing = model.query.filter(
                model.name == incoming["name"],
                model.record_owner ==
                RECORD_OWNER,
            ).first()

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

def import_leads(df):
    model = get_model("Lead")

    for index, row in df.iterrows():
        row_no = index + 2

        if row_is_completely_empty(row):
            stat(SHEET_LEADS, "skipped")
            continue

        name = clean_text(row.get("Name"))

        if not name:
            stat(SHEET_LEADS, "skipped")
            continue

        # IMPORTANT:
        # The column immediately after Contact in Aman.xlsx is
        # Unnamed: 5. User specifically wants its values in
        # the CRM's remarks/responses field.
        remarks = clean_text(
            row.get("Unnamed: 5")
        )

        # Address + Location are combined into the existing
        # Lead.location field.
        location_parts = []

        location = clean_text(row.get("Location"))
        address = clean_text(row.get("Address"))

        if location:
            location_parts.append(location)

        if address and address not in location_parts:
            location_parts.append(address)

        combined_location = (
            ", ".join(location_parts)
            if location_parts
            else None
        )

        incoming = {
            "name": name,
            "reference": None,
            "location": combined_location,
            "phone": clean_phone(row.get("Contact")),
            "responses": remarks,
            "next_action": None,
            "date_of_1st_followup": None,
            "next_to_call": None,
            "recent": None,
            "record_owner": RECORD_OWNER,
        }

        identity = safe_identity(
            incoming["name"],
            incoming["phone"],
        )

        # Strong match when phone exists.
        if incoming["phone"]:
            existing = model.query.filter(
                model.name == incoming["name"],
                model.phone == incoming["phone"],
                model.record_owner ==
                RECORD_OWNER,
            ).first()

            # If the same named person has no phone in DB,
            # use name as a fallback.
            if existing is None:
                existing = model.query.filter(
                    model.name == incoming["name"],
                    model.record_owner ==
                    RECORD_OWNER,
                ).first()

        else:
            existing = model.query.filter(
                model.name == incoming["name"],
                model.record_owner ==
                RECORD_OWNER,
            ).first()

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

def import_meetings(df):
    model = get_model("Meeting")

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

        # A row with no meaningful meeting data is skipped.
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
            "designation": clean_text(
                row.get("Designation")
            ),
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

        # Matching strategy:
        # 1. Company + contact + date
        # 2. Company + name + date
        # 3. If date is missing, company + contact
        # 4. If no company, name + contact + date
        existing = None

        if company and contact and meeting_date:
            existing = model.query.filter(
                model.firm_name == company,
                model.contact_no == contact,
                model.date_of_meeting == meeting_date,
                model.record_owner ==
                RECORD_OWNER,
            ).first()

        if existing is None and company and name and meeting_date:
            existing = model.query.filter(
                model.firm_name == company,
                model.name == name,
                model.date_of_meeting == meeting_date,
                model.record_owner ==
                RECORD_OWNER,
            ).first()

        if existing is None and company and contact and not meeting_date:
            existing = model.query.filter(
                model.firm_name == company,
                model.contact_no == contact,
                model.record_owner ==
                RECORD_OWNER,
            ).first()

        if existing is None and not company and name and contact:
            existing = model.query.filter(
                model.name == name,
                model.contact_no == contact,
                model.record_owner ==
                RECORD_OWNER,
            ).first()

        # If there is a very weak identity, don't risk updating
        # an unrelated existing meeting.
        if existing is None:
            has_strong_identity = (
                (company and contact)
                or (company and name and meeting_date)
                or (name and contact and meeting_date)
            )

            if not has_strong_identity:
                add_review(
                    SHEET_MEETINGS,
                    row_no,
                    "Could not establish a strong matching key",
                    identity,
                )

                # It is still safe to import as NEW if the row
                # contains meaningful data, but we mark it for
                # manual review in the report.
                stat(SHEET_MEETINGS, "new")
                db.session.add(
                    add_new(model, incoming)
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
        print(f"\nProcessing Invoices: {len(df)} rows")
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

    print("=" * 75)
    print("AMAN SINGH WORKBOOK IMPORTER")
    print("=" * 75)
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
                    # Discard this sheet's staged changes.
                    db.session.rollback()

                else:
                    # COMMIT_EVERY_SHEET behaviour.
                    db.session.commit()

                    print(
                        f"Committed: {sheet}"
                    )

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
                "No database changes were committed."
            )
        else:
            print(
                "\nAll successfully processed sheets "
                "were committed."
            )

    save_report()


if __name__ == "__main__":
    main()
