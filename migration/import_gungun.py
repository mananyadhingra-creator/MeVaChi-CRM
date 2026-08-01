"""
=========================================================
Import Gungun Workbook
=========================================================
"""

import traceback
import pandas as pd

from migration.config import *
from migration.mappings import *
from migration.database import *
from migration.utils import *
from migration.report import MigrationReport

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
# PREVIEW CLIENTS
# ==========================================================

def preview_clients(clients):

    print("\n")
    print("=" * 70)
    print("FIRST 3 CLIENTS")
    print("=" * 70)

    for i, client in enumerate(clients[:3], start=1):

        print()
        print(f"Client {i}")
        print("-" * 70)

        print("Client Name        :", client.client_name)
        print("Property Type      :", client.property_type)
        print("Address            :", client.address)
        print("State              :", client.state)
        print("Location Link      :", client.location_link)
        print("Nearest Metro      :", client.nearest_metrostation)
        print("Mail               :", client.mail_id)
        print("Mobile             :", client.mobile_no)
        print("Product            :", client.product)
        print("Installation Date  :", client.installation_date)
        print("Activation Date    :", client.activation_date)
        print("Units Installed    :", client.no_of_units_installed)
        print("CMC Applicable     :", client.cmc_applicable)
        print("Next Renewal       :", client.next_cmc_renewal_date)
        print("Latitude           :", client.latitude)
        print("Longitude          :", client.longitude)
        print("Service Interval   :", client.service_interval_days)
        print("Record Owner       :", client.record_owner)

    print()
    print("=" * 70)
    print(f"TOTAL CLIENTS READY : {len(clients)}")
    print("=" * 70)
    print()

# ==========================================================
# PREVIEW CUSTOMER CARE CARDS
# ==========================================================

def preview_cards(cards):

    print()
    print("=" * 70)
    print("FIRST 3 CUSTOMER CARE CARDS")
    print("=" * 70)

    for i, card in enumerate(cards[:3], start=1):

        print()
        print(f"Card {i}")
        print("-" * 70)

        print("Client ID           :", card.client_id)
        print("Service Date        :", card.service_date)
        print("Service Of          :", card.service_of)
        print("No. of Filters      :", card.no_of_filters)
        print("Filters Cleaned     :", card.no_of_filters_cleaned)
        print("Controller Changed  :", card.controller_changed)
        print("Fan Changed         :", card.fan_changed)
        print("Serviced By         :", card.serviced_by)
        print("Pre Service Msg     :", card.pre_service_msgd)
        print("Post Service Report :", card.post_service_report_sent)
        print("Misc Messages       :", card.miscellaneous_messages)
        print("Tips & Tricks       :", card.tips_and_tricks)
        print("Referrals Program   :", card.referrals_program)
        print("News Sent           :", card.news_sent)
        print("Communication Date  :", card.communication_date)
        print("Remark              :", card.remark)
        print("Record Owner        :", card.record_owner)

    print()

    print("=" * 70)
    print(f"TOTAL CARDS READY : {len(cards)}")
    print("=" * 70)
    print()

# ==========================================================
# PREVIEW MODE
# ==========================================================

PREVIEW_ONLY = False

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
# IMPORT CLIENTS
# ==========================================================

