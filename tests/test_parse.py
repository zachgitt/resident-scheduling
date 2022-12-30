import pytest

from classes.block import Block
from parse import parse_doctors, parse_shifts
from settings.config import Seniority, Locations


@pytest.mark.parametrize('file', [
    'doctors_succeeds.csv',
    'doctors_leading_space.csv',
    'doctors_trailing_space.csv'
])
def test_parse_doctor_succeeds(file):
    """
    NOTE: Tests assume that this is a 28 day block and therefore
    each doctor gets an additional 4 mandatory time off per conference.
    """
    block = Block(1, 28)
    num_wednesday_conferences = 4
    doctors = parse_doctors(block, f'inputs/{file}')
    assert len(doctors) == 1
    doctor = doctors[0]
    assert doctor.name == 'Ben Hong'
    assert doctor.seniority == Seniority.FOURTH_YEAR
    assert doctor.chief
    assert doctor.carry_hours == 12
    assert len(doctor.requested_timeoff) == 0
    assert len(doctor.mandatory_timeoff) == 5 + num_wednesday_conferences
    assert doctor.half_block == 'both'
    assert doctor.pre_block_hours == 0


def test_parse_doctor_with_skipped_row():
    block = Block(1, 28)
    doctors = parse_doctors(block, 'inputs/doctors_empty_row.csv')
    assert len(doctors) == 2


def test_parse_doctor_invalid_row():
    block = Block(1, 28)
    with pytest.raises(AssertionError) as e:
        parse_doctors(block, 'inputs/doctors_invalid_row.csv')
    assert e.value.args[0] == 'Row found with empty string and null value'


def test_parse_doctor_with_empty_requested_timeoff():
    block = Block(1, 28)
    with pytest.raises(AssertionError) as e:
        parse_doctors(block, 'inputs/doctors_empty_timeoff.csv')
    assert e.value.args[0] == "Row value is empty string, should either be explicitly null ('_') or a non-empty value"


def test_parse_doctor_invalid_requested_timeoff_format():
    block = Block(1, 28)
    with pytest.raises(AssertionError) as e:
        parse_doctors(block, 'inputs/doctors_invalid_timeoff.csv') # 13:25:8
    assert 'Incorrect format for timeoff' in e.value.args[0]


def test_parse_shifts_succeeds():
    block = Block(1, 28)
    shifts = parse_shifts(block, 'inputs/shifts_succeeds.csv')
    assert len(shifts) == 1
    shift = shifts[0]
    assert shift.location in Locations
    assert shift.start_day == 1
    assert shift.start_time == 10
    assert shift.duration == 9
    assert len(shift.position_preferences) == 4
    assert shift.position_preferences == [0, 1, 2, 3]
    assert not shift.optional


def test_parse_shifts_with_skipped_row():
    pass


def test_parse_shifts_invalid_row():
    pass
