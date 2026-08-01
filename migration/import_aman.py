"""
=========================================================
MeVaChi CRM
Aman Workbook Importer
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

def preview_visits(visits):

    print("\n")
    print("=" * 70)
    print("FIRST 3 VISITS")
    print("=" * 70)

    for i, visit in enumerate(visits[:3], start=1):

        print()

        print(f"Visit {i}")

        print("-" * 70)

        print("State           :", visit.state)
        print("Region          :", visit.region)
        print("ABC             :", visit.abc)
        print("Company         :", visit.company_name)
        print("Person          :", visit.person_name)
        print("Designation     :", visit.designation)
        print("Contact         :", visit.contact_no)
        print("Address         :", visit.address)
        print("Brief           :", visit.brief)
        print("Visit Date      :", visit.visit_date)
        print("Leads Generated :", visit.leads_generated)
        print("M2              :", visit.m2)
        print("M3              :", visit.m3)
        print("Record Owner    :", visit.record_owner)

    print()
    print("=" * 70)
    print(f"TOTAL VISITS READY : {len(visits)}")
    print("=" * 70)
    print()

# ==========================================================
# PREVIEW SALES
# ==========================================================

def preview_sales(sales):

    print("\n")
    print("=" * 70)
    print("FIRST 3 SALES")
    print("=" * 70)

    for i, sale in enumerate(sales[:3], start=1):

        print()

        print(f"Sale {i}")

        print("-" * 70)

        print("Name             :", sale.name)
        print("Reference No     :", sale.reference_no)
        print("Project Stage    :", sale.project_stage)
        print("MOC              :", sale.moc)
        print("Source           :", sale.source)
        print("Address          :", sale.address)
        print("Project Type     :", sale.project_type)
        print("Category         :", sale.category)
        print("Contact          :", sale.contact_no)
        print("Revenue          :", sale.revenue)
        print("Total Revenue    :", sale.total_revenue)
        print("Record Owner     :", sale.record_owner)

    print()

    print("=" * 70)

    print(f"TOTAL SALES READY : {len(sales)}")

    print("=" * 70)

    print()

# ==========================================================
# PREVIEW INVOICES
# ==========================================================

def preview_invoices(invoices):

    print("\n")

    print("=" * 70)
    print("FIRST 3 INVOICES")
    print("=" * 70)

    for i, invoice in enumerate(invoices[:3], start=1):

        print()

        print(f"Invoice {i}")

        print("-" * 70)

        print("Name             :", invoice.name)
        print("DOI              :", invoice.doi)
        print("Invoice No       :", invoice.invoice_no)
        print("GST No           :", invoice.gst_no)
        print("Product Sold     :", invoice.product_sold)
        print("Total Units      :", invoice.total_units)
        print("Price of Units   :", invoice.price_of_units)
        print("1st Yr CMC       :", invoice.first_year_cmc)
        print("Installation     :", invoice.installation)
        print("Total Sensor     :", invoice.total_sensor)
        print("Sensor Cost      :", invoice.sensor_cost)
        print("Revenue          :", invoice.revenue)
        print("Total Revenue    :", invoice.total_revenue)
        print("Record Owner     :", invoice.record_owner)

    print()

    print("=" * 70)
    print(f"TOTAL INVOICES READY : {len(invoices)}")
    print("=" * 70)

    print()

# ==========================================================
# PREVIEW DRAWINGS
# ==========================================================

def preview_drawings(drawings):

    print("\n")

    print("=" * 70)
    print("FIRST 3 DRAWINGS")
    print("=" * 70)

    for i, drawing in enumerate(drawings[:3], start=1):

        print()

        print(f"Drawing {i}")

        print("-" * 70)

        print("Name          :", drawing.name)
        print("Address       :", drawing.address)
        print("Iterations    :", drawing.iterations)
        print("MOCA          :", drawing.moca)
        print("Record Owner  :", drawing.record_owner)

    print()

    print("=" * 70)
    print(f"TOTAL DRAWINGS READY : {len(drawings)}")
    print("=" * 70)

    print()

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

        print("Name           :", lead.name)
        print("Reference      :", lead.reference)
        print("Location       :", lead.location)
        print("Phone          :", lead.phone)
        print("Responses      :", lead.responses)
        print("Next Action    :", lead.next_action)
        print("Record Owner   :", lead.record_owner)

    print()

    print("=" * 70)
    print(f"TOTAL LEADS READY : {len(leads)}")
    print("=" * 70)

    print()

# ==========================================================
# IMPORT VISITS
# ==========================================================

def import_visits(df):

    Visit = get_model("Visit")

    df = clean_dataframe(df)

    visits = []

    for _, row in df.iterrows():

        # Import only rows where ABC exists

        if is_empty(row.get("ABC")):
            report.skipped("Visits")
            continue

        visit = Visit(

            meeting_id=None,

            state=clean_text(row.get("State")),
            region=clean_text(row.get("Region")),
            abc=clean_text(row.get("ABC")),
            company_name=clean_text(row.get("Company")),
            person_name=clean_text(row.get("Name")),
            designation=clean_text(row.get("Designation")),
            contact_no=clean_phone(row.get("Contact")),
            address=clean_text(row.get("Address")),
            brief=clean_text(row.get("Breif")),
            visit_date=clean_date(row.get("Date")),
            leads_generated=clean_int(row.get("Leads Generated")),
            m2=clean_text(row.get("M2")),
            m3=clean_text(row.get("M3")),
            record_owner=RECORD_OWNER

        )

# -----------------------------------------
# DUPLICATE CHECK
# -----------------------------------------

        existing = Visit.query.filter(
            Visit.company_name == visit.company_name,
            Visit.person_name == visit.person_name,
            Visit.visit_date == visit.visit_date,
            Visit.record_owner == visit.record_owner
        ).first()

        if existing:

            report.skipped("Visits")
            continue

        visits.append(visit)

        report.imported("Visits")

    preview_visits(visits)

    return visits

# ==========================================================
# IMPORT SALES
# ==========================================================

def import_sales(df):

    

    SalesPipeline = get_model("SalesPipeline")

    df = clean_dataframe(df)

    sales = []

    

    for _, row in df.iterrows():

        # --------------------------------------------
        # Import only rows having Project Type
        # --------------------------------------------

        if is_empty(row.get("Project Type")):

            report.skipped("Sales")

            continue

        

        sale = SalesPipeline(

            

            proposal_id=None,

            name=clean_text(
                row.get("Name")
            ),

            reference_no=clean_text(
                row.get("Refrence No.")
            ),

            project_stage=clean_text(
                row.get("Project Stage")
            ),

            moc=clean_text(
                row.get("MOC")
            ),

            source=clean_text(
                row.get("Source")
            ),

            next_action=clean_text(
                row.get("Next Action")
            ),

            address=clean_text(
                row.get("Address")
            ),

            contact_no=clean_phone(
                row.get("Contact")
            ),

            project_type=clean_text(
                row.get("Project Type")
            ),

            category=clean_text(
                row.get("Category")
            ),

            email_id=clean_text(
                row.get("Email ID")
            ),

            site_incharge=clean_text(
                row.get("Site Incharge")
            ),

            site_incharge_contact=clean_phone(
                row.get("Contact.1")
            ),

            first_contact=clean_date(
                row.get("First Contact")
            ),

            last_contact=clean_date(
                row.get("Last Contact")
            ),

            followup_date=clean_date(
                row.get("Followup Date")
            ),

            no_of_site_visits=clean_int(
                row.get("No. of Site Visit")
            ),

            area_covered=clean_decimal(
                row.get("Area Covered")
            ),

            total_units=clean_int(
                row.get("Total Units")
            ),

            price_of_units=clean_decimal(
                row.get("Price of Units")
            ),

            first_year_cmc=clean_decimal(
                row.get("1st Yr. CMC")
            ),

            installation=clean_decimal(
                row.get("Installation")
            ),

            total_sensor=clean_int(
                row.get("Total Sensor")
            ),

            sensor_cost=clean_decimal(
                row.get("Sensor Cost")
            ),

            discount=clean_decimal(
                row.get("Discount")
            ),

            revenue=clean_decimal(
                row.get("Revenue (₹)")
            ),

            amount_received=clean_decimal(
                row.get("Received(₹)")
            ),

            amount_due=clean_decimal(
                row.get("Due(₹)")
            ),

            total_revenue=clean_decimal(
                row.get("Total Revenue")
            ),

            gst_no=clean_text(
                row.get("GST No.")
            ),

            cmc_onwards=clean_decimal(
                row.get("CMC Onwards")
            ),

            total_cmc=clean_decimal(
                row.get("Total CMC")
            ),

            sales_person=None,

            record_owner=RECORD_OWNER

        )

        # --------------------------------------------
        # DUPLICATE CHECK
        # --------------------------------------------

        if sale.reference_no and sale.reference_no.strip():

            existing = SalesPipeline.query.filter_by(
                reference_no=sale.reference_no.strip(),
                record_owner=sale.record_owner
            ).first()

        else:

            existing = SalesPipeline.query.filter_by(

                name=sale.name,

                project_type=sale.project_type,

                address=sale.address,

                record_owner=sale.record_owner

            ).first()

        if existing:

            report.skipped("Sales")

            continue

        sales.append(sale)

        

        report.imported("Sales")

    

    preview_sales(sales)

    return sales

# ==========================================================
# IMPORT INVOICES
# ==========================================================

def import_invoices(df):

    Invoice = get_model("Invoice")

    df = clean_dataframe(df)

    invoices = []

    for _, row in df.iterrows():

        # --------------------------------------------
        # Import only rows having Name
        # --------------------------------------------

        if is_empty(row.get("Name")):

            report.skipped("Invoices")

            continue

        invoice = Invoice(

            sales_id=None,

            name=clean_text(
                row.get("Name")
            ),

            doi=clean_date(
                row.get("DOI")
            ),

            invoice_no=clean_text(
                row.get("Invoice No.")
            ),

            gst_no=clean_text(
                row.get("GST No.")
            ),

            product_sold=clean_text(
                row.get("Product Sold")
            ),

            total_units=clean_int(
                row.get("Total Units")
            ),

            price_of_units=clean_decimal(
                row.get("Price of Units")
            ),

            first_year_cmc=clean_decimal(
                row.get("1st Yr. CMC")
            ),

            installation=clean_decimal(
                row.get("Installation")
            ),

            total_sensor=clean_int(
                row.get("Total Sensor")
            ),

            sensor_cost=clean_decimal(
                row.get("Sensor Cost")
            ),

            revenue=clean_decimal(
                row.get("Revenue (₹)")
            ),

            total_revenue=clean_decimal(
                row.get("Total Revenue")
            ),

            record_owner=RECORD_OWNER

        )

        # --------------------------------------------
        # DUPLICATE CHECK
        # --------------------------------------------

        if invoice.invoice_no and invoice.invoice_no.strip():

            existing = Invoice.query.filter_by(

                invoice_no=invoice.invoice_no.strip(),

                record_owner=invoice.record_owner

            ).first()

        else:

            existing = Invoice.query.filter_by(

                name=invoice.name,

                doi=invoice.doi,

                record_owner=invoice.record_owner

            ).first()

        if existing:

            report.skipped("Invoices")

            continue

        invoices.append(invoice)

        report.imported("Invoices")

    preview_invoices(invoices)

    return invoices

# ==========================================================
# IMPORT DRAWINGS
# ==========================================================

def import_drawings(df):

    Drawing = get_model("Drawing")

    df = clean_dataframe(df)

    drawings = []

    for _, row in df.iterrows():

        # Import if Name OR Address exists

        if (
            is_empty(row.get("Name"))
            and
            is_empty(row.get("Address"))
        ):

            report.skipped("Drawings")

            continue

        drawing = Drawing(

            visit_id=None,

            name=clean_text(
                row.get("Name")
            ),

            address=clean_text(
                row.get("Address")
            ),

            iterations=clean_int(
                row.get("No. of Iteration")
            ),

            moca=clean_text(
                row.get("MODM")
            ),

            record_owner=RECORD_OWNER

        )

        # -----------------------------------------
        # DUPLICATE CHECK
        # -----------------------------------------

        existing = Drawing.query.filter_by(

            name=drawing.name,

            address=drawing.address,

            record_owner=drawing.record_owner

        ).first()

        if existing:

            report.skipped("Drawings")

            continue

        drawings.append(drawing)

        report.imported("Drawings")

    preview_drawings(drawings)

    return drawings

# ==========================================================
# IMPORT LEADS
# ==========================================================

def import_leads(df):

    Lead = get_model("Lead")

    df = clean_dataframe(df)

    leads = []

    for _, row in df.iterrows():

        if is_empty(row.get("Name")):

            report.skipped("Leads")

            continue

        location = combine_fields(
            row.get("Address"),
            row.get("Location")
        )

        lead = Lead(

            name=clean_text(
                row.get("Name")
            ),

            reference=None,

            location=location,

            phone=clean_phone(
                row.get("Contact")
            ),

            responses=clean_text(
                row.get("Unnamed: 5")
            ),

            next_action=clean_text(
                row.get("Unnamed: 6")
            ),

            date_of_1st_followup=None,

            next_to_call=None,

            recent=None,

            record_owner=RECORD_OWNER

        )

        # -----------------------------------------
        # DUPLICATE CHECK
        # -----------------------------------------

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
# PROCESS SHEET
# ==========================================================

PREVIEW_ONLY = False


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
    # VISITS
    # -----------------------------------------------------

    if rule["table"] == "Visit":

        visits = import_visits(df)

        if PREVIEW_ONLY:

            print("\nPreview Mode Enabled")
            print("Nothing has been inserted into the database.\n")

            return

        try:

            print("\nImporting Visits...")

            for visit in visits:

                db.session.add(visit)

            db.session.commit()

            print(f"\n{len(visits)} Visits Imported Successfully.\n")

        except Exception as e:

            db.session.rollback()

            print("\nERROR OCCURRED\n")

            traceback.print_exc()

            report.error(
                "Visits",
                0,
                str(e)
            )

        return

    # -----------------------------------------------------
    # SALES
    # -----------------------------------------------------

    if rule["table"] == "SalesPipeline":

        

        sales = import_sales(df)

        if PREVIEW_ONLY:

            print("\nPreview Mode Enabled")
            print("Nothing has been inserted into the database.\n")

            return

        try:

            print("\nImporting Sales...")

            for sale in sales:

                db.session.add(sale)

            db.session.commit()

            print(f"\n{len(sales)} Sales Imported Successfully.\n")

        except Exception as e:

            db.session.rollback()

            print("\nERROR OCCURRED\n")

            traceback.print_exc()

            report.error(
                "Sales",
                0,
                str(e)
            )

        return

    # -----------------------------------------------------
    # INVOICES
    # -----------------------------------------------------

    if rule["table"] == "Invoice":

        invoices = import_invoices(df)

        if PREVIEW_ONLY:

            print("\nPreview Mode Enabled")
            print("Nothing has been inserted into the database.\n")

            return

        try:

            print("\nImporting Invoices...")

            for invoice in invoices:

                db.session.add(invoice)

            db.session.commit()

            print(f"\n{len(invoices)} Invoices Imported Successfully.\n")

        except Exception as e:

            db.session.rollback()

            print("\nERROR OCCURRED\n")

            traceback.print_exc()

            report.error(
                "Invoices",
                0,
                str(e)
            )

        return

    # -----------------------------------------------------
    # DRAWINGS
    # -----------------------------------------------------

    if rule["table"] == "Drawing":

        drawings = import_drawings(df)

        if PREVIEW_ONLY:

            print("\nPreview Mode Enabled")
            print("Nothing has been inserted into the database.\n")

            return

        try:

            print("\nImporting Drawings...")

            for drawing in drawings:

                db.session.add(drawing)

            db.session.commit()

            print(f"\n{len(drawings)} Drawings Imported Successfully.\n")

        except Exception as e:

            db.session.rollback()

            print("\nERROR OCCURRED\n")

            traceback.print_exc()

            report.error(
                "Drawings",
                0,
                str(e)
            )

        return

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