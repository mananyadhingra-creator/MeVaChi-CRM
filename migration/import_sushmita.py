"""
=========================================================
MeVaChi CRM
Sushmita Workbook Importer
=========================================================
"""

import os
import traceback
import pandas as pd

from migration.config import (
    EXCEL_FOLDER,
    WORKBOOK_NAME,
    DRY_RUN
)

from migration.mappings import (
    SKIP_SHEETS,
    IMPORT_RULES,
    RECORD_OWNER
)

from migration.database import (
    app,
    db,
    get_model
)

from migration.report import MigrationReport

from migration.utils import (
    clean_text,
    clean_phone,
    clean_int,
    clean_decimal,
    clean_date,
    combine_fields,
    is_empty
)

report = MigrationReport()


# ==========================================================
# FIND WORKBOOK
# ==========================================================

def find_workbook():

    workbook = os.path.join(
        EXCEL_FOLDER,
        WORKBOOK_NAME
    )

    if not os.path.exists(workbook):
        raise FileNotFoundError(
            f"{WORKBOOK_NAME} not found."
        )

    return workbook


# ==========================================================
# LOAD WORKBOOK
# ==========================================================

workbook_path = find_workbook()

excel = pd.ExcelFile(workbook_path)

print("=" * 70)
print("Workbook :", workbook_path)
print("=" * 70)

print("\nSheets Found\n")

for sheet in excel.sheet_names:
    print("-", sheet)

print()


# ==========================================================
# REMOVE USELESS COLUMNS
# ==========================================================

def clean_dataframe(df):

    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]

    df = df.loc[
        :,
        df.columns.astype(str).str.strip() != ""
    ]

    return df


# ==========================================================
# PREVIEW
# ==========================================================



# ==========================================================
# PREVIEW LEADS
# ==========================================================

def preview_leads(leads):

    print("\n")

    print("=" * 70)
    print("FIRST 3 LEADS")
    print("=" * 70)

    for i, lead in enumerate(leads[:3], start=1):

        print()

        print(f"Lead {i}")

        print("-" * 70)

        print("Name               :", lead.name)
        print("Reference          :", lead.reference)
        print("Location           :", lead.location)
        print("Phone              :", lead.phone)
        print("Responses          :", lead.responses)
        print("1st Followup       :", lead.date_of_1st_followup)
        print("Next To Call       :", lead.next_to_call)
        print("Recent             :", lead.recent)
        print("Record Owner       :", lead.record_owner)

    print()

    print("=" * 70)
    print(f"TOTAL LEADS READY : {len(leads)}")
    print("=" * 70)

    print()

# ==========================================================
# PREVIEW MEETINGS
# ==========================================================

def preview_meetings(meetings):

    print("\n")

    print("=" * 70)
    print("FIRST 3 MEETINGS")
    print("=" * 70)

    for i, meeting in enumerate(meetings[:3], start=1):

        print()

        print(f"Meeting {i}")

        print("-" * 70)

        print("Meeting Fixed By   :", meeting.meeting_fixed_by)
        print("Source             :", meeting.source)
        print("Name               :", meeting.name)
        print("Reference          :", meeting.reference)
        print("Firm Name          :", meeting.firm_name)
        print("Designation        :", meeting.designation)
        print("Address            :", meeting.address)
        print("State              :", meeting.state)
        print("Contact            :", meeting.contact_no)
        print("Email              :", meeting.email)
        print("Meeting Date       :", meeting.date_of_meeting)
        print("Mode               :", meeting.mode_of_meeting)
        print("Meeting Status     :", meeting.meeting_status)
        print("Conducted By       :", meeting.meeting_conducted_by)
        print("Last Followup      :", meeting.date_of_last_followup)
        print("Next Call          :", meeting.date_to_call_next)
        print("Final Remarks      :", meeting.final_remarks)
        print("Reschedule Date    :", meeting.reschedule_date)
        print("Reason             :", meeting.reason_for_reschedule)
        print("Remarks            :", meeting.remarks)
        print("Record Owner       :", meeting.record_owner)

    print()

    print("=" * 70)
    print(f"TOTAL MEETINGS READY : {len(meetings)}")
    print("=" * 70)

    print()

# ==========================================================
# PREVIEW PROPOSALS
# ==========================================================

