"""
=========================================================
Import Itat Workbook
=========================================================
"""

import traceback
import pandas as pd

from migration.config import *
from migration.mappings import *
from migration.database import *
from migration.utils import *
from migration.report import MigrationReport

# ==========================================================
# LOAD WORKBOOK
# ==========================================================

excel = pd.ExcelFile(

    f"{EXCEL_FOLDER}/{WORKBOOK_NAME}"

)

report = MigrationReport()

print("=" * 70)
print(f"Workbook : {EXCEL_FOLDER}/{WORKBOOK_NAME}")
print("=" * 70)

print("\nSheets Found\n")

for sheet in excel.sheet_names:

    print("-", sheet)

print("\n")

# ==========================================================
# PREVIEW MODE
# ==========================================================

PREVIEW_ONLY = False

# ==========================================================
# PREVIEW LEADS
# ==========================================================

def preview_leads(leads):

    print()

    print("=" * 70)
    print("FIRST 3 LEADS")
    print("=" * 70)

    for i, lead in enumerate(leads[:3], start=1):

        print()

        print(f"Lead {i}")

        print("-" * 70)

        print("Name          :", lead.name)
        print("Location      :", lead.location)
        print("Phone         :", lead.phone)
        print("Responses     :")
        print(lead.responses)
        print("Next Action   :", lead.next_action)
        print("Record Owner  :", lead.record_owner)

    print()

    print("=" * 70)
    print(f"TOTAL LEADS READY : {len(leads)}")
    print("=" * 70)

    print()

# ==========================================================
# PREVIEW PROPOSALS
# ==========================================================

def preview_proposals(proposals):

    print()

    print("=" * 70)
    print("FIRST 3 PROPOSALS")
    print("=" * 70)

    for i, proposal in enumerate(proposals[:3], start=1):

        print()

        print(f"Proposal {i}")

        print("-" * 70)

        print("Name             :", proposal.name)
        print("Contact Person   :", proposal.contact_person)
        print("Contact Number   :", proposal.phone_no_contact_person)
        print("Email            :", proposal.email)
        print("Site Address     :", proposal.site_address)
        print("Product          :", proposal.product)
        print("Total Amount     :", proposal.total_amount)
        print("Remarks          :", proposal.remarks)
        print("Next Action      :", proposal.next_action)
        print("Record Owner     :", proposal.record_owner)

    print()

    print("=" * 70)
    print(f"TOTAL PROPOSALS READY : {len(proposals)}")
    print("=" * 70)

    print()

# ==========================================================
# IMPORT LEADS
# ==========================================================

def import_leads(df):

    Lead = get_model("Lead")

    leads = []

    for _, row in df.iterrows():

    # --------------------------------------------------
    # Skip Empty / Total Row
    # --------------------------------------------------

        client_name = clean_text(
            row.get("CLIENT NAME")
        )

        if not client_name:

            report.skipped("Leads")

            continue

        if "total quotation" in client_name.lower():

            report.skipped("Leads")

            continue

        # --------------------------------------------------
        # Build Responses
        # --------------------------------------------------

        response_parts = []

        remarks = clean_text(
            row.get("REMARKS")
        )

        if remarks:

            response_parts.append(
                f"Remarks: {remarks}"
            )

        contact_person = clean_text(
            row.get("CONTACT PERSON")
        )

        if contact_person:

            response_parts.append(
                f"Contact Person: {contact_person}"
            )

        designation = clean_text(
            row.get("DESIGNATION")
        )

        if designation:

            response_parts.append(
                f"Designation: {designation}"
            )

        email = clean_text(
            row.get("EMAIL ID")
        )

        if email:

            response_parts.append(
                f"Email: {email}"
            )

        amount = clean_decimal(
            row.get("Amount")
        )

        if amount is not None:

            response_parts.append(
                f"Amount Without GST: ₹{amount:,.2f}"
            )

        responses = "\n\n".join(
            response_parts
        )

        # --------------------------------------------------
        # Next Action
        # --------------------------------------------------

        tentative_closer = clean_text(
            row.get("Tentative closer")
        )

        next_action = None

        if tentative_closer:

            next_action = (
                f"Tentative Closer: {tentative_closer}"
            )

        # --------------------------------------------------
        # Create Lead
        # --------------------------------------------------

        lead = Lead(

            name=client_name,

            location=clean_text(
                row.get("LOCALITY")
            ),

            phone=clean_phone(
                row.get("CONTACT NUMBER")
            ),

            responses=responses,

            next_action=next_action,

            reference=None,

            date_of_1st_followup=None,

            next_to_call=None,

            recent=None,

            record_owner=RECORD_OWNER

        )

        # --------------------------------------------------
        # Duplicate Check
        # --------------------------------------------------

        existing = Lead.query.filter_by(

            name=lead.name,

            phone=lead.phone,

            record_owner=lead.record_owner

        ).first()

        if existing:

            report.skipped("Leads")

            continue

        leads.append(lead)

        report.imported("Leads")

    preview_leads(leads)

    return leads

