from functools import cmp_to_key
from settings.block import START_DAY, END_DAY
from settings.config import Seniority, ExpectedHours, Locations, ExpectedNights, ExpectedWeekends


class Block:
    def __init__(self, block_start=1, block_end=28):
        assert -5 <= block_start <= 7, f"Block start is {block_start}, but must begin within 7 days of day 1"
        assert 22 <= block_end <= 34, f"Block end is {block_end}, but must end within 7 days of day 28"
        self.block_start = block_start
        self.block_end = block_end
        print(f'Creating {self}')

    def __repr__(self):
        return f'Block=[{self.block_start}, {self.block_end}]'


class Doctor:
    def __init__(self,
                 name,
                 seniority,
                 chief="No",
                 carry_hours=0,
                 half_block="Both",
                 pre_block_hours=0,
                 requested_timeoff=None,
                 mandatory_timeoff=None,
                 ):

        # Set potentially immutable type
        if requested_timeoff is None:
            requested_timeoff = []
        if mandatory_timeoff is None:
            mandatory_timeoff = []

        # Validate types
        assert type(name) == str, f"Doctor name is {name}, but must be a string"
        assert type(seniority) == int, f"Seniority for {name} is {seniority}, but must be an integer"
        assert type(chief) == str, f"Chief for {name} is {chief}, but must be a string"
        assert type(carry_hours) == int, f"Carried hour for {name} is {carry_hours}, but must be an integer"
        assert type(half_block) == str, f"Half block for {name} is {half_block}, but must be a string"
        assert type(pre_block_hours) == int, f"Pre-block hours worked this week by {name} is {pre_block_hours} but must be an integer"
        assert isinstance(requested_timeoff, list), f"Requested time-off for {name} is {requested_timeoff}, but must be a list"
        assert isinstance(mandatory_timeoff, list), f"Mandatory time-off for {name} is {mandatory_timeoff}, but must be a list"

        assert Seniority.has_value(seniority), f"Seniority is {seniority}, but must be between 0 and 4 which represent Off-Service, First Year, Second Year, Third Year, Fourth Year"

        # Lowercase input
        chief = chief.lower()
        half_block = half_block.lower()

        assert chief in ["no", "yes"], f"Chief for {name} is {chief}, but must be 'Yes' or 'No'"
        assert half_block in ["1", "2", "both"], f"Half block for {name} is {half_block}, but must be '1', '2', or 'Both'"
        if half_block in ["1", "2"]:
            assert len(requested_timeoff) == 1, f"{name} requested {len(requested_timeoff)} times-off but must choose 1 for a half block"
            assert requested_timeoff[0].duration == 48, f"{name} requested {requested_timeoff[0].duration} hours off, but must be 48 hours for a half block"
            if half_block == "1":
                assert requested_timeoff[0].start_day <= 14, f"{name} requested day {requested_timeoff[0].start_day} off, but is on for first half of the block"
            else:
                assert 15 <= requested_timeoff[0].start_day, f"{name} requested day {requested_timeoff[0].start_day} off, but is on for the second half of the block"
        if half_block == "both":
            assert len(requested_timeoff) == 2, f"{name} requested {len(requested_timeoff)} times-off but must choose 2 for a full block"
            for rt in requested_timeoff:
                assert rt.duration in [12, 72], f"{name} requested {rt.duration} hours off, but must be 12 or 72 hours for a full block"
        assert 0 <= pre_block_hours, f"Pre-block hours worked for this week by {name} is {pre_block_hours}, but must be non-negative"

        assert carry_hours >= pre_block_hours, f"{name} worked {pre_block_hours} this week before the block started, so there minimum carried hours should be at least this large, found {carry_hours}"

        self.name = name
        self.seniority = Seniority(seniority)
        self.chief = True if chief == "yes" else False
        self.carry_hours = carry_hours
        self.half_block = half_block
        self.weekly_hours = [pre_block_hours]
        self.requested_timeoff = requested_timeoff
        self.mandatory_timeoff = mandatory_timeoff
        self.expected_hours = self.calculate_expected_hours()
        self.expected_night_range = self.calculate_expected_night_shift_range()
        self.expected_weekend_range = self.calculate_expected_weekend_shift_range()
        self.actual_hours = carry_hours  # TODO: confirm that only carry is used for total hours worked
        self.actual_nights = 0 # TODO: determine if there are carry nights
        self.actual_weekends = 0 # TODO: determine if there are carry weekends
        self.actual_shifts = 0

        # Add Wednesday conference for EM residents
        if not Seniority(seniority) == Seniority.OFF_SERVICE:
            for day in range(START_DAY, END_DAY+1):
                if day % 7 == 3 and self.working_on_day(day):
                    self.add_mandatory_time_off(day, 7, 8)

        print(f'Creating {self}')

    def __repr__(self):
        attrs = vars(self)
        msg = "Doctor "
        msg += ', '.join(f"{key}:{value}" for key, value in attrs.items())
        return msg

    def get_start_day(self):
        start_day = START_DAY
        if self.half_block == "2":
            start_day = 15
        return start_day

    def get_end_day(self):
        end_day = END_DAY
        if self.half_block == "1":
            end_day = 14
        return end_day

    def get_working_days(self):
        return self.get_end_day() - self.get_start_day() + 1

    def calculate_expected_hours(self):
        expected_hours = ExpectedHours[self.seniority]
        if self.chief:
            expected_hours = 124

        working_days = self.get_working_days()
        return expected_hours * (working_days / 28)

    def calculate_expected_night_shift_range(self):
        expected_nights_range = ExpectedNights[self.seniority]
        lower = expected_nights_range[0]
        upper = expected_nights_range[1]

        working_days = self.get_working_days()
        ratio = working_days / 28
        night_range = (lower * ratio, upper * ratio)

        return night_range

    def calculate_expected_weekend_shift_range(self):
        expected_weekends_range = ExpectedWeekends[self.seniority]
        lower = expected_weekends_range[0]
        upper = expected_weekends_range[1]

        working_days = self.get_working_days()
        ratio = working_days / 28
        weekend_range = (lower * ratio, upper * ratio)

        return weekend_range

    def working_on_day(self, day):
        return bool(self.get_start_day() <= day <= self.get_end_day())

    def add_mandatory_time_off(self, start_day, start_time, duration):
        """
        This should be called by any doctor after they are assigned a shift
        """
        timeoff = TimeOff(self.name, start_day, start_time, duration, mandatory=True)
        self.mandatory_timeoff.append(timeoff)

    def remove_mandatory_time_off(self):
        self.mandatory_timeoff.pop()

    def worked_weekly_max_hours(self):
        """
        This should return True if they worked 60 hours from the previous Sunday
        to next Sunday (carried hours should be added if its the first week)
        """
        return bool(60 <= self.weekly_hours[-1])

    def received_weekly_break(self):
        """
        This should return True if they had a 24 hour break from the previous
        Sunday to next Sunday.
        """
        pass

    def reset_weekly_hours(self):
        """
        Reset when shift starts on Sunday 7am signifying the new week.
        Track each weeks weekly hours to allow for backtracking.
        """
        self.weekly_hours.append(0)

    def undo_reset_weekly_hours(self):
        """
        Remove this current weeks weekly hours when backtracking.
        """
        self.weekly_hours.pop()

    def add_shift(self, shift):
        # Add actual hours worked, nights, and weekend count by this shift
        # Then add mandatory time off after the shift
        self.actual_shifts += 1
        self.actual_hours += shift.duration
        self.weekly_hours[-1] += shift.duration
        if shift.night:
            self.actual_nights += 1
        if shift.weekend:
            self.actual_weekends += 1

        start_day = shift.start_day + (shift.start_time + shift.duration) // 24
        start_time = shift.start_time + (shift.start_time + shift.duration) % 24
        self.add_mandatory_time_off(start_day, start_time, shift.duration)

    def remove_shift(self, shift):
        self.actual_shifts -= 1
        self.actual_hours -= shift.duration
        self.weekly_hours[-1] -= shift.duration
        if shift.night:
            self.actual_shifts -= 1
        if shift.weekend:
            self.actual_weekends -= 1
        self.mandatory_timeoff.pop() # TODO: check popping last does not have a corner case

    def stats(self):
        """
        Recalculate carried hours after schedule is complete
        """
        pass


