def compare_timeoff(timeoff1, timeoff2):
    """Sort in chronological order"""
    if timeoff1.start_day < timeoff2.start_day:
        return -1
    elif timeoff1.start_day > timeoff2.start_day:
        return 1
    elif timeoff1.start_time < timeoff2.start_time:
        return -1
    elif timeoff1.start_time > timeoff2.start_time:
        return 1
    else:
        return 0


class TimeOff:
    def __init__(self, block, name, start_day, start_time, duration, mandatory=True):
        # Validate types
        assert type(start_day) == int, f"Day for {name}'s time-off is {start_day}, but must be an integer"
        assert type(start_time) == int, f"Start time for {name}'s time-off is {start_time}, but must be an integer"
        assert type(duration) == int, f"Duration for {name}'s time-off is {duration}, but must be an integer"

        # Validate day
        assert block.start <= start_day <= block.end, f"Day for {name}'s time-off is {start_day}, but must be between {block.start} and {block.end}"

        # Validate start time
        assert 0 <= start_time <= 23, f"Start time for {name}'s time-off is {start_time}, but must be between 0 and 23"
        if start_day == block.start:
            assert 7 <= start_time, f"Start time for {name}'s time-off is {start_time}, but must be after 7am for the first day"

        # Validate duration
        # If working 4 weeks, they can do upto 12 and upto 72
        # If working 2 weeks, they get upto 48
        if not mandatory:
            assert duration <= 72, f"Duration for {name}'s requested time-off is {duration}, but must be less than or equal to 72 hours"
        end_day = start_day + (start_time + duration) // 24 # TODO: test 12 hours after 7pm start produces the second day
        end_time = (start_time + duration % 24) % 24

        # Days start at 7am, so you just need to end at or before the day after last
        if end_day == block.end + 1:
            assert end_time <= 7, f"End time for {name}'s time-off is {end_time}, but must end before 7am if it extends past the last day"

        self.start_day = start_day
        self.start_time = start_time
        self.duration = duration

    def __repr__(self):
        attrs = vars(self)
        msg = ', '.join(f"{key}:{value}" for key, value in attrs.items())
        return f"({msg})"