# ==========================================================
# IMPORT PROPOSALS
# ==========================================================

def import_proposals(df):

    Proposal = get_model("Proposal")

    proposals = []

    for _, row in df.iterrows():

    # --------------------------------------------------
    # Skip Empty / Total Row
    # --------------------------------------------------

        client_name = clean_text(
            row.get("CLIENT NAME")
        )
  
        if not client_name:

            report.skipped("Proposals")

            continue

        if "total quotation" in client_name.lower():

            report.skipped("Proposals")

            continue

        # --------------------------------------------------
        # Next Action
        # --------------------------------------------------

        tentative_closer = clean_text(
            row.get("Tentative closer")
        )

        next_action = None

        if tentative_closer:

            next_action = (
                f"Tentative Closer: {tentative_closer}"
            )

        # --------------------------------------------------
        # Create Proposal
        # --------------------------------------------------

        proposal = Proposal(

            name=client_name,

            site_address=clean_text(
                row.get("LOCALITY")
            ),

            contact_person=clean_text(
                row.get("CONTACT PERSON")
            ),

            phone_no_contact_person=clean_phone(
                row.get("CONTACT NUMBER")
            ),

            email=clean_text(
                row.get("EMAIL ID")
            ),

            remarks=clean_text(
                row.get("REMARKS")
            ),

            next_action=next_action,

            total_amount=clean_decimal(
                row.get("Amount")
            ),

            product="Molecular Filters",

            record_owner=RECORD_OWNER,

            # ----------------------------------------------
            # Remaining fields
            # ----------------------------------------------

            reference_no=None,

            phone_no_client=None,

            source=None,

            type=None,

            reference_source_details=None,

            phone_no_source=None,

            state=None,

            total_area_sqft=None,

            type_of_units=None,

            no_of_mvd_units=None,

            no_of_mvd_max_units=None,

            total_no_of_units=None,

            cost_total_per_unit=None,

            no_of_monitors=None,

            cmc=None,

            per_unit_cost=None,

            per_unit_cost_max_unit=None,

            cmc_cost=None,

            monitor_cost=None,

            installation_cost=None,

            final_amount=None,

            discount=None,

            cmc_starting_period=None,

            date_of_proposal_sent=None,

            proposal_prepared_by=None,

            proposal_shared_by=None,

            status="Proposal Submit",

            date_of_last_followup=None,

            next_to_call=None,

            area_covered=None,

            area_not_covered=None,

            meeting_id=None,

            drawing_id=None

        )

        # --------------------------------------------------
        # Duplicate Check
        # --------------------------------------------------

        existing = Proposal.query.filter_by(

            name=proposal.name,

            phone_no_contact_person=proposal.phone_no_contact_person,

            record_owner=proposal.record_owner

        ).first()

        if existing:

            report.skipped("Proposals")

            continue

        proposals.append(proposal)

        report.imported("Proposals")

    preview_proposals(proposals)

    return proposals

# ==========================================================
# PROCESS SHEET
# ==========================================================

def process_sheet(sheet_name):

    print()

    print("=" * 70)
    print(f"Processing : {sheet_name}")
    print("=" * 70)

    # --------------------------------------------------
    # Skip unwanted sheets
    # --------------------------------------------------

    if sheet_name in SKIP_SHEETS:

        print("Skipped.\n")

        return

    # --------------------------------------------------
    # Read Sheet
    # --------------------------------------------------

    df = pd.read_excel(

        excel,

        sheet_name=sheet_name

    )

    df.columns = df.columns.str.strip()

    print(f"Rows    : {len(df)}")
    print(f"Columns : {len(df.columns)}")

    # --------------------------------------------------
    # Import Objects
    # --------------------------------------------------

    leads = import_leads(df)

    proposals = import_proposals(df)

    # --------------------------------------------------
    # Preview Only
    # --------------------------------------------------

    if PREVIEW_ONLY:

        print("\nPreview Mode Enabled")
        print("Nothing has been inserted into the database.\n")

        return

    # --------------------------------------------------
    # Insert into Database
    # --------------------------------------------------

    try:

        print("\nImporting Leads...")

        for lead in leads:

            db.session.add(lead)

        print("Importing Proposals...")

        for proposal in proposals:

            db.session.add(proposal)

        db.session.commit()

        print()

        print(f"{len(leads)} Leads Imported Successfully.")

        print(f"{len(proposals)} Proposals Imported Successfully.\n")

    except Exception as e:

        db.session.rollback()

        traceback.print_exc()

        report.error(

            "Import",

            0,

            str(e)

        )

# ==========================================================
# MAIN
# ==========================================================

def main():

    with app.app_context():

        for sheet in excel.sheet_names:

            try:

                process_sheet(sheet)

            except Exception as e:

                traceback.print_exc()

                report.error(

                    sheet,

                    0,

                    str(e)

                )

        report.generate()

if __name__ == "__main__":

    main()