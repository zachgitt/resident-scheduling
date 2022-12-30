from functools import cmp_to_key

from classes.shift import compare_shifts
global_shift = None


def compare_doctors(doctor1, doctor2):
    # Order: Front-Back is Last-First so the doctor at the back of the list
    # should be chosen first

    # 1. Requested Timeoff
    # 2. String nights
    # 3. String weekends
    # 4. Amount of weekends
    # 5. Amount of nights
    # 6. Shift preference
    # 7. Hours needed
    # 8. Location hours

    # Requested Timeoff
    wants_timeoff1 = False
    wants_timeoff2 = False
    for timeoff1 in doctor1.requested_timeoff:
        if global_shift.overlaps_timeoff(timeoff1):
            wants_timeoff1 = True
    for timeoff2 in doctor2.requested_timeoff:
        if global_shift.overlaps_timeoff(timeoff2):
            wants_timeoff2 = True
    if wants_timeoff1 and not wants_timeoff2:
        return -1
    elif not wants_timeoff1 and wants_timeoff2:
        return 1

    # String nights
    # Doctors who are mid-strung are prioritized (back of list is popped first)
    # After 2 weekend shifts, doctors no longer work weekends
    if doctor1.consecutive_night_shifts < doctor2.consecutive_night_shifts:
        return -1
    elif doctor1.consecutive_night_shifts > doctor2.consecutive_night_shifts:
        return 1

    # String weekends
    # After 5 night shifts
    if doctor1.consecutive_weekend_shifts < doctor2.consecutive_weekend_shifts:
        return -1
    elif doctor1.consecutive_weekend_shifts > doctor2.consecutive_weekend_shifts:
        return 1

    # TODO: doctors who are mid weekend/night shift are sorted higher
    if doctor1.string_nights < doctor2.string_nights:
        return -1
    elif doctor1.string_nights > doctor2.string_nights:
        return 1

    # Amount of weekends, upper bound
    weekends_needed1 = doctor1.expected_weekend_range[1] - doctor1.actual_weekends
    weekends_needed2 = doctor2.expected_weekend_range[1] - doctor2.actual_weekends
    if weekends_needed1 < weekends_needed2:
        return -1
    elif weekends_needed1 > weekends_needed2:
        return 1

    # Amount of nights, upper bound
    nights_needed1 = doctor1.expected_night_range[1] - doctor1.actual_nights
    nights_needed2 = doctor2.expected_night_range[1] - doctor2.actual_nights
    if nights_needed1 < nights_needed2:
        return -1
    elif nights_needed1 > nights_needed2:
        return 1

    # Preference for seniority
    position_preferences = global_shift.position_preferences
    seniority_index1 = -1
    for i, seniority in position_preferences:
        # TODO: test that this compares properly
        if seniority == doctor1.seniority:
            seniority_index1 = i
    seniority_index2 = -1
    for j, seniority, in position_preferences:
        if seniority == doctor2.seniority:
            seniority_index2 = j
    assert seniority_index1 != -1, f"Preferences for shift are {position_preferences}, but doctor1 seniority is {doctor1.seniority}"
    assert seniority_index2 != -1, f"Preferences for shift are {position_preferences}, but doctor2 seniority is {doctor2.seniority}"
    # Smaller index represents higher priority
    if seniority_index1 > seniority_index2:
        return -1
    elif seniority_index1 < seniority_index2:
        return 1

    # Hours needed
    hours_needed1 = doctor1.expected_hours - doctor1.actual_hours
    hours_needed2 = doctor2.expected_hours - doctor2.actual_hours
    if hours_needed1 < hours_needed2:
        return -1
    elif hours_needed1 > hours_needed2:
        return 1

    # Location hours, less location hours should be prioritized
    location_hours1 = doctor1.location_hours[global_shift.location]
    location_hours2 = doctor2.location_hours[global_shift.location]
    if location_hours1 > location_hours2:
        return -1
    elif location_hours1 < location_hours2:
        return 1

    # Doctors tied
    return 0


class Schedule:
    def __init__(self, block, doctors, shifts):
        # Sort shifts based on start time
        # TODO: filter out optional shifts
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
        sorted_doctors = self.sort_doctors(available_doctors)
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

            # Shift would exceed expected nights
            if doctor.actual_nights == doctor.expected_night_range[1]:
                continue

            # Shift would exceed number of weekends
            if doctor.actual_weekends == doctor.expected_weekend_range[1]:
                continue

            # Shift would exceed 60 hours
            if doctor.weekly_hours[-1] + shift.duration > 60:
                continue

            # Doctor hit the max weekend string
            if not doctor.can_work_more_weekend_shifts():
                continue

            # Doctor hit the max night string
            if not doctor.can_work_more_night_shifts():
                continue

            available.append(doctor)

        return available

    def sort_doctors(self, doctors):
        return sorted(doctors, key=cmp_to_key(compare_doctors))

    def choose_doctor(self, doctors):
        if len(doctors) == 0:
            return None

        # TODO: potentially randomize instead of selecting the best doctor
        return doctors[-1]

    def create_extra_shifts(self, shifts, doctors):
        """
        Create extra shifts for doctors that do not have enough hours.
        TODO: only use optional shifts for this
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
                    doctor.reset_weekly_hours(shift.start_day)

    def export(self):
        # TODO: export schedule to image or csv
        pass

    def __repr__(self):
        print('FINAL SCHEDULE:')
        for shift in self.schedule:
            print(shift)