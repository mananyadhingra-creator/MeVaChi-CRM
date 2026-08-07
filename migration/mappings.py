"""
=========================================================
Workbook Mapping
=========================================================
"""

# --------------------------------------------------------
# SHEETS TO SKIP
# --------------------------------------------------------



SKIP_SHEETS = {
    "Monthly Plan",
    "Sheet3"
}

# --------------------------------------------------------
# RECORD OWNER
# --------------------------------------------------------

RECORD_OWNER = "Sushmita"

# --------------------------------------------------------
# IMPORT RULES
# --------------------------------------------------------

IMPORT_RULES = {

    # ----------------------------------------------------
    # LEADS
    # ----------------------------------------------------

    "Leads": {

        "table": "Lead",

        # Import only if Name OR Reference exists

        "required_columns": [
            "Name",
            "Reference"
        ]

    },

    # ----------------------------------------------------
    # MEETINGS
    # ----------------------------------------------------

    "Meetings": {

        "table": "Meeting",

        # Import only if Meeting Fixed By
        # OR Name
        # OR Firm Name exists

        "required_columns": [
            "Meeting Fixed By",
            "Name",
            "Firm Name"
        ]

    },

    # ----------------------------------------------------
    # PROPOSALS
    # ----------------------------------------------------

    "Proposals": {

        "table": "Proposal",

        # Import only if Name OR Reference No. exists

        "required_columns": [
            "Name",
            "Reference no."
        ]

    }

}