def preview_proposals(proposals):

    print("\n")

    print("=" * 70)
    print("FIRST 3 PROPOSALS")
    print("=" * 70)

    for i, proposal in enumerate(proposals[:3], start=1):

        print()

        print(f"Proposal {i}")

        print("-" * 70)

        print("Reference No        :", proposal.reference_no)
        print("Name                :", proposal.name)
        print("Phone               :", proposal.phone_no_client)
        print("Source              :", proposal.source)
        print("Type                :", proposal.type)
        print("Reference Details   :", proposal.reference_source_details)
        print("Contact Person      :", proposal.contact_person)
        print("Email               :", proposal.email)
        print("Site Address        :", proposal.site_address)
        print("State               :", proposal.state)
        print("Area (sqft)         :", proposal.total_area_sqft)
        print("Product             :", proposal.product)
        print("Total Units         :", proposal.total_no_of_units)
        print("Total Amount        :", proposal.total_amount)
        print("Discount            :", proposal.discount)
        print("Final Amount        :", proposal.final_amount)
        print("Proposal Date       :", proposal.date_of_proposal_sent)
        print("Prepared By         :", proposal.proposal_prepared_by)
        print("Shared By           :", proposal.proposal_shared_by)
        print("Status              :", proposal.status)
        print("Last Followup       :", proposal.date_of_last_followup)
        print("Next Call           :", proposal.next_to_call)
        print("Record Owner        :", proposal.record_owner)

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

    df = clean_dataframe(df)

    leads = []

    for _, row in df.iterrows():

        # -----------------------------------------
        # Import if Name OR Reference exists
        # -----------------------------------------

        if (

            is_empty(row.get("Name"))

            and

            is_empty(row.get("Reference"))

        ):

            report.skipped("Leads")

            continue

        lead = Lead(

            name=clean_text(
                row.get("Name")
            ),

            reference=clean_text(
                row.get("Reference")
            ),

            location=clean_text(
                row.get("Location")
            ),

            phone=clean_phone(
                row.get("Phone")
            ),

            responses=clean_text(
                row.get("Responses (6-May-26)")
            ),

            next_action=None,

            date_of_1st_followup=clean_date(
                row.get("Date of lst flw up")
            ),

            next_to_call=clean_date(
                row.get("Next to cl")
            ),

            recent=clean_text(
                row.get("Recent")
            ),

            record_owner=RECORD_OWNER

        )

        # -----------------------------------------
        # DUPLICATE CHECK
        # -----------------------------------------

        if not PREVIEW_ONLY:

            existing = None

            if lead.reference and lead.reference.strip():

                existing = Lead.query.filter_by(

                    reference=lead.reference.strip(),

                    record_owner=lead.record_owner

                ).first()

            if existing is None:

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
# IMPORT MEETINGS
# ==========================================================

