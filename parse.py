import csv

from classes.doctor import Doctor
from classes.shift import Shift
from classes.timeoff import TimeOff


def parse_raw_timeoff(name, timeoff_string, mandatory=True):
    """
    Format is space delimited day:time:duration.
    """
    if timeoff_string == '_':
        return None

    timeoffs = []
    string_timeoffs = timeoff_string.split(' ')
    for st in string_timeoffs:
        assert len(st.split(':')) == 3, f"Incorrect format for timeoff, found {st}, expecting Day:Time:Duration"
        start_day, start_time, duration = st.split(':')
        timeoff = TimeOff(name, int(start_day), int(start_time), int(duration), mandatory)
        timeoffs.append(timeoff)

    return timeoffs


def is_empty(row):
    """
    Skips a row of input if all cells are empty strings. Allows
    for csv to be more organized.
    """
    all_empty = True
    found_null = False
    found_empty = False
    for key, value in row.items():
        if value != '':
            all_empty = False
        if value == '_':
            found_null = True
        if value == '':
            found_empty = True

    # Error if there are a mix of empty strings and
    # explicitly set null ('_') cells.
    assert not (found_empty and found_null), f"Row found with empty string and null value"

    return all_empty


def clean_row(row):
    # Remove trailing and leading whitespace
    for key, value in row.items():
        row[key] = value.strip()
        assert value != '', f"Row value is empty string, should either be explicitly null ('_') or a non-empty value"
    return row


def parse_doctors(filename, block):

    doctors = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if is_empty(row):
                continue

            row = clean_row(row)
            requested_raw = row['Requested Day:Time:Duration']  # TODO: test what happens if it is None
            mandatory_raw = row['Mandatory Day:Time:Duration']
            requested = parse_raw_timeoff(row['Name'], requested_raw, False)
            mandatory = parse_raw_timeoff(row['Name'], mandatory_raw, True)
            doctor = Doctor(
                block,
                row['Name'],
                int(row['Seniority']),
                row['Chief'],
                float(row['Carried Hours']),
                row['Half Block'],
                int(row['Pre Block Hours']),
                requested,
                mandatory
            )
            doctors.append(doctor)

    return doctors


def parse_raw_position_preferences(position_preferences_string):
    """
    Format is delimitied by '>' character.
    """
    preferences = []
    string_preferences = position_preferences_string.split('>')
    for preference in string_preferences:
        assert preference.isnumeric(), f"Preference is {preference} within position preferences {position_preferences_string}, but must be convertable to number"
        preferences.append(int(preference))

    return preferences


def parse_shifts(block, filename):
    shifts = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            position_preferences = parse_raw_position_preferences(row['Position Preferences'])
            shift = Shift(
                block,
                row['Location'],
                int(row['Day']),
                int(row['Time']),
                int(row['Duration']),
                position_preferences,
                row['Optional']
            )
            shifts.append(shift)

    return shifts
