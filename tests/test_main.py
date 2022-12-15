def test_
block = Block(START_DAY, END_DAY)
doctors = parse_doctors('settings/doctors.csv')
shifts = parse_shifts('settings/shifts.csv')
schedule = Schedule(block, doctors, shifts)