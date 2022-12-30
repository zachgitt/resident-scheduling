from classes.block import Block
from classes.schedule import Schedule
from settings.block import START_DAY, END_DAY
from parse import parse_doctors, parse_shifts


if __name__ == "__main__":
    block = Block(START_DAY, END_DAY)
    doctors = parse_doctors(block, 'settings/doctors.csv')
    shifts = parse_shifts(block, 'settings/shifts.csv')
    schedule = Schedule(block, doctors, shifts)
    schedule.create_extra_shifts(shifts, doctors)

    print('PRINTING SCHEDULE AND STATS')
    print(schedule)
    for doctor in doctors:
        print(doctor)