def import_meetings(df):

    Meeting = get_model("Meeting")

    df = clean_dataframe(df)

    meetings = []

    for _, row in df.iterrows():

        # -----------------------------------------
        # Import if Meeting Fixed By OR
        # Name OR Firm Name exists
        # -----------------------------------------

        if (

            is_empty(row.get("Meeting Fixed By"))

            and

            is_empty(row.get("Name"))

            and

            is_empty(row.get("Firm Name"))

        ):

            report.skipped("Meetings")

            continue

        meeting = Meeting(

            meeting_fixed_by=clean_text(
                row.get("Meeting Fixed By")
            ),

            source=clean_text(
                row.get("Source")
            ),

            name=clean_text(
                row.get("Name")
            ),

            reference=clean_text(
                row.get("Reference")
            ),

            firm_name=clean_text(
                row.get("Firm Name")
            ),

            designation=clean_text(
                row.get("Designation")
            ),

            address=clean_text(
                row.get("Address")
            ),

            state=clean_text(
                row.get("State")
            ),

            contact_no=clean_phone(
                row.get("Contact No.")
            ),

            email=clean_text(
                row.get("Email")
            ),

            company_info_shared=clean_text(
                row.get("Company Info Shared")
            ),

            meeting_fixed=clean_text(
                row.get("Meeting Fixed")
            ),

            date_of_meeting=clean_date(
                row.get("Date of Meeting")
            ),

            mode_of_meeting=clean_text(
                row.get("Mode of Meeting")
            ),

            meeting_status=clean_text(
                row.get("Meeting Status")
            ),

            meeting_conducted_by=clean_text(
                row.get("Meeting Conducted By")
            ),

            floor_plan_shared=clean_text(
                row.get("Floor Plan Shared")
            ),

            site_visit=clean_text(
                row.get("Site Visit (Y/N)")
            ),

            post_meeting_mail=clean_text(
                row.get("Post-Meeting Mail")
            ),

            date_of_last_followup=clean_date(
                row.get("Date of Last Follow-up")
            ),

            date_to_call_next=clean_date(
                row.get("Date to cl next")
            ),

            final_remarks=clean_text(
                row.get("Final Remarks")
            ),

            reschedule_date=clean_date(
                row.get("Rescheduled Date")
            ),

            reason_for_reschedule=clean_text(
                row.get("Reason for Rescheduling")
            ),

            remarks=clean_text(
                row.get("Remarks")
            ),

            next_action=None,

            lead_id=None,

            record_owner=RECORD_OWNER

        )

        # -----------------------------------------
        # DUPLICATE CHECK
        # -----------------------------------------

        if not PREVIEW_ONLY:

            existing = None

            if meeting.reference and meeting.reference.strip():

                existing = Meeting.query.filter_by(

                    reference=meeting.reference.strip(),

                    record_owner=meeting.record_owner

                ).first()

            if existing is None:

                existing = Meeting.query.filter_by(

                    name=meeting.name,

                    firm_name=meeting.firm_name,

                    date_of_meeting=meeting.date_of_meeting,

                    record_owner=meeting.record_owner

                ).first()

            if existing:

                report.skipped("Meetings")

                continue

        meetings.append(meeting)

        report.imported("Meetings")

    preview_meetings(meetings)

    return meetings

# ==========================================================
# IMPORT PROPOSALS
# ==========================================================