def import_clients(df):

    Client = get_model("Client")

    df = clean_dataframe(df)

    df.columns = [str(col).strip() for col in df.columns]

    clients = []

    for _, row in df.iterrows():

        # --------------------------------------------------
        # Import only rows having Client Name
        # --------------------------------------------------

        if is_empty(row.get("Client Name")):

            report.skipped("Clients")

            continue

        # --------------------------------------------------
        # Combine Address
        # --------------------------------------------------

        address = combine_fields(

            row.get("Address"),

            row.get("Unnamed: 4")

        )

        # --------------------------------------------------
        # Latitude / Longitude
        # --------------------------------------------------

        latitude, longitude = get_coordinates_from_address(

            address,

            clean_text(
                row.get("State")
            )

        )

        

        client = Client(

            client_name=clean_text(
                row.get("Client Name")
            ),

            monitor_present=clean_text(
                row.get("Monitor present")
            ),

            property_type=clean_text(
                row.get("Type")
            ),

            address=address,

            location_link=clean_text(
                row.get("Location")
            ),

            nearest_metrostation=clean_text(
                row.get("Nearest Metro Station")
            ),

            mail_id=clean_text(
                row.get("Mail id")
            ),

            state=clean_text(
                row.get("State")
            ),

            mobile_no=clean_phone(
                row.get("Mobile No.")
            ),

            product=clean_text(
                row.get("Product")
            ),

            installation_date=clean_date(
                row.get("Installation Date")
            ),

            activation_date=clean_date(
                row.get("Activation date")
            ),

            filter_colour=clean_text(
                row.get("Filter Colour")
            ),

            no_of_units_installed=clean_int(
                row.get("No. of Units \nInstalled")
            ),

            solution_working=clean_text(
                row.get("Solution\n Working ")
            ),

            cmc_applicable=clean_text(
                row.get("CMC \nApplicable ")
            ),

            cmc_due_days=clean_int(
                row.get("CMC Due \nDays")
            ),

            cmc_due=clean_text(
                row.get("CMC \nDue ")
            ),

            next_cmc_renewal_date=clean_date(
                row.get("Next CMC Renewal Date")
            ),

            cmc_amount=clean_decimal(
                row.get("CMC \nAmount ")
            ),

            last_service_days=clean_int(
                row.get("Last Service days")
            ),

            last_service_date=clean_date(
                row.get("Last Service \nDate ")
            ),

            service_interval_days=45,

            service_due=clean_text(
                row.get("Service \nDue ")
            ),

            filter_clean=clean_date(
                row.get("Filter Clean")
            ),

            service_for=clean_text(
                row.get("Service\n For ")
            ),

            no_of_filters_replaced=clean_int(
                row.get("No. of Filters \nReplaced ")
            ),

            pre_service_msg=clean_text(
                row.get("Pre Service message")
            ),

            post_service_msg=clean_text(
                row.get("Post Service messaged")
            ),

            remark=clean_text(
                row.get("Remark")
            ),

            proposal_id=None,

            invoice_id=None,

            latitude=latitude,

            longitude=longitude,

            record_owner=RECORD_OWNER

        )

        # --------------------------------------------------
        # DUPLICATE CHECK
        # --------------------------------------------------

        existing = Client.query.filter_by(

            client_name=client.client_name,

            record_owner=client.record_owner

        ).first()

        if existing:

            report.skipped("Clients")

            continue

        clients.append(client)

        report.imported("Clients")

        

    preview_clients(clients)

    return clients

