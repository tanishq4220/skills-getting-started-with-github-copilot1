from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def activities_data(monkeypatch):
    isolated_activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture
def client():
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_catalog_and_participants(client, activities_data):
    # Arrange
    expected_activity_names = {
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team",
        "Track and Field Club",
        "Art Studio",
        "Drama Club",
        "Debate Club",
        "Science Club",
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    response_activities = response.json()
    assert expected_activity_names <= response_activities.keys()
    assert response_activities["Chess Club"]["participants"] == activities_data["Chess Club"]["participants"]


def test_signup_adds_participant(client, activities_data):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities_data[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client, activities_data):
    # Arrange
    activity_name = "Chess Club"
    email = activities_data[activity_name]["participants"][0]
    original_participants = activities_data[activity_name]["participants"].copy()

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"
    assert activities_data[activity_name]["participants"] == original_participants


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client, activities_data):
    # Arrange
    activity_name = "Chess Club"
    email = activities_data[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities_data[activity_name]["participants"]


def test_unregister_rejects_unregistered_participant(client, activities_data):
    # Arrange
    activity_name = "Chess Club"
    email = "not.signed.up@mergington.edu"
    assert email not in activities_data[activity_name]["participants"]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up"


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"