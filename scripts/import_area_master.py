import os
import pandas as pd
from sqlalchemy import create_engine, text

# ==========================================
# DATABASE CONNECTION (Railway)
# ==========================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:IWIWgslswszNUtcNMEZIESpVhLqLSIYg@hayabusa.proxy.rlwy.net:37924/railway"
)

engine = create_engine(DATABASE_URL, future=True)

# ==========================================
# READ EXCEL
# ==========================================

df = pd.read_excel("imports/ncr_location_master.xlsx")

# Excel doesn't contain pincode
if "pincode" not in df.columns:
    df["pincode"] = None

# Replace NaN with None
df = df.where(pd.notnull(df), None)

print(f"\nFound {len(df)} records.\n")

inserted = 0
updated = 0

# ==========================================
# IMPORT
# ==========================================

with engine.begin() as conn:

    for _, row in df.iterrows():

        area_name = row["area_name"]
        city = row["city"]
        state = row["state"]
        latitude = row["latitude"]
        longitude = row["longitude"]
        # Skip rows with missing coordinates
        if pd.isna(latitude) or pd.isna(longitude):
            print(f"Skipped: {area_name} ({city}) - Missing coordinates")
            continue
        place_type = row["place_type"]
        pincode = row["pincode"]

        # --------------------------------------
        # Check if this location already exists
        # --------------------------------------

        existing = conn.execute(
            text("""
                SELECT area_id
                FROM area_master
                WHERE area_name = :area_name
                AND city = :city
                LIMIT 1
            """),
            {
                "area_name": area_name,
                "city": city
            }
        ).fetchone()

        # --------------------------------------
        # UPDATE EXISTING RECORD
        # --------------------------------------

        if existing:

            conn.execute(
                text("""
                    UPDATE area_master
                    SET
                        state = :state,
                        latitude = :latitude,
                        longitude = :longitude,
                        place_type = :place_type,
                        pincode = :pincode
                    WHERE area_id = :area_id
                """),
                {
                    "area_id": existing.area_id,
                    "state": state,
                    "latitude": latitude,
                    "longitude": longitude,
                    "place_type": place_type,
                    "pincode": pincode,
                }
            )

            updated += 1

        # --------------------------------------
        # INSERT NEW RECORD
        # --------------------------------------

        else:

            conn.execute(
                text("""
                    INSERT INTO area_master
                    (
                        area_name,
                        city,
                        state,
                        pincode,
                        latitude,
                        longitude,
                        place_type
                    )
                    VALUES
                    (
                        :area_name,
                        :city,
                        :state,
                        :pincode,
                        :latitude,
                        :longitude,
                        :place_type
                    )
                """),
                {
                    "area_name": area_name,
                    "city": city,
                    "state": state,
                    "pincode": pincode,
                    "latitude": latitude,
                    "longitude": longitude,
                    "place_type": place_type,
                }
            )

            inserted += 1

print("=" * 50)
print("AREA MASTER IMPORT COMPLETED")
print("=" * 50)
print(f"Inserted : {inserted}")
print(f"Updated  : {updated}")
print("=" * 50)