SHEET_CLIENT_MAP = {

    "Modi (Manni)"                    : 2,
    "Rishab (Manni Friend)"           : 1,
    "Abhishek (Manni - Vinni)"        : 3,
    "Sughanda Suri"                   : 4,
    "Ghaziabad office"                : 5,
    "Sasha Gaba (Office)"             : 6,
    "Sasha Gaba (Res.)"               : 7,
    "Puneet Goyal"                    : 8,
    "Sir Resd."                       : 9,
    "Gulshan Arora "                  : 10,
    "Neeraj Pawah"                    : 11,
    "JS Ahlawat "                     : 12,
    "Anand Chetali bansal (Res)"      : 13,
    "Anand Chetali bansal (Office)"   : 14,
    "Ashish Meena "                   : 15,
    "Saksham Verma"                   : 16,
    "Surbhi Singh "                   : 17,
    "Kamal "                          : 18,
    "Garg Brothers (Res)"             : 19,
    "Garg Brothers (Office) "         : 20,
    " Ravi Kant"                      : 21,
    "Amit Khosla "                    : 22,
    "Shivam Lightning Consultancy"    : 23,
    " Jitendra Khurana (Siegwerk)"    : 24,
    "Manish Sharma  Vikram Shriram "  : 25,
    "Roots Cafe"                      : 26,
    "Anil Yadav "                     : 27,
    "Siddhant Jain and Dashrath"      : 28,
    "Vivek Pratap Singh"              : 29,
    "Harshit"                         : 30,
    "Yudhishthir"                     : 31,
    "Dileep Giri"                     : 32,
    "Docere (Office) "                : 33,
    "lakshmi Ji (Office)"             : 34,
    "lakshmi Ji (Residence)"          : 35,
    "Amy"                             : 36,
    "Jatin Goel"                      : 37,
    "Piyush Mittal (Resi)"            : 38,
    "Piyush Mittal"                   : 39,
    "Paras(Resi)"                     : 40,
    "Varun"                          : 41,
    "Ajay Talwar"                    : 42,
    " Ajay Talwar 2"                 : 43,
    "Amit Sharma"                    : 44,
    "Meenu Singh"                    : 45,
    "Rajnish Chaudhary"              : 46,
    "Shivangi"                       : 47,
    "Sandesh Raghav"                 : 48,
    "Muskan Kharbanda"               : 49,
    "Anil Gupta"                     : 50,
    "Madhuri Singh Tripathi"         : 51,
    "Vinamra Jain"                   : 52,
    "Piyush Popli"                   : 53,
    "Rajesh Ghai"                    : 54,
    "Dr. Dinesh Bansal"              : 55,
    "Vibhuti Vistaar"                : 56,
    "Amit"                           : 57,
    "Akash"                          : 58,
    "Akash (Office)"                 : 59,
    "Vanketesh E Raman Prasad"       : 60,
    "Dr. Sapna Jain"                 : 61,
    "Sumeet Gupta (Resi)"            : 62,
    "Sumeet Gupta (Office)"          : 63,
    "Shankar (Servant)"              : 64,
    "Amit Suri-Richa Suri"           : 65,
    "Nimbus Group(Resi)"             : 66,
    "Sumit Goel"                     : 67,
    "Pooja Aggarwal"                 : 68,
    "Nisha Aggarwal"                 : 69,
    "Shashi Bhushan"                 : 70,
    "Ravi Gupta"                     : 71,
    "Meena Gupta"                    : 72,
    "Ritesh Sharma"                  : 73,
    "Keshav"                         : 74,
    "RC Bhargava"                    : 75,
    "Nimbus(Office)"                 : 76,
    "Vijul"                          : 77,
    "Mukul"                          : 78,
    "Paras Tayal(office)"            : 79,
    "Ram Mehrotra"                   : 80,
    "Vikram Narang"                  : 81,
    "Bhanu Kharbanda"               : 82,
    "Vaishnav"                      : 83,
    "Natwar Aggarwal"               : 84,
    "Dr.SK Narang"                  : 85,
    "Rajesh Ghai(Jabra)"            : 86,
    "Bhavna"                        : 87,
    "Aman Verma"                    : 88,
    "Sundar Lal"                    : 89,
    "Siddharth Bagai"               : 90,
    "Prashant Pureway"              : 91,
    "MP Singh"                      : 92,
    "MP Singh Basement"             : 93,
    "PK Khare"                      : 94,
    "Aniruddh Minda"                : 95,
    "ujjwal"                        : 96,
    "Anupam Gupta (office)"         : 97,
    "Anupam Gupta (Resi)"           : 98,
    "Sakshi"                        : 99,
    "Tirath "                       : 100,
    "Tirath (Sonipat)"              : 101,
    "Roneq Sandos"                  : 102,
    "Aman Sharma"                   : 103,
    "Sahil Sharma"                  : 104,
    "DK Sharma"                     : 105,
    "Ajay Grover"                   : 106,
    "Chahat"                        : 107,
    "Akashh"                        : 108,
    "Nikhil Jain"                   : 109,
    "Nidhi"                         : 110,
    "Akshay Arora"                  : 111,
    "Garima Bansal"                 : 112,
    "Dikshit"                       : 113,
    "Anuj Talwar"                   : 114,
    "Vercha Jewellers"              : 115

}

def find_client(sheet_name):

    Client = get_model("Client")

    client_id = SHEET_CLIENT_MAP.get(sheet_name)

    if client_id is None:
        return None

    return Client.query.get(client_id)

