"""
=========================================================
Database Bootstrap
=========================================================
"""

import os
import sys

# ---------------------------------------------------------
# Make project root importable
# ---------------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------
# Import Flask app + SQLAlchemy
# ---------------------------------------------------------

from app import (
    app,
    db,

    Lead,
    Visit,
    Drawing,
    SalesPipeline,
    Invoice
)

# ---------------------------------------------------------
# MODEL LOOKUP
# ---------------------------------------------------------

MODEL_MAP = {

    "Lead": Lead,

    "Visit": Visit,

    "Drawing": Drawing,

    "SalesPipeline": SalesPipeline,

    "Invoice": Invoice

}


def get_model(name):

    return MODEL_MAP[name]