class TimeOff:
    def __init__(self, name, start_day, start_time, duration, mandatory=True):
        # Validate types
        assert type(start_day) == int, f"Day for {name}'s time-off is {start_day}, but must be an integer"
        assert type(start_time) == int, f"Start time for {name}'s time-off is {start_time}, but must be an integer"
        assert type(duration) == int, f"Duration for {name}'s time-off is {duration}, but must be an integer"

        # Validate day
        assert START_DAY <= start_day <= END_DAY, f"Day for {name}'s time-off is {start_day}, but must be between {START_DAY} and {END_DAY}"

        # Validate start time
        assert 0 <= start_time <= 23, f"Start time for {name}'s time-off is {start_time}, but must be between 0 and 23"
        if start_day == START_DAY:
            assert 7 <= start_time, f"Start time for {name}'s time-off is {start_time}, but must be after 7am for the first day"

        # Validate duration
        # TODO: set limitations for mandatory time off as well
        if not mandatory:
            assert duration in [12, 48, 72], f"Duration for {name}'s requested time-off is {duration}, but can only be 12, 48 or 72 hours"
        end_day = start_day + (start_time + duration) // 24 # TODO: test 12 hours after 7pm start produces the second day
        end_time = (start_time + duration % 24) % 24

        # Days start at 7am, so you just need to end at or before the day after last
        if end_day == END_DAY + 1:
            assert end_time <= 7, f"End time for {name}'s time-off is {end_time}, but must end before 7am if it extends past the last day"

        self.start_day = start_day
        self.start_time = start_time
        self.duration = duration

    def __repr__(self):
        attrs = vars(self)
        msg = ', '.join(f"{key}:{value}" for key, value in attrs.items())
        return f"({msg})"


