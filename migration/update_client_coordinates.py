"""
=========================================================
Update Client Latitude / Longitude
=========================================================
"""

from migration.database import (
    app,
    db,
    Client,
    get_coordinates_from_address
)


def main():

    with app.app_context():

        clients = Client.query.filter(
            (Client.latitude.is_(None)) |
            (Client.longitude.is_(None))
        ).all()

        updated = 0
        not_found = 0

        print("=" * 70)
        print("Updating Client Coordinates")
        print("=" * 70)
        print()

        for client in clients:

            lat, lon = get_coordinates_from_address(

                client.address,

                client.state

            )

            if lat is None or lon is None:

                print(f"❌ NOT FOUND : {client.client_name}")

                not_found += 1

                continue

            client.latitude = lat
            client.longitude = lon

            updated += 1

            print(
                f"✅ {client.client_name}"
                f" -> ({lat}, {lon})"
            )

        db.session.commit()

        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)

        print(f"Updated   : {updated}")
        print(f"Not Found : {not_found}")


if __name__ == "__main__":

    main()