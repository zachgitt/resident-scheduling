def test_parse_doctor_succeeds():
    doctors = parse_doctors('tests/inputs/doctors_succeeds.csv')
    # Check the number of doctors is correct
    # Check chief is chief
    pass

def test_parse_doctor_invalid_requested_timeoff_format():
    doctors = parse_doctors('tests/input/doctors_invalid_timeoff.csv') # 13:25:8
    pass