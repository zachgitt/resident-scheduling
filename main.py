from classes import Block, Schedule
from settings.block import START_DAY, END_DAY
from parse import parse_doctors, parse_shifts


if __name__ == "__main__":
    block = Block(START_DAY, END_DAY)
    doctors = parse_doctors('settings/doctors.csv')
    shifts = parse_shifts('settings/shifts.csv')
    schedule = Schedule(block, doctors, shifts)
    # TODO: save schedule to image
