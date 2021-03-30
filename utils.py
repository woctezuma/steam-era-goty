# Reference: https://github.com/woctezuma/metacouncil-goty/blob/master/extend_steamspy.py

import steampi.calendar


def get_release_year_for_problematic_app_id(app_id):
    # As of December 2020, SteamSpy returns release_date_as_str = "29 янв. 2015" for appID = "319630".
    release_date_as_str = steampi.calendar.get_release_date_as_str(app_id=app_id)
    matched_release_year = release_date_as_str.split(' ')[-1]
    try:
        matched_release_year_as_int = int(matched_release_year)
    except ValueError:
        matched_release_year = release_date_as_str.split(' ')[0]
        matched_release_year_as_int = int(matched_release_year)

    return matched_release_year_as_int
