import pandas as pd

print("Reading GeoNames data...")

cols = [
    "geonameid",
    "name",
    "asciiname",
    "alternatenames",
    "latitude",
    "longitude",
    "feature_class",
    "feature_code",
    "country_code",
    "cc2",
    "admin1",
    "admin2",
    "admin3",
    "admin4",
    "population",
    "elevation",
    "dem",
    "timezone",
    "modification_date"
]

df = pd.read_csv(
    "imports/IN.txt",
    sep="\t",
    names=cols,
    encoding="utf-8",
    low_memory=False
)

print("Total records:", len(df))

# Keep only populated places
df = df[df["feature_class"] == "P"]

# Delhi NCR keywords
keywords = [
    "Delhi",
    "New Delhi",
    "Noida",
    "Greater Noida",
    "Ghaziabad",
    "Gurgaon",
    "Gurugram",
    "Faridabad",
    "Sahibabad",
    "Loni",
    "Dadri",
    "Modinagar",
    "Muradnagar",
    "Bahadurgarh",
    "Sonipat",
    "Manesar"
]

mask = df["alternatenames"].fillna("").str.contains(
    "|".join(keywords),
    case=False,
    regex=True
)

mask |= df["name"].str.contains(
    "|".join(keywords),
    case=False,
    regex=True
)

df = df[mask]

print("Filtered records:", len(df))

df = df[[
    "name",
    "latitude",
    "longitude"
]]

df = df.drop_duplicates()

df.columns = [
    "area_name",
    "latitude",
    "longitude"
]

df["city"] = ""
df["pincode"] = ""

df = df[
    [
        "area_name",
        "city",
        "latitude",
        "longitude",
        "pincode"
    ]
]

df.to_csv(
    "imports/area_master.csv",
    index=False
)

print("Done!")
print(df.head())
print("Rows:", len(df))