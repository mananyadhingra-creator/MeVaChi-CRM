"""
=========================================================
Aman Workbook Mapping
=========================================================
"""

# --------------------------------------------------------
# SHEETS TO SKIP
# --------------------------------------------------------

SKIP_SHEETS = {
    "Sites",
    "Rajat",
    "Sheet9"
}

# --------------------------------------------------------
# RECORD OWNER
# --------------------------------------------------------

RECORD_OWNER = "Aman"

# --------------------------------------------------------
# IMPORT RULES
# --------------------------------------------------------

IMPORT_RULES = {

    "Leads": {

        "table": "Lead",

        # Import only rows having Name
        "required_column": "Name"

    },

    "Visits": {

        "table": "Visit",

        # Import only rows having ABC
        "required_column": "ABC"

    },

    "Drawings": {

        "table": "Drawing",

        # Import if Name OR Address exists
        "required_columns_any": [

            "Name",
            "Address"

        ]

    },

    "Sale Acheiveds Revenue": {

        "table": "SalesPipeline",

        # Import only if Project Type exists
        "required_column": "Project Type"

    },

    "Invoice": {

        "table": "Invoice",

        # Import only if Name exists
        "required_column": "Name"

    }

}