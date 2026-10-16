
"""Integration tests for the running Hostel Allocation API."""

import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app





@pytest.fixture
def client():
    """Test the FastAPI app in-process using real PostgreSQL and Redis."""
    with TestClient(app) as api:
        yield api

@pytest.fixture
def existing_student(client):
    """Get a real student from the database."""
    response = client.get("/students")
    assert response.status_code == 200

    students = response.json()["students"]
    assert students, "The database must contain at least one student"

    return students[0]


# 1. Health and read endpoints


def test_health_checks_postgres_and_redis(client):
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["postgres"] is True
    assert data["redis"] is True


def test_students_endpoint_returns_ranked_students(client):
    response = client.get("/students")

    assert response.status_code == 200
    data = response.json()

    assert "students" in data
    assert "mutual_pairs" in data
    assert "one_way_requests" in data
    assert len(data["students"]) > 0

    ranks = [student["rank"] for student in data["students"]]
    assert ranks == list(range(1, len(ranks) + 1))


def test_rooms_endpoint_returns_room_details(client):
    response = client.get("/rooms")

    assert response.status_code == 200
    rooms = response.json()["rooms"]

    assert len(rooms) > 0

    for room in rooms:
        assert "id" in room
        assert "code" in room
        assert "room_type" in room
        assert "capacity" in room
        assert "filled" in room


# 2. Student preference validation


def test_unknown_student_preferences_return_404(client):
    response = client.put(
        "/students/999999/preferences",
        json={"room_type": "double", "wants": []},
    )

    assert response.status_code == 404


def test_invalid_room_type_returns_400(client, existing_student):
    sid = existing_student["id"]

    response = client.put(
        f"/students/{sid}/preferences",
        json={"room_type": "penthouse", "wants": []},
    )

    assert response.status_code == 400
    assert "room_type" in response.json()["detail"]


def test_non_list_roommate_requests_return_400(client, existing_student):
    sid = existing_student["id"]

    response = client.put(
        f"/students/{sid}/preferences",
        json={"wants": "not-a-list"},
    )

    assert response.status_code == 400
    assert "wants must be a list" in response.json()["detail"]


def test_too_many_roommate_requests_return_400(client, existing_student):
    sid = existing_student["id"]

    response = client.put(
        f"/students/{sid}/preferences",
        json={"wants": [101, 102, 103]},
    )

    assert response.status_code == 400
    assert "at most" in response.json()["detail"]


def test_student_cannot_request_themselves(client, existing_student):
    sid = existing_student["id"]

    response = client.put(
        f"/students/{sid}/preferences",
        json={"wants": [sid]},
    )

    assert response.status_code == 400
    assert "cannot request yourself" in response.json()["detail"]


def test_duplicate_roommate_requests_return_400(client, existing_student):
    sid = existing_student["id"]
    other_id = next(
        student["id"]
        for student in client.get("/students").json()["students"]
        if student["id"] != sid
    )

    response = client.put(
        f"/students/{sid}/preferences",
        json={"wants": [other_id, other_id]},
    )

    assert response.status_code == 400
    assert "same roommate twice" in response.json()["detail"]


def test_nonexistent_roommate_returns_404(client, existing_student):
    sid = existing_student["id"]

    response = client.put(
        f"/students/{sid}/preferences",
        json={"wants": [999999]},
    )

    assert response.status_code == 404
    assert "no student with id" in response.json()["detail"]


def test_valid_preferences_can_be_saved(client, existing_student):
    """Save the student's existing preferences to avoid changing seed data."""
    sid = existing_student["id"]
    original_room_type = existing_student["room_type"]
    original_wants = existing_student["wants"]

    response = client.put(
        f"/students/{sid}/preferences",
        json={
            "room_type": original_room_type,
            "wants": original_wants,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["student"] == sid
    assert data["room_type"] == original_room_type
    assert data["wants"] == original_wants


# 3. Allocation workflow: API, database, and Redis


def test_unknown_run_returns_404(client):
    missing_run_id = uuid4().hex[:8]

    response = client.get(f"/runs/{missing_run_id}")

    assert response.status_code == 404


def test_allocation_run_completes_and_result_is_retrievable(client):
    # Start a real allocation. This creates a run in PostgreSQL and
    # tracks progress through Redis.
    response = client.post("/allocate")

    assert response.status_code == 202
    started = response.json()

    run_id = started["run_id"]
    assert started["status"] == "queued"
    assert started["poll"] == f"/runs/{run_id}"

    # The background allocation may take a moment to finish.
    deadline = time.monotonic() + 15
    status_data = {}

    while time.monotonic() < deadline:
        status_response = client.get(f"/runs/{run_id}")
        assert status_response.status_code == 200

        status_data = status_response.json()
        status = status_data["status"]

        if status in ("done", "failed"):
            break

        time.sleep(0.25)

    assert status_data.get("status") == "done", (
        f"Allocation did not finish successfully: {status_data}"
    )

    # Verify the completed plan can be retrieved from the API.
    result_response = client.get(
        "/allocation",
        params={"run_id": run_id},
    )

    assert result_response.status_code == 200
    result = result_response.json()

    assert result["run_id"] == run_id
    assert len(result["allocation"]) > 0

    for assignment in result["allocation"]:
        assert assignment["name"]
        assert assignment["room"]
        assert "got_room_type" in assignment
        assert "got_floor" in assignment