class PositionPreferences:
    def __init__(self, most_to_least_preferred):
        """
        These are the accepted seniorities for this position, listed in descending
        preference.
        """
        assert isinstance(most_to_least_preferred, list), f"Preferred seniority is {most_to_least_preferred}, but should be a list type"
        self.preferences = most_to_least_preferred


# TODO: create check_day_time_duration which should be reused by TimeOff and Shift


class Shift:
    def __init__(self, location, start_day, start_time, duration, position_preferences):
        # Validate types
        assert type(location) == str
        assert type(start_day) == int
        assert type(start_time) == int
        assert type(duration) == int
        assert isinstance(position_preferences, list)

        assert location in Locations, f"Shift location is {location}, but must be one of {', '.join([l for l in Locations])}"

        # Validate day
        assert START_DAY <= start_day <= END_DAY, f"Shift start day for {location} is {start_day}, but must be between {START_DAY} and {END_DAY}"

        # Validate start time
        assert 0 <= start_time <= 23, f"Shift start time for {location} is {start_time}, but must be between 0 and 23"
        if start_day == START_DAY:
            assert 7 <= start_time, f"Shift start time for {location} is {start_time}, but must be after 7am for the first day"

        # Validate duration
        assert duration in [8, 9, 10, 12], f"Shift duration for {location} is {duration}, but can only be 8, 9, 10 or 12 hours"
        end_day = start_day + (start_time + duration) // 24
        end_time = (start_time + duration % 24) % 24

        # Days start at 7am, so you just need to end at or before the day after last
        if end_day == END_DAY + 1:
            assert end_time <= 7, f"Shift end time for {location} is {end_time}, but must end before 7am if it extends past the last day"

        self.location = location
        self.start_day = start_day
        self.start_time = start_time
        self.duration = duration
        self.position_preferences = position_preferences
        self.night = self.determine_if_night(start_time)
        self.weekend = self.determine_if_weekend(start_day, start_time)
        self.doctor = None

        print(f'Creating {self}')

    def assign_doctor(self, doctor):
        self.doctor = doctor
        doctor.add_shift(self)
        doctor.add_mandatory_time_off(self.start_time, self.start_time, self.duration)
        print(f'Assigning Shift:{self} to Doctor:{doctor}')

    def unassign_doctor(self, doctor):
        self.doctor = None
        doctor.remove_shift(self)
        doctor.remove_mandatory_time_off()
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


def higher_preference(preferences, doctor1, doctor2):
    # TODO: return True if doctor1 has higher preference than doctor2
    pass


global_shift = None
def compare_doctors(doctor1, doctor2):
    # Order
    # TODO: still unsure how to make sure the end result will be balanced,
    #   perhaps do the best upto expected weekends/nights lower bounds, and
    #   then round robin? Or do swaps at the end?
    #   FRED -- would it be ok to have some people be within 1 of each other?
    #       otherwise it would be difficult to add 3-5 nights or 2 weekends

    # Sort by hours needed, nights needed, weekends needed, shift preference
    # Move to back of list if requested this time off
    position_preferences = global_shift.position_preferences

    # TODO: doctors who are mid weekend/night shift are sorted higher
    if doctor1.string_nights < doctor2.string_nights:
        return -1
    elif doctor1.string_nights > doctor2.string_nights:
        return 1


    return 0


