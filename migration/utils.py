import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, date

import pandas as pd
from dateutil import parser


# ==========================================================
# EMPTY VALUES
# ==========================================================

EMPTY_VALUES = {
    "",
    " ",
    "-",
    "--",
    "NA",
    "N/A",
    "NULL",
    "null",
    "None",
    "none",
    "nan",
    "NaN"
}


def is_empty(value):
    if value is None:
        return True

    if pd.isna(value):
        return True

    if isinstance(value, str):
        if value.strip() in EMPTY_VALUES:
            return True

    return False


# ==========================================================
# TEXT
# ==========================================================

def clean_text(value):
    if is_empty(value):
        return None

    value = str(value).strip()

    value = re.sub(r"\s+", " ", value)

    return value


# ==========================================================
# PHONE
# ==========================================================

def clean_phone(value):
    if is_empty(value):
        return None

    if isinstance(value, float):
        if value.is_integer():
            value = int(value)

    value = str(value)

    value = value.replace(".0", "")
    value = value.replace(" ", "")
    value = value.replace("-", "")
    value = value.replace("(", "")
    value = value.replace(")", "")

    if value.startswith("+91"):
        value = value[3:]

    if value.startswith("91") and len(value) > 10:
        value = value[2:]

    if value.startswith("0") and len(value) > 10:
        value = value[1:]

    return value


# ==========================================================
# INTEGER
# ==========================================================

def clean_int(value):
    if is_empty(value):
        return None

    try:

        if isinstance(value, str):
            value = value.replace(",", "")

        return int(float(value))

    except:
        return None


# ==========================================================
# DECIMAL
# ==========================================================



def clean_decimal(value):

    if is_empty(value):
        return None

    try:

        if isinstance(value, str):

            value = (
                value.replace(",", "")
                     .replace("₹", "")
                     .replace("Rs.", "")
                     .replace("rs.", "")
                     .replace("/-", "")
                     .strip()
            )

        return (
            Decimal(str(value))
            .quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )
        )

    except (InvalidOperation, ValueError, TypeError):

        return None


# ==========================================================
# DATE
# ==========================================================

def clean_date(value):

    if is_empty(value):
        return None

    try:

        if isinstance(value, pd.Timestamp):
            return value.date()

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        # Excel Serial Date
        if isinstance(value, (int, float)):
            if value > 1000:
                return pd.to_datetime(value, unit="D", origin="1899-12-30").date()

        text = str(value).strip()

        text = text.replace(".", "/")
        text = text.replace("\\", "/")

        # remove ordinal suffixes
        text = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', text)

        dt = parser.parse(
            text,
            fuzzy=True,
            dayfirst=True
        )

        return dt.date()

    except Exception:

        return None


# ==========================================================
# BOOLEAN
# ==========================================================

def clean_bool(value):

    if is_empty(value):
        return None

    text = str(value).strip().lower()

    if text in ["yes", "y", "true", "1"]:
        return "YES"

    if text in ["no", "n", "false", "0"]:
        return "NO"

    return None


# ==========================================================
# COLUMN FINDER
# ==========================================================

def get_column(df, name):

    for col in df.columns:

        if str(col).strip().lower() == name.strip().lower():
            return col

    return None

# ==========================================================
# COMBINE MULTIPLE TEXT FIELDS
# ==========================================================

def combine_fields(*values):

    cleaned = []

    for value in values:

        value = clean_text(value)

        if value:

            if value not in cleaned:
                cleaned.append(value)

    if not cleaned:
        return None

    return ", ".join(cleaned)