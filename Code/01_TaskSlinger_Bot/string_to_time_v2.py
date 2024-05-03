import time
"""
step 1: convert to 24 hour time
if am in string -> no need to +12 to convert to 24 hour time
if pm in string -> +12 to convert to 24 hour time
if hr in string -> already in 24 hour time
if hours in string -> already in 24 hour time

if hours > 12, do not add 12

step 2: drop the 'am' or 'pm' or 'hr' or 'hours'
handle the following:
    1315, 13:15

"""
# time hours-minutes-seconds format
time_strings = ["09:15", "09:15 hrs", "23:15 hrs", '3:45pm', '3pm', '345pm', '1115pm', "1030am", "10:30am", "10:30 am", '11am', '7pm']
format_codes = ["%H:%M", "%H:%M hrs", "%H%Mam", "%H:%Mam"]


def time_to_time_str(time_obj: time) -> str:
    return str(time_obj.tm_hour).zfill(2) + ':' + str(time_obj.tm_min).zfill(2)

def add_12(t: str, sep: str) -> str:
    # t: input that was either am or pm, and not already in 24 hr format
    minutes = t.split(sep)[1].zfill(2)
    hr = str(int(t.split(sep)[0]) + 12)
    # print(f"hr: {hr}")
    t = hr.zfill(2) + ':' + minutes.zfill(2)
    return t


def convert_to_24_hr_format(t: str, time_of_day: str) -> str:
    if ':' in t:
        # assume it is in 24 hr format with no extra numbers i.e nn:nn and not nnn:nnnn
        if time_of_day == "pm" and int(t.split(':')[0]) < 12:
            t = add_12(t, ':')
    elif len(t) > 4:  # e.g. 11155pm, the time is an error:, return a default 00:00
        t = '00:00'
        return t
    elif len(t) == 4:  # e.g. 0345am or 0345pm
        t = t[:2] + ':' + t[2:]
        if time_of_day == "pm" and int(t.split(':')[0]) < 12:
            t = add_12(t, ':')
    elif len(t) == 3:  # e.g. 345am or 345pm
        t = t[:1] + ':' + t[1:]
        if time_of_day == "pm" and int(t.split(':')[0]) < 12:
            t = add_12(t, ':')
    elif len(t) == 2 or len(t) == 1:  # e.g. 3am or 3pm
        t = t + ':00'
        if time_of_day == "pm" and int(t.split(':')[0]) < 12:
            t = add_12(t, ':')
    return t


def convert_to_24_hour_string(time_str: str) -> str:
    t = time_str.strip().lower()
    if 'am' in t:
        t = t.replace('am', '').strip()
        t = convert_to_24_hr_format(t, 'am')
    elif 'pm' in t:
        t = t.replace('pm', '').strip()
        t = convert_to_24_hr_format(t, 'pm')
    elif 'hrs' in t:
        t = t.replace('hrs', '').strip()
    elif 'hours' in t:
        t = t.replace('hrs', '').strip()
    elif ':' in t:
        pass

    # if the next line crashes, it means that the above rules did not catch a particular pattern
    t = t.split(':')[0].zfill(2) + ':' + t.split(':')[1].zfill(2)
    return t


def from_str_get_time_obj(t: str):
    return time.strptime(convert_to_24_hour_string(t), format_codes[0])


def from_str_get_24hr_time_str(t: str) -> str:
    """

    :param t:
    :return: HH:MM (does not return SS)
    """
    t = time.strptime(convert_to_24_hour_string(t), format_codes[0])
    return time_to_time_str(t)


if __name__ == "__main__":
    for idx, ts in enumerate(time_strings):
        print(f"time string idx: {idx} ------>\t{time_strings[idx]}")
        print('\tconvert_to_24_hour_string -->   ', convert_to_24_hour_string(ts))

        # with the 24 hr strings, get the time object
        try:
            tt = time.strptime(convert_to_24_hour_string(ts), format_codes[0])  # convert to datetime obj
            tt_str = time_to_time_str(tt)  # convert to str
            print('\t\t\t\t\t', tt_str)
        except ValueError as e:
            pass

        print()
        print('*'*100)

