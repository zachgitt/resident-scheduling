from enum import Enum


class Seniority(Enum):
    # Off service are non-emergency residents that are on rotation
    OFF_SERVICE = 0
    FIRST_YEAR = 1
    SECOND_YEAR = 2
    THIRD_YEAR = 3
    FOURTH_YEAR = 4

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


# Standard hours assumes a 28 day cycle, this is adjusted when calculated
# per doctor depending on how many days they are working.
ExpectedHours = {
    Seniority.OFF_SERVICE: 200,
    Seniority.FIRST_YEAR: 200,
    Seniority.SECOND_YEAR: 170,
    Seniority.THIRD_YEAR: 165,
    Seniority.FOURTH_YEAR: 136,
}


# Standard nights assumes a 28 day cycle.
ExpectedNights = {
    Seniority.OFF_SERVICE: (8, 10),
    Seniority.FIRST_YEAR: (8, 10),
    Seniority.SECOND_YEAR: (6, 8),
    Seniority.THIRD_YEAR: (5, 7),
    Seniority.FOURTH_YEAR: (4, 5),
}


# Standard weekends assumes a 28 day cycle. Note bounds are inclusive
# and might repeat.
ExpectedWeekends = {
    Seniority.OFF_SERVICE: (4, 5),
    Seniority.FIRST_YEAR: (4, 5),
    Seniority.SECOND_YEAR: (4, 4),
    Seniority.THIRD_YEAR: (4, 4),
    Seniority.FOURTH_YEAR: (3, 4),
}


Locations = {
    'Acute 1',
    'Acute 2',
    'Resus'
}