# ==========================================================
# IMPORT CUSTOMER CARE CARDS
# ==========================================================

def import_customer_care_cards(sheet_name, df):

    CustomerCareCard = get_model("CustomerCareCard")
    Client = get_model("Client")

    # Read actual service table


    df.columns = [str(col).strip() for col in df.columns]

    cards = []

    # --------------------------------------------------
    # Find Client
    # --------------------------------------------------

    client = find_client(sheet_name)

    if not client:

        print(f"\nClient not found for sheet : {sheet_name}\n")

        return cards

    # --------------------------------------------------
    # Iterate service rows
    # --------------------------------------------------

    for _, row in df.iterrows():

        # Ignore blank rows

        if is_empty(row.get("Service Dates")):

            report.skipped("Customer Care Cards")

            continue

        card = CustomerCareCard(

            client_id=client.client_id,

            service_date=clean_date(
                row.get("Service Dates")
            ),

            service_of=clean_text(
                row.get("Serivce of")
            ),

            no_of_filters=clean_int(
                row.get("No. of Filters")
            ),

            no_of_filters_cleaned=None,

            controller_changed=clean_bool(
                row.get("Controller Changed")
            ),

            fan_changed=clean_bool(
                row.get("Fan Changed")
            ),

            serviced_by=clean_text(
                row.get("Serviced By")
            ),

            pre_service_msgd=clean_bool(
                row.get("Pre Service msgd")
            ),

            post_service_report_sent=clean_bool(
                row.get("Post Service Report sent")
            ),

            miscellaneous_messages=clean_text(
                row.get("Miscellaneous messages")
            ),

            tips_and_tricks=clean_text(
                row.get("Tips and Tricks")
            ),

            referrals_program=clean_text(
                row.get("Referrals Program")
            ),

            news_sent=clean_bool(
                row.get("News Sent")
            ),

            communication_date=clean_date(
                row.get("Date")
            ),

            remark=clean_text(
                row.get("Remark")
            ),

            record_owner=RECORD_OWNER

        )

        cards.append(card)

        report.imported("Customer Care Cards")

        existing = CustomerCareCard.query.filter_by(
            client_id=client.client_id,
            service_date=clean_date(row.get("Service Dates")),
            service_of=clean_text(row.get("Serivce of"))
        ).first()

        if existing:

            report.skipped("Customer Care Cards")

            continue

    preview_cards(cards)

    return cards

# ==========================================================
# PROCESS MODE
# ==========================================================

PREVIEW_ONLY = False

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

    # ==================================================
    # CLIENTS
    # ==================================================

    if sheet_name == "Main Sheet":

        df = pd.read_excel(
            excel,
            sheet_name=sheet_name
        )

        print(f"Rows    : {len(df)}")
        print(f"Columns : {len(df.columns)}")

        clients = import_clients(df)

        if PREVIEW_ONLY:

            print("\nPreview Mode Enabled")
            print("Nothing has been inserted into the database.\n")

            return

        try:

            print("\nImporting Clients...")

            for client in clients:

                db.session.add(client)

            db.session.commit()

            print(f"\n{len(clients)} Clients Imported Successfully.\n")

        except Exception as e:

            db.session.rollback()

            traceback.print_exc()

            report.error(
                "Clients",
                0,
                str(e)
            )

        return

    # ==================================================
    # CUSTOMER CARE CARDS
    # ==================================================

    df = pd.read_excel(
        excel,
        sheet_name=sheet_name,
        header=7
    )

    print(f"Rows    : {len(df)}")
    print(f"Columns : {len(df.columns)}")

    cards = import_customer_care_cards(
        sheet_name,
        df
    )

    if PREVIEW_ONLY:

        print("\nPreview Mode Enabled")
        print("Nothing has been inserted into the database.\n")

        return

    try:

        print("\nImporting Customer Care Cards...")

        for card in cards:

            db.session.add(card)

        db.session.commit()

        print(f"\n{len(cards)} Customer Care Cards Imported Successfully.\n")

    except Exception as e:

        db.session.rollback()

        traceback.print_exc()

        report.error(
            "Customer Care Cards",
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