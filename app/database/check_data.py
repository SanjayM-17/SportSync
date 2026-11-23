
from sqlalchemy import text
from app.database.connection import engine

try:
    with engine.connect() as connection:

        print("\n===== SPORTSYNC DATABASE CHECK =====")

        tables = {
            "Users": "users",
            "Facilities": "facilities",
            "Equipment": "equipment",
            "TimeSlots": "timeslots",
            "Bookings": "bookings"
        }

        for name, table in tables.items():
            result = connection.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            )
            count = result.scalar()
            print(f"{name}: {count} records")

        print("\n===== SAMPLE FACILITIES =====")

        result = connection.execute(text("""
            SELECT facility_id, facility_name,
                   sport_type, capacity
            FROM facilities
            LIMIT 5
        """))

        for row in result:
            print(row)

        print("\nDataset access successful!")

except Exception as error:
    print("Error:", error)
