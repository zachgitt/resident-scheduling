from settings.config import Locations


def compare_shifts(shift1, shift2):
    # Sort by day, if tied, sort by time
    if shift1.start_day < shift2.start_day:
        return -1
    elif shift1.start_day > shift2.start_day:
        return 1
    elif shift1.start_time < shift2.start_time:
        return -1
    elif shift1.start_time > shift2.start_time:
        return 1
    else:
        return 0

# TODO: create check_day_time_duration which should be reused by TimeOff and Shift

# TODO: test if shift starts at day 1
class Shift:
    def __init__(self, block, location, start_day, start_time, duration, position_preferences, optional='False'):
        # Validate types
        assert type(location) == str
        assert type(start_day) == int
        assert type(start_time) == int
        assert type(duration) == int
        assert isinstance(position_preferences, list)
        assert type(optional) == str

        assert location in Locations, f"Shift location is {location}, but must be one of {', '.join([l for l in Locations])}"

        # Validate day
        assert block.start <= start_day <= block.end, f"Shift start day for {location} is {start_day}, but must be between {block.start} and {block.end}"

        # Validate start time
        assert 0 <= start_time <= 23, f"Shift start time for {location} is {start_time}, but must be between 0 and 23"
        if start_day == block.start:
            assert 7 <= start_time, f"Shift start time for {location} is {start_time}, but must be after 7am for the first day"

        # Validate duration
        assert duration in [8, 9, 10, 12], f"Shift duration for {location} is {duration}, but can only be 8, 9, 10 or 12 hours"
        end_day = start_day + (start_time + duration) // 24
        end_time = (start_time + duration % 24) % 24

        # Days start at 7am, so you just need to end at or before the day after last
        if end_day == block.end + 1:
            assert end_time <= 7, f"Shift end time for {location} is {end_time}, but must end before 7am if it extends past the last day"

        assert optional in ['False', 'True'], f"Shift optional found is {optional}, but must be either True or False"

        self.location = location
        self.start_day = start_day
        self.start_time = start_time
        self.duration = duration
        self.position_preferences = position_preferences
        self.night = self.determine_if_night(start_time)
        self.weekend = self.determine_if_weekend(start_day, start_time)
        self.doctor = None
        self.optional = (optional == 'True')

        print(f'Creating {self}')

    def assign_doctor(self, doctor):
        self.doctor = doctor
        doctor.add_shift(self)
        doctor.add_mandatory_time_off(self.start_time, self.start_time, self.duration)
        print(f'Assigning Shift:{self} to Doctor:{doctor}')

    def unassign_doctor(self, doctor):
        self.doctor = None
        doctor.remove_shift(self)
        doctor.remove_mandatory_timeoff()
        print(f'Unassigning Shift:{self} to Doctor:{doctor}')

    def determine_if_night(self, start_time):
        # Night shifts start at 7pm. Starting at 7am does not count.
        return bool(19 <= start_time or start_time < 7)

    def determine_if_weekend(self, start_day, start_time):
        # Weekend shifts start between Sat 7am - Mon 7am (exclusive Mon 7am)

        # Saturday
        if start_day % 7 == 6 and start_time >= 7:
            return True
        # Sunday
        if start_day % 7 == 0:
            return True
        # Monday
        if start_day % 7 == 1 and start_time < 7:
            return True

        return False

    def overlaps_timeoff(self, timeoff):
        # TODO: account for the previous night might overlap the next morning
        start1 = self.start_time
        end1 = self.start_time + self.duration

        start2 = timeoff.start_time
        end2 = timeoff.start_time + timeoff.duration

        # TODO: write tests to check that start/end overlaps do not count
        if start2 <= start1 < end2:
            return True
        if start2 < end1 <= end2:
            return True
        return False

    def __repr__(self):
        attrs = vars(self)
        msg = "Shift "
        msg += ', '.join(f"{key}:{value}" for key, value in attrs.items())
        return msg
