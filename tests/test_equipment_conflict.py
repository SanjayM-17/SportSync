
from app.database.connection import SessionLocal
from app.engines.conflict_engine import detect_conflicts

db = SessionLocal()

try:
    conflicts = detect_conflicts(
        db=db,
        sport="Football",
        participants=10,
        facility_id="F001",
        booking_date="2018-01-01",
        start_time="07:00",
        end_time="08:00",
        equipment_id="E002",
        equipment_quantity=16
    )

    equipment_conflicts = [
        conflict for conflict in conflicts
        if conflict["type"] == "Equipment Conflict"
    ]

    print("========== TC22: EQUIPMENT CONFLICT TEST ==========")
    print("Equipment: Football (E002)")
    print("Available quantity: 15")
    print("Requested quantity: 16")

    if equipment_conflicts:
        print("\nTEST PASSED")
        print("Result:", equipment_conflicts)
    else:
        print("\nTEST FAILED")
        print("Expected Equipment Conflict was not detected.")

finally:
    db.close()
