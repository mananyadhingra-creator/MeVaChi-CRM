import osmium
import pandas as pd

areas = []

# Delhi NCR Bounding Box
MIN_LAT = 28.10
MAX_LAT = 29.20
MIN_LON = 76.60
MAX_LON = 77.90

PLACE_TYPES = {
    "suburb",
    "neighbourhood",
    "quarter",
    "city_district",
    "residential",
    "town",
    "village",
    "hamlet"
}


def inside_bbox(lat, lon):
    return (
        MIN_LAT <= lat <= MAX_LAT and
        MIN_LON <= lon <= MAX_LON
    )


class AreaHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()
        self.areas = []

    def save_place(self, tags, lat, lon):

        place = tags.get("place")

        if place not in PLACE_TYPES:
            return

        name = tags.get("name")

        if not name:
            return

        city = (
            tags.get("addr:city")
            or tags.get("is_in:city")
            or tags.get("addr:district")
            or tags.get("district")
            or ""
        )

        self.areas.append({
            "area_name": name.strip(),
            "city": city.strip(),
            "latitude": lat,
            "longitude": lon,
            "place_type": place,
            "pincode": ""
        })

    def node(self, n):

        if not n.location.valid():
            return

        lat = n.location.lat
        lon = n.location.lon

        if not inside_bbox(lat, lon):
            return

        self.save_place(n.tags, lat, lon)

    def way(self, w):

        if len(w.nodes) == 0:
            return

        first = w.nodes[0]

        if not first.location.valid():
            return

        lat = first.location.lat
        lon = first.location.lon

        if not inside_bbox(lat, lon):
            return

        self.save_place(w.tags, lat, lon)

    def relation(self, r):

        if "place" not in r.tags:
            return

        # Relations usually don't expose a direct center.
        # We'll keep a placeholder.
        self.areas.append({
            "area_name": r.tags.get("name", "").strip(),
            "city": "",
            "latitude": None,
            "longitude": None,
            "place_type": r.tags.get("place"),
            "pincode": ""
        })


handler = AreaHandler()

handler.apply_file(
    "imports/northern-zone-260719.osm.pbf",
    locations=True
)

df = pd.DataFrame(handler.areas)

# Remove rows where coordinates are missing
df = df.dropna(subset=["latitude", "longitude"])

# Convert coordinates to numeric (invalid values become NaN)
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

# Remove invalid coordinates
df = df.dropna(subset=["latitude", "longitude"])

VALID_TYPES = [
    "neighbourhood",
    "suburb",
    "quarter",
    "residential",
    "town",
    "village",
    "hamlet"
]

df = df[df["place_type"].isin(VALID_TYPES)]

df = df[df["area_name"] != ""]

df.drop_duplicates(
    subset=["area_name","place_type"],
    inplace=True
)

df.sort_values(
    ["place_type", "area_name"],
    inplace=True
)

df.to_csv(
    "imports/area_master.csv",
    index=False
)

print("=" * 60)
print("Extraction Complete")
print("=" * 60)
print(df["place_type"].value_counts())
print()
print("TOTAL:", len(df))