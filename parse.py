import csv
from classes import TimeOff, Doctor, Shift


def parse_raw_timeoff(name, timeoff_string, mandatory=True):
    """
    Format is space delimited day:time:duration.
    """
    if timeoff_string == 'None':
        return None

    timeoffs = []
    string_timeoffs = timeoff_string.split(' ')
    for st in string_timeoffs:
        assert len(st.split(':')) == 3, f"Incorrect format for time-off, found {st}, expecting one or more Day:Time:Duration"
        start_day, start_time, duration = st.split(':')
        timeoff = TimeOff(name, int(start_day), int(start_time), int(duration), mandatory)
        timeoffs.append(timeoff)

    return timeoffs


# TODO: write test and potentially catch bad csv input
# TODO: test that empty value for cell throws error
def parse_doctors(filename):

    doctors = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # TODO: throw error if space exists after comma for any value
            requested_raw = row['Requested Day:Time:Duration']  # TODO: test what happens if it is None
            mandatory_raw = row['Mandatory Day:Time:Duration']
            requested = parse_raw_timeoff(row['Name'], requested_raw, False)
            mandatory = parse_raw_timeoff(row['Name'], mandatory_raw, True)
            doctor = Doctor(
                row['Name'],
                int(row['Seniority']),
                row['Chief'],
                int(row['Carried Hours']),
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


def parse_shifts(filename):
    shifts = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            position_preferences = parse_raw_position_preferences(row['Position Preferences'])
            shift = Shift(
                row['Location'],
                int(row['Day']),
                int(row['Time']),
                int(row['Duration']),
                position_preferences
            )
            shifts.append(shift)

    return shifts