def import_proposals(df):

    Proposal = get_model("Proposal")

    df = clean_dataframe(df)

    proposals = []

    for _, row in df.iterrows():

        # -----------------------------------------
        # Import if Name OR Reference No. exists
        # -----------------------------------------

        if (

            is_empty(row.get("Name"))

            and

            is_empty(row.get("Reference no."))

        ):

            report.skipped("Proposals")

            continue

        proposal = Proposal(

            reference_no=clean_text(
                row.get("Reference no.")
            ),

            name=clean_text(
                row.get("Name")
            ),

            phone_no_client=clean_phone(
                row.get("Phone No. (Client)")
            ),

            source=clean_text(
                row.get("Source")
            ),

            type=clean_text(
                row.get("Type")
            ),

            reference_source_details=clean_text(
                row.get("Reference")
            ),

            phone_no_source=clean_phone(
                row.get("Phone No. (Source)")
            ),

            contact_person=clean_text(
                row.get("Contact Person (Name / Designation)")
            ),

            phone_no_contact_person=clean_phone(
                row.get("Phone No. (Contact P.)")
            ),

            email=clean_text(
                row.get("Email")
            ),

            site_address=clean_text(
                row.get("Site Address")
            ),

            state=clean_text(
                row.get("State")
            ),

            total_area_sqft=clean_decimal(
                row.get("Total Area (sq. ft.)")
            ),

            area_covered=clean_text(
                row.get("Area Covered")
            ),

            area_not_covered=clean_text(
                row.get("Area not Considered")
            ),

            type_of_units=clean_text(
                row.get("Type of Units")
            ),

            no_of_mvd_units=clean_int(
                row.get("No. of MVC Units")
            ),

            no_of_mvd_max_units=clean_int(
                row.get("No. of MVC Max Units")
            ),

            total_no_of_units=clean_int(
                row.get("Total No. of Units")
            ),

            product=clean_text(
                row.get("Product")
            ),

            cost_total_per_unit=clean_text(
                row.get("Cost (Total/ Per Unit)")
            ),

            no_of_monitors=clean_int(
                row.get("No. of Monitors")
            ),

            cmc=clean_text(
                row.get("CMC")
            ),

            per_unit_cost=clean_decimal(
                row.get("Per Unit Cost")
            ),

            per_unit_cost_max_unit=clean_decimal(
                row.get("Per Unit Cost - Max Unit")
            ),

            cmc_cost=clean_decimal(
                row.get("CMC Cost")
            ),

            monitor_cost=clean_decimal(
                row.get("Monitor Cost")
            ),

            installation_cost=clean_decimal(
                row.get("Installation")
            ),

            total_amount=clean_decimal(
                row.get("Total Amount")
            ),

            cmc_starting_period=clean_text(
                row.get("CMC Starting Period")
            ),

            discount=clean_decimal(
                row.get("Discount")
            ),

            final_amount=clean_decimal(
                row.get("Final Amount")
            ),

            date_of_proposal_sent=clean_date(
                row.get("Date of Proposal Sent")
            ),

            proposal_prepared_by=clean_text(
                row.get("Proposal Prepared By")
            ),

            proposal_shared_by=clean_text(
                row.get("Proposal Shared By")
            ),

            status=clean_text(
                row.get("Status")
            ),

            date_of_last_followup=clean_date(
                row.get("Date of Last Follow-up")
            ),

            next_to_call=clean_date(
                row.get("Next to cl")
            ),

            remarks=clean_text(
                row.get("Remarks")
            ),

            next_action=None,

            meeting_id=None,

            drawing_id=None,

            record_owner=RECORD_OWNER

        )

        # -----------------------------------------
        # DUPLICATE CHECK
        # -----------------------------------------

        if not PREVIEW_ONLY:

            existing = None

            if proposal.reference_no and proposal.reference_no.strip():

                existing = Proposal.query.filter_by(

                    reference_no=proposal.reference_no.strip(),

                    record_owner=proposal.record_owner

                ).first()

            if existing is None:

                existing = Proposal.query.filter_by(

                    name=proposal.name,

                    site_address=proposal.site_address,

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

PREVIEW_ONLY = True


def process_sheet(sheet_name):

    print("\n")
    print("=" * 70)
    print(f"Processing : {sheet_name}")
    print("=" * 70)

    sheet_key = sheet_name.strip()

    if sheet_key in SKIP_SHEETS:

        print("Skipped.\n")

        return

    if sheet_key not in IMPORT_RULES:

        print("No mapping found.\n")

        return

    rule = IMPORT_RULES[sheet_key]

    df = pd.read_excel(
        excel,
        sheet_name=sheet_name
    )

    print(f"Rows    : {len(df)}")
    print(f"Columns : {len(df.columns)}")

    # -----------------------------------------------------
    # LEADS
    # -----------------------------------------------------

    if rule["table"] == "Lead":

        leads = import_leads(df)

        if PREVIEW_ONLY:

            print("\nPreview Mode Enabled")
            print("Nothing has been inserted into the database.\n")

            return

        try:

            print("\nImporting Leads...")

            for lead in leads:

                db.session.add(lead)

            db.session.commit()

            print(f"\n{len(leads)} Leads Imported Successfully.\n")

        except Exception as e:

            db.session.rollback()

            print("\nERROR OCCURRED\n")

            traceback.print_exc()

            report.error(
                "Leads",
                0,
                str(e)
            )

        return

    # -----------------------------------------------------
    # MEETINGS
    # -----------------------------------------------------

    if rule["table"] == "Meeting":

        meetings = import_meetings(df)

        if PREVIEW_ONLY:

            print("\nPreview Mode Enabled")
            print("Nothing has been inserted into the database.\n")

            return

        try:

            print("\nImporting Meetings...")

            for meeting in meetings:

                db.session.add(meeting)

            db.session.commit()

            print(f"\n{len(meetings)} Meetings Imported Successfully.\n")

        except Exception as e:

            db.session.rollback()

            print("\nERROR OCCURRED\n")

            traceback.print_exc()

            report.error(
                "Meetings",
                0,
                str(e)
            )

        return
    # -----------------------------------------------------
    # PROPOSALS
    # -----------------------------------------------------

    if rule["table"] == "Proposal":

        proposals = import_proposals(df)

        if PREVIEW_ONLY:

            print("\nPreview Mode Enabled")
            print("Nothing has been inserted into the database.\n")

            return

        try:

            print("\nImporting Proposals...")

            for proposal in proposals:

                db.session.add(proposal)

            db.session.commit()

            print(
                f"\n{len(proposals)} Proposals Imported Successfully.\n"
            )

        except Exception as e:

            db.session.rollback()

            print("\nERROR OCCURRED\n")

            traceback.print_exc()

            report.error(

                "Proposals",

                0,

                str(e)

            )

        return

    print("Importer not written yet for this sheet.\n")




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