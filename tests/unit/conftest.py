import pytest
from dotenv import load_dotenv
import yaml

from app import create_app
from app.db import DB
from app.db.students import StudentResource
from app.db.bookings import BookingResource


@pytest.fixture(scope="session", autouse=True)
def app():
    load_dotenv()
    app = create_app()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def runner(app):
    return app.test_cli_runner()


def load_students():
    """
    Load student data from the YAML fixture file.
    """
    with open("tests/unit/fixtures/students.yaml", "r") as file:
        students = yaml.safe_load(file)

    return students


@pytest.fixture(scope="session")
def students():
    return load_students()


@pytest.fixture(scope="function", autouse=True)
def seeded_students_db(students):
    """
    Preload the mock 'students' collection with data from the YAML fixture.
    """
    student_resource = StudentResource()
    student_resource.delete_all_students()  # Clear existing data
    student_resource.add_multiple_students(students)


@pytest.fixture(scope="function", params=load_students())
def single_student(request):
    return request.param


def load_bookings():
    """Load booking data from the YAML fixture file."""
    with open("tests/unit/fixtures/bookings.yaml", "r") as file:
        bookings = yaml.safe_load(file)
    return bookings


@pytest.fixture(scope="session")
def bookings():
    return load_bookings()


@pytest.fixture(scope="function", autouse=True)
def seeded_bookings_db(bookings):
    """Preload the mock 'bookings' collection with data from the YAML fixture."""
    booking_resource = BookingResource()
    booking_resource.delete_all_bookings()
    booking_resource.add_multiple_bookings(bookings)
