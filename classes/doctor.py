from functools import cmp_to_key

from classes.timeoff import TimeOff, compare_timeoff
from settings.config import (
    Seniority, ExpectedHours, Locations, ExpectedNights, ExpectedWeekends,
    MAX_CONSECUTIVE_NIGHT_SHIFTS, MAX_CONSECUTIVE_WEEKEND_SHIFTS
)


class Doctor:
    def __init__(self,
                 block,
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
        assert type(carry_hours) == float, f"Carried hour for {name} is {carry_hours}, but must be a float"
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
            assert len(requested_timeoff) <= 1, f"{name} requested {len(requested_timeoff)} times-off but must choose at most 1 for a half block"
            assert requested_timeoff[0].duration <= 48, f"{name} requested {requested_timeoff[0].duration} hours off, but must be less than or equal to 48 hours for a half block"
            if half_block == "1":
                assert requested_timeoff[0].start_day <= 14, f"{name} requested day {requested_timeoff[0].start_day} off, but is on for first half of the block"
            else:
                assert 15 <= requested_timeoff[0].start_day, f"{name} requested day {requested_timeoff[0].start_day} off, but is on for the second half of the block"
        if half_block == "both":
            assert len(requested_timeoff) <= 2, f"{name} requested {len(requested_timeoff)} times-off but must choose at most 2 for a full block"
            requested_timeoff.sort(key=cmp_to_key(compare_timeoff))
            if len(requested_timeoff) == 2:
                shorter = requested_timeoff[0].duration
                longer = requested_timeoff[1].duration
                assert shorter <= 12, f"{name} requested {shorter} hours off, but must be less than 12 hours for the shorter request"
                assert longer <= 72, f"{name} requested {longer} hours off, but must be less than 72 hours for the longer request"
            elif len(requested_timeoff) == 1:
                duration = requested_timeoff[0].duration
                assert duration <= 72, f"{name} requested {duration} hours off, but must be less than 72 hours"

        assert 0 <= pre_block_hours, f"Pre-block hours worked for this week by {name} is {pre_block_hours}, but must be non-negative"

        # Negate carry hours, negative hours means they worked X hours
        carry_hours *= -1
        assert carry_hours >= pre_block_hours, f"{name} worked {pre_block_hours} this week before the block started, so there minimum carried hours should be at least this large, found {carry_hours}"

        # Only use pre_block_hours if they are working the first half
        weekly_hours = [pre_block_hours]
        if half_block == "2":
            weekly_hours = [0]

        self.block = block
        self.name = name
        self.seniority = Seniority(seniority)
        self.chief = True if chief == "yes" else False
        self.carry_hours = carry_hours
        self.half_block = half_block
        self.pre_block_hours = pre_block_hours
        self.weekly_hours = weekly_hours
        self.requested_timeoff = requested_timeoff
        self.mandatory_timeoff = mandatory_timeoff
        self.expected_hours = self.calculate_expected_hours()
        self.expected_night_range = self.calculate_expected_night_shift_range()
        self.expected_weekend_range = self.calculate_expected_weekend_shift_range()
        self.actual_hours = carry_hours  # TODO: confirm that only carry is used for total hours worked
        self.actual_nights = 0
        self.actual_weekends = 0
        self.actual_shifts = 0
        self.consecutive_weekend_shifts = 0
        self.consecutive_night_shifts = 0
        self.location_hours = {location: 0 for location in Locations}
        self.shifts = []

        # Add Wednesday conference for EM residents
        if not Seniority(seniority) == Seniority.OFF_SERVICE:
            for day in range(block.start, block.end+1):
                if day % 7 == 3 and self.working_on_day(day):
                    self.add_mandatory_time_off(day, 7, 8)

        print(f'Creating {self}')

    def __repr__(self):
        attrs = vars(self)
        msg = "Doctor "
        msg += ', '.join(f"{key}:{value}" for key, value in attrs.items())
        return msg

    def get_start_day(self):
        start_day = self.block.start
        if self.half_block == "2":
            start_day = 15
        return start_day

    def get_end_day(self):
        end_day = self.block.end
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
        timeoff = TimeOff(self.block, self.name, start_day, start_time, duration, mandatory=True)
        self.mandatory_timeoff.append(timeoff)

    def remove_mandatory_timeoff(self):
        assert len(self.mandatory_timeoff) > 0, f"Mandatory timeoff cannot be removed from {self.name}, None exist"
        self.mandatory_timeoff.pop()

    def worked_weekly_max_hours(self):
        """
        This should return True if they worked 60 hours from the previous Sunday
        to next Sunday (carried hours should be added if its the first week)
        """
        return bool(60 <= self.weekly_hours[-1])

    def received_weekly_break(self):
        # TODO: write this if it is a problem that people aren't getting breaks
        """
        This should return True if they had a 24 hour break from the previous
        Sunday to next Sunday.
        """
        pass

    def overlaps_second_block(self, day):
        """
        Check if the first day of the week overlaps with the second block
        (day 15).
        """
        return bool(day == 15)

    def reset_weekly_hours(self, day):
        """
        Reset when shift starts on Sunday 7am signifying the new week.
        Track each weeks weekly hours to allow for backtracking.
        If newest week overlaps with second block (day 15), override weekly
        hours.
        """
        hours = 0
        if self.overlaps_second_block(day):
            hours = self.pre_block_hours

        self.weekly_hours.append(hours)

    def undo_reset_weekly_hours(self):
        """
        Remove this current weeks weekly hours when backtracking.
        """
        assert len(self.weekly_hours) > 0, f"Weekly hours cannot be removed from {self.name}, None exist"
        self.weekly_hours.pop()

    def calculate_consecutive_nights(self):
        """
        When backtracking, consecutive nights need to be recalculated using the
        doctors shifts. This is because removing a day that occurs after a
        string of nights tells you consecutive nights can be reset to zero. But
        removing a night that occurs after a string of days does not tell you
        how many nights occur before this.

        """
        consecutive_nights = 0
        for shift in reversed(self.shifts):
            if shift.night:
                consecutive_nights += 1
            else:
                break
        return consecutive_nights

    def calculate_consecutive_weekends(self):
        consecutive_weekend_shifts = 0
        for shift in reversed(self.shifts):
            if shift.weekend:
                consecutive_weekend_shifts += 1
            else:
                break
        return consecutive_weekend_shifts

    def add_shift(self, shift):
        # Add actual hours worked, nights, and weekend count by this shift
        # Then add mandatory time off after the shift
        # And hours by location
        # Save shift for doctor
        self.actual_shifts += 1
        self.actual_hours += shift.duration
        self.weekly_hours[-1] += shift.duration
        self.location_hours[shift.location] += shift.duration
        if shift.night:
            self.actual_nights += 1
            self.consecutive_night_shifts += 1
        else:
            self.consecutive_night_shifts = 0

        if shift.weekend:
            self.actual_weekends += 1
            self.consecutive_weekend_shifts += 1
        else:
            self.consecutive_weekend_shifts = 0

        start_day = shift.start_day + (shift.start_time + shift.duration) // 24
        start_time = shift.start_time + (shift.start_time + shift.duration) % 24
        self.add_mandatory_time_off(start_day, start_time, shift.duration)
        self.shifts.append(shift)

    def remove_shift(self):
        assert len(self.shifts) > 0, f"Shift cannot be removed from {self.name}, None exist"

        # TODO: test that popping a day that had a string of nights before sets consecutive nights properly
        shift = self.shifts.pop()
        self.actual_shifts -= 1
        self.actual_hours -= shift.duration
        self.weekly_hours[-1] -= shift.duration
        self.location_hours[shift.location] -= shift.duration

        # Note: You could calculate consecutive nights/weekends every time
        # a shift is added or removed but this would be slower than incrementing
        # and decrementing and only recalculating when you absolutely need to.
        if shift.night:
            self.actual_nights -= 1
            self.consecutive_night_shifts -= 1
        else:
            # Cannot decrement or reset to zero, need to calculate using the shifts
            self.consecutive_night_shifts = self.calculate_consecutive_nights()

        if shift.weekend:
            self.actual_weekends -= 1
            self.consecutive_weekend_shifts -= 1
        else:
            # Cannot decrement or reset to zero, need to calculate using the shifts
            self.consecutive_weekend_shifts = self.calculate_consecutive_weekends()

        assert len(self.mandatory_timeoff) > 0, f"Mandatory timeoff cannot be removed from {self.name}, None exist"
        self.mandatory_timeoff.pop() # TODO: check popping last does not have a corner case
        # TODO: remove consecutive nights and weekends

    def can_work_more_night_shifts(self):
        if self.consecutive_night_shifts == MAX_CONSECUTIVE_NIGHT_SHIFTS:
            return False
        # Already reached upper boundary of nights
        if self.actual_nights == self.expected_night_range[1]:
            return False

        return True

    def can_work_more_weekend_shifts(self):
        if self.consecutive_weekend_shifts == MAX_CONSECUTIVE_WEEKEND_SHIFTS:
            return False
        # Already reached upper boundary of weekends
        if self.actual_weekends == self.expected_weekend_range[1]:
            return False

        return True

    def stats(self):
        # TODO: remove this, don't think it is useful since all member attributes
        #   of doctor can be printed out with representation
        """
        Recalculate carried hours after schedule is complete
        """
        pass