class Schedule:
    def __init__(self, block, doctors, shifts):
        # Sort shifts based on start time
        shifts.sort(key=cmp_to_key(compare_shifts))
        curr_schedule = []
        self.schedule = self.search(doctors, shifts, 0, curr_schedule)

    def search(self, doctors, shifts, i, curr_schedule):
        if len(shifts) == i:
            print('Schedule Complete!!!')
            return curr_schedule

        # Set shift to be used by sorting comparator
        shift = shifts[i]
        global global_shift
        global_shift = shift

        self.try_resetting_weekly_hours(doctors, shifts, i)
        available_doctors = self.filter_available_doctors(doctors, shift)
        sorted_doctors = self.sort_doctors(available_doctors, shift)
        doctor = self.choose_doctor(sorted_doctors)

        if doctor is None:
            self.undo_try_resetting_weekly_hours(doctors, shifts, i)
            return None

        # Continue iterating
        shift.assign_doctor(doctor)
        response = self.search(doctors, shifts, i+1, curr_schedule)
        if response:
            return response
        else:
            # Backtrack
            print(f'Backtracking Shift i={i}/{len(shifts)}')
            shift.unassign_doctor(doctor)
            self.undo_try_resetting_weekly_hours(doctors, shifts, i)
            return None

    def filter_available_doctors(self, doctors, shift):
        available = []
        for doctor in doctors:
            # Mandatory timeoff
            for timeoff in doctor.mandatory_timeoff:
                if shift.overlaps_timeoff(timeoff):
                    break

            # Not working on day
            if not doctor.working_on_day(shift.start_day): # TODO: you might need to check they are not working the next day if duration goes over
                continue

            # Does not have seniority
            if doctor.seniority not in shift.position_preferences:
                continue

            # Shift would exceed 60 hours
            if doctor.weekly_hours[-1] + shift.duration > 60:
                continue

            available.append(doctor)

        return available

    def sort_doctors(self, doctors, shift):
        return sorted(doctors, key=cmp_to_key(compare_doctors))

    def choose_doctor(self, doctors):
        if len(doctors) == 0:
            return None

        # TODO: potentially randomize instead of selecting the best doctor
        return doctors[-1]

    def create_extra_shifts(self, shifts, doctors):
        """
        Create extra shifts for doctors that do not have enough hours.
        TODO: determine with fred if they are supposed to be added to specific
                shifts and not just any
        """
        pass

    def undo_try_resetting_weekly_hours(self, doctors, shifts, i):
        # When backtracking, determine if you need to remove this weeks hours
        assert i > 0, f"Undoing weekly reset hours for shift 0, but should be impossible"

        # Determine if you are crossing threshold back to last week
        prev_shift = shifts[i-1]
        shift = shifts[i]

        # Undo reset doctor weekly hours worked if newest shift is Sun 7am
        if shift.start_day % 7 == 0 and shift.start_time == 7:
            # The previous shift exists and was earlier
            if (prev_shift is not None) and \
                    (prev_shift.start_day < shift.start_day and
                     prev_shift.start_time < shift.start_time):
                print(f'Undoing resetting weekly hours between prev_shift={prev_shift} and shift={shift}')
                for doctor in doctors:
                    doctor.undo_reset_weekly_hours()


    def try_resetting_weekly_hours(self, doctors, shifts, i):
        # No need to reset if its the first # TODO: check this is accurate
        if i < 1:
            return

        prev_shift = shifts[i-1]
        shift = shifts[i]

        # Reset doctor weekly hours worked if newest shift is Sun 7am
        if shift.start_day % 7 == 0 and shift.start_time == 7:
            # The previous shift exists and was earlier
            if (prev_shift is not None) and \
               (prev_shift.start_day < shift.start_day and
                prev_shift.start_time < shift.start_time):
                print(f'Resetting weekly hours between prev_shift={prev_shift} and shift={shift}')
                for doctor in doctors:
                    doctor.reset_weekly_hours()

    def export(self):
        # TODO: export schedule to image or csv
        pass

    def __repr__(self):
        print('FINAL SCHEDULE:')
        for shift in self.schedule:
            print(shift)
