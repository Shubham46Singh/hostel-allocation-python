"""Unit tests for the hostel room allocation algorithm."""

import pytest

from app.allocate import (
    AllocationError,
    capacity_of,
    form_groups,
    is_viable_occupancy,
    merit_key,
    mutual_pairs,
    one_way_requests,
    rank_students,
)


def student(student_id, merit=50, year=1, wants=None, name=None):
    """Create a sample student for testing."""
    return {
        "id": student_id,
        "name": name or f"Student {student_id}",
        "merit": merit,
        "year": year,
        "wants": wants or [],
    }


# --------------------------------------------------
# 1. Student ranking tests
# --------------------------------------------------

def test_higher_merit_gets_better_rank():
    students = [
        student(1, merit=70),
        student(2, merit=90),
        student(3, merit=80),
    ]

    ranked = rank_students(students)

    assert [s["id"] for s in ranked] == [2, 3, 1]
    assert [s["rank"] for s in ranked] == [1, 2, 3]


def test_higher_year_wins_when_merit_is_equal():
    students = [
        student(1, merit=80, year=1),
        student(2, merit=80, year=3),
        student(3, merit=80, year=2),
    ]

    ranked = rank_students(students)

    assert [s["id"] for s in ranked] == [2, 3, 1]


def test_lower_id_wins_when_merit_and_year_are_equal():
    students = [
        student(5, merit=80, year=2),
        student(2, merit=80, year=2),
        student(9, merit=80, year=2),
    ]

    ranked = rank_students(students)

    assert [s["id"] for s in ranked] == [2, 5, 9]


def test_ranking_does_not_modify_original_students():
    students = [
        student(1, merit=70),
        student(2, merit=90),
    ]

    rank_students(students)

    assert all("rank" not in s for s in students)


def test_merit_key_orders_students_correctly():
    first = student(1, merit=90, year=1)
    second = student(2, merit=80, year=3)

    assert merit_key(first) < merit_key(second)


# --------------------------------------------------
# 2. Mutual roommate request tests
# --------------------------------------------------

def test_mutual_request_creates_one_pair():
    students = [
        student(1, wants=[2]),
        student(2, wants=[1]),
    ]

    assert mutual_pairs(students) == [(1, 2)]


def test_one_way_request_does_not_create_mutual_pair():
    students = [
        student(1, wants=[2]),
        student(2, wants=[3]),
        student(3),
    ]

    assert mutual_pairs(students) == []


def test_self_request_is_ignored():
    students = [
        student(1, wants=[1, 2]),
        student(2, wants=[1]),
    ]

    assert mutual_pairs(students) == [(1, 2)]


def test_mutual_pairs_are_sorted_and_not_duplicated():
    students = [
        student(3, wants=[1]),
        student(1, wants=[3]),
        student(2, wants=[3]),
    ]

    assert mutual_pairs(students) == [(1, 3)]


def test_duplicate_requests_do_not_duplicate_pairs():
    students = [
        student(1, wants=[2, 2]),
        student(2, wants=[1]),
    ]

    assert mutual_pairs(students) == [(1, 2)]


# --------------------------------------------------
# 3. One-way request tests
# --------------------------------------------------

def test_one_way_request_is_reported_as_not_mutual():
    students = [
        student(1, wants=[2], name="Ishita"),
        student(2, wants=[3], name="Janvi"),
        student(3, name="Kabir"),
    ]

    result = one_way_requests(students)

    assert {
        "student": 1,
        "name": "Ishita",
        "wanted": 2,
        "wanted_name": "Janvi",
        "reason": "not_mutual",
    } in result


def test_request_for_nonexistent_student_is_reported():
    students = [
        student(1, wants=[99], name="Ishita"),
    ]

    result = one_way_requests(students)

    assert result == [
        {
            "student": 1,
            "name": "Ishita",
            "wanted": 99,
            "wanted_name": None,
            "reason": "no_such_student",
        }
    ]


def test_mutual_request_is_not_reported_as_one_way():
    students = [
        student(1, wants=[2]),
        student(2, wants=[1]),
    ]

    assert one_way_requests(students) == []


# --------------------------------------------------
# 4. Group formation tests
# --------------------------------------------------

def test_mutual_pair_stays_in_same_group():
    students = [
        student(1, wants=[2]),
        student(2, wants=[1]),
    ]

    groups, bumped = form_groups(students)

    assert groups == [[1, 2]]
    assert bumped == []


def test_mutual_triple_forms_one_group():
    students = [
        student(1, wants=[2, 3]),
        student(2, wants=[1, 3]),
        student(3, wants=[1, 2]),
    ]

    groups, bumped = form_groups(students)

    assert groups == [[1, 2, 3]]
    assert bumped == []


def test_mutual_chain_forms_groups_without_exceeding_capacity():
    students = [
        student(1, wants=[2]),
        student(2, wants=[1, 3]),
        student(3, wants=[2, 4]),
        student(4, wants=[3, 5]),
        student(5, wants=[4]),
    ]

    groups, bumped = form_groups(students, max_size=4)

    assert groups == [[1, 2, 3, 4], [5]]
    assert all(len(group) <= 4 for group in groups)
    assert len(bumped) == 1
    assert bumped[0]["student"] == 5
    assert bumped[0]["blocked_by"] == 4
    assert bumped[0]["reason"] == "outranked"


def test_group_formation_rejects_zero_maximum_size():
    with pytest.raises(AllocationError):
        form_groups([student(1)], max_size=0)


# --------------------------------------------------
# 5. Room capacity tests
# --------------------------------------------------

@pytest.mark.parametrize(
    ("room_type", "expected_capacity"),
    [
        ("single", 1),
        ("double", 2),
        ("triple", 3),
        ("quad", 4),
    ],
)
def test_capacity_of_known_room_types(room_type, expected_capacity):
    assert capacity_of({"room_type": room_type}) == expected_capacity


def test_explicit_room_capacity_takes_precedence():
    assert capacity_of({"room_type": "single", "capacity": 3}) == 3


def test_unknown_room_type_raises_allocation_error():
    with pytest.raises(AllocationError):
        capacity_of({"room_type": "penthouse"})


# --------------------------------------------------
# 6. Valid room occupancy tests
# --------------------------------------------------

@pytest.mark.parametrize(
    ("capacity", "filled", "expected"),
    [
        (1, 0, True),
        (1, 1, True),
        (2, 0, True),
        (2, 1, True),
        (2, 2, True),
        (3, 0, True),
        (3, 1, False),
        (3, 2, True),
        (4, 0, True),
        (4, 1, False),
        (4, 2, True),
        (4, 4, True),
    ],
)
def test_is_viable_occupancy(capacity, filled, expected):
    assert is_viable_occupancy(capacity, filled) is expected
