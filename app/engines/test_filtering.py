
from datetime import date

from app.database.connection import SessionLocal
from app.engines.filtering_engine import (
    get_available_facilities,
    filter_by_sport,
    filter_by_capacity,
    get_available_time_slots,
    filter_by_time_slot,
    filter_by_equipment
)


def run_test(name, test_function):
    print(f"\n{name}")

    try:
        test_function()
        print("PASS")
    except Exception as error:
        print("FAIL:", error)


def test_available_facilities(db):
    facilities = get_available_facilities(db)

    assert isinstance(facilities, list)

    for facility in facilities:
        assert facility["facility_id"] is not None

    print("Available facilities:", len(facilities))


def test_filter_by_sport(db):
    facilities = get_available_facilities(db)

    football = filter_by_sport(
        facilities,
        "Football"
    )

    for facility in football:
        assert facility["sport_type"].lower() == "football"

    print("Football facilities:", len(football))


def test_filter_by_capacity(db):
    facilities = get_available_facilities(db)

    suitable = filter_by_capacity(
        facilities,
        5
    )

    for facility in suitable:
        assert facility["capacity"] >= 5

    print("Facilities with capacity >= 5:", len(suitable))


def test_available_time_slots(db):
    slots = get_available_time_slots(
        db=db,
        booking_date=date(2035, 1, 1)
    )

    assert isinstance(slots, list)

    print("Available base timeslots:", len(slots))


def test_facility_specific_time_slots(db):
    facilities = get_available_facilities(db)

    if not facilities:
        print("SKIPPED: No active facilities.")
        return

    facility_id = facilities[0]["facility_id"]

    slots = get_available_time_slots(
        db=db,
        booking_date=date(2035, 1, 1),
        start_time="07:00",
        end_time="08:00",
        facility_id=facility_id
    )

    assert isinstance(slots, list)

    print("Facility-specific timeslots:", len(slots))


def test_filter_by_time_slot(db):
    facilities = get_available_facilities(db)

    available = filter_by_time_slot(
        db=db,
        facilities=facilities,
        booking_date=date(2035, 1, 1),
        start_time="07:00",
        end_time="08:00"
    )

    assert isinstance(available, list)

    print("Facilities available for selected time:", len(available))


def test_filter_by_equipment(db):
    equipment = filter_by_equipment(
        db=db,
        sport="Football",
        required_quantity=1,
        booking_date=date(2035, 1, 1),
        start_time="07:00",
        end_time="08:00"
    )

    assert isinstance(equipment, list)

    for item in equipment:
        assert item["available_quantity"] >= 1

    print("Available Football equipment:", len(equipment))


def test_invalid_equipment_quantity(db):
    try:
        filter_by_equipment(
            db=db,
            sport="Football",
            required_quantity=0,
            booking_date=date(2035, 1, 1),
            start_time="07:00",
            end_time="08:00"
        )

        raise AssertionError(
            "Zero equipment quantity should be rejected."
        )

    except ValueError:
        pass


def main():
    db = SessionLocal()

    try:
        run_test(
            "TC01 - Available facilities",
            lambda: test_available_facilities(db)
        )

        run_test(
            "TC02 - Filter facilities by sport",
            lambda: test_filter_by_sport(db)
        )

        run_test(
            "TC03 - Filter facilities by capacity",
            lambda: test_filter_by_capacity(db)
        )

        run_test(
            "TC04 - Get available timeslots",
            lambda: test_available_time_slots(db)
        )

        run_test(
            "TC05 - Facility-specific timeslots",
            lambda: test_facility_specific_time_slots(db)
        )

        run_test(
            "TC06 - Filter facilities by time",
            lambda: test_filter_by_time_slot(db)
        )

        run_test(
            "TC07 - Shared equipment availability",
            lambda: test_filter_by_equipment(db)
        )

        run_test(
            "TC08 - Reject invalid equipment quantity",
            lambda: test_invalid_equipment_quantity(db)
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
