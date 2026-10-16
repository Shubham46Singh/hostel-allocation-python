
"""Tests for room selection, allocation, repair, and progress."""

import pytest

from app.allocate import (
    AllocationError,
    _repair_lonely,
    allocate,
    choose_room,
    room_score,
)


def student(
    student_id,
    merit=50,
    year=1,
    wants=None,
    room_type="double",
    floor_pref=None,
    name=None,
):
    return {
        "id": student_id,
        "name": name or f"Student {student_id}",
        "merit": merit,
        "year": year,
        "wants": wants or [],
        "room_type": room_type,
        "floor_pref": floor_pref,
    }


def room(room_id, room_type, floor=1, capacity=None, occupants=None):
    result = {
        "id": room_id,
        "code": f"R{room_id}",
        "room_type": room_type,
        "floor": floor,
        "occupants": occupants or [],
    }
    if capacity is not None:
        result["capacity"] = capacity
    return result


# 1. Room scoring and selection

def test_matching_room_type_scores_higher_than_floor_match():
    leader = student(1, room_type="double", floor_pref=2)

    matching_type = room_score(
        room(1, "double", floor=1, capacity=2), 2, leader
    )
    matching_floor = room_score(
        room(2, "triple", floor=2, capacity=3), 2, leader
    )

    assert matching_type > matching_floor


def test_room_with_insufficient_capacity_is_not_scored():
    leader = student(1)

    assert room_score(room(1, "single", capacity=1), 2, leader) is None


def test_room_score_rewards_filling_an_existing_room():
    leader = student(1, room_type="double")

    empty_room = room(1, "double", capacity=2)
    partly_filled_room = room(
        2, "double", capacity=2, occupants=[99]
    )

    empty_score = room_score(empty_room, 1, leader, occupied=0)
    filled_score = room_score(partly_filled_room, 1, leader, occupied=1)

    assert filled_score > empty_score


def test_choose_room_breaks_ties_using_lowest_room_id():
    rooms = [
        room(5, "double", capacity=2),
        room(2, "double", capacity=2),
    ]

    selected = choose_room(
        rooms, 2, student(1, room_type="double")
    )

    assert selected["id"] == 2


def test_choose_room_returns_none_when_no_room_fits():
    rooms = [room(1, "single", capacity=1)]

    assert choose_room(rooms, 2, student(1)) is None


# 2. Repairing lonely rooms

def test_repair_moves_lone_student_to_smaller_room():
    state = [
        room(1, "quad", capacity=4, occupants=[1]),
        room(2, "double", capacity=2),
    ]

    moved, stranded = _repair_lonely(state)

    assert state[0]["occupants"] == []
    assert state[1]["occupants"] == [1]
    assert len(moved) == 1
    assert moved[0]["student"] == 1
    assert moved[0]["from"] == "R1"
    assert moved[0]["to"] == "R2"
    assert stranded == []


def test_repair_brings_someone_into_lonely_room_when_no_target_exists():
    state = [
        room(1, "quad", capacity=4, occupants=[1]),
        room(2, "double", capacity=2, occupants=[2, 3]),
    ]

    moved, stranded = _repair_lonely(state, pos={2: 1, 3: 2})

    assert state[0]["occupants"] == [1, 3]
    assert state[1]["occupants"] == [2]
    assert moved[0]["student"] == 3
    assert stranded == []


def test_repair_reports_stranded_student_when_no_fix_is_possible():
    state = [room(1, "quad", capacity=4, occupants=[1])]

    moved, stranded = _repair_lonely(state)

    assert moved == []
    assert stranded == [
        {
            "student": 1,
            "room": "R1",
            "reason": "alone in a 4-bed room, nowhere to move them",
        }
    ]


# 3. Full allocation

def test_allocate_rejects_empty_student_list():
    with pytest.raises(AllocationError, match="no students"):
        allocate([], [room(1, "double", capacity=2)])


def test_allocate_rejects_empty_room_list():
    with pytest.raises(AllocationError, match="no rooms"):
        allocate([student(1)], [])


def test_allocate_places_students_and_respects_room_capacity():
    students = [
        student(1, merit=90),
        student(2, merit=80),
        student(3, merit=70),
    ]
    rooms = [
        room(1, "double", capacity=2),
        room(2, "single", capacity=1),
    ]

    result = allocate(students, rooms)

    assert result["summary"]["students"] == 3
    assert result["summary"]["placed"] == 3
    assert result["unplaced"] == []
    assert len(result["assignments"]) == 3

    for allocated_room in result["rooms"]:
        assert allocated_room["filled"] <= allocated_room["capacity"]


def test_allocate_reports_student_when_all_rooms_are_full():
    students = [student(1), student(2)]
    rooms = [room(1, "single", capacity=1)]

    result = allocate(students, rooms)

    assert result["summary"]["placed"] == 1
    assert len(result["unplaced"]) == 1
    assert result["unplaced"][0]["reason"] == (
        "no room large enough was free"
    )


def test_allocate_avoids_leaving_one_student_alone_in_quad():
    students = [student(1, room_type="double")]
    rooms = [
        room(1, "quad", capacity=4),
        room(2, "double", capacity=2),
    ]

    result = allocate(students, rooms)

    assert result["assignments"][0]["room"] == "R2"
    assert result["stranded"] == []


def test_one_way_request_is_not_disappointed_if_students_share_room():
    students = [
        student(1, wants=[2], name="A"),
        student(2, name="B"),
    ]
    rooms = [room(1, "quad", capacity=4)]

    result = allocate(students, rooms)

    assignments = result["assignments"]
    assert assignments[0]["room_id"] == assignments[1]["room_id"]
    assert result["disappointed"] == []


def test_allocate_is_deterministic():
    students = [
        student(1, merit=80, wants=[2]),
        student(2, merit=70, wants=[1]),
        student(3, merit=60),
    ]
    rooms = [
        room(2, "double", capacity=2),
        room(1, "single", capacity=1),
    ]

    first = allocate(students, rooms)
    second = allocate(students, rooms)

    assert first == second


def test_progress_callback_is_monotonic_and_finishes():
    updates = []

    def progress(done, total, message):
        updates.append((done, total, message))

    allocate(
        [student(1), student(2)],
        [room(1, "double", capacity=2)],
        progress=progress,
    )

    done_values = [update[0] for update in updates]

    assert done_values == sorted(done_values)
    assert done_values[-1] == 5
    assert updates[-1][1] == 5
    assert updates[-1][2] == "done"
