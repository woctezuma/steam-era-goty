import Levenshtein as lv

from bayesian_goty import load_input
from download_json import getTodaysSteamSpyData


def parse_votes(data, num_games_per_voter=5):
    import re

    raw_votes = dict()

    for element in data:
        tokens = re.split('(;)', element)

        voter_name = tokens[0]
        voted_games = [tokens[2 * (i + 1)] for i in range(num_games_per_voter)]

        raw_votes[voter_name] = dict()
        for i in range(len(voted_games)):
            position = num_games_per_voter - i

            game_name = voted_games[i]
            raw_votes[voter_name][position] = game_name

    return raw_votes


def normalize_votes(raw_votes, matches):
    # Index of the first neighbor
    neighbor_reference_index = 0

    normalized_votes = dict()

    for voter_name in raw_votes.keys():
        normalized_votes[voter_name] = dict()
        normalized_votes[voter_name]['ballots'] = dict()
        normalized_votes[voter_name]['distances'] = dict()
        for (position, game_name) in raw_votes[voter_name].items():

            if game_name in matches.keys():

                normalized_votes[voter_name]['ballots'][position] = matches[game_name]['matched_appID'][
                    neighbor_reference_index]
                normalized_votes[voter_name]['distances'][position] = matches[game_name]['match_distance'][
                    neighbor_reference_index]
            else:
                normalized_votes[voter_name]['ballots'][position] = None
                normalized_votes[voter_name]['distances'][position] = None

    return normalized_votes


def find_closest_appID(game_name_input, steamspy_database, num_closest_neighbors=1):
    dist = dict()

    lower_case_input = game_name_input.lower()

    for appID in steamspy_database.keys():
        str = steamspy_database[appID]['name']

        # Compare names in lower cases, to avoid mismatches for Tekken vs. TEKKEN, or Warhammer vs. WARHAMMER
        dist[appID] = lv.distance(lower_case_input, str.lower())

    sorted_appIDS = sorted(dist.keys(), key=lambda x: dist[x])

    if check_database_of_problematic_game_names(game_name_input):
        closest_appID = [find_hard_coded_appID(game_name_input)]
        if num_closest_neighbors > 1:
            closest_appID.extend(sorted_appIDS[0:(num_closest_neighbors - 1)])
    else:
        closest_appID = sorted_appIDS[0:num_closest_neighbors]

    closest_distance = [dist[appID] for appID in closest_appID]

    return (closest_appID, closest_distance)


def precompute_matches(raw_votes, steamspy_database, num_closest_neighbors=1):
    seen_game_names = set()
    matches = dict()

    for voter in raw_votes.keys():
        for (position, raw_name) in raw_votes[voter].items():
            if raw_name not in seen_game_names:
                seen_game_names.add(raw_name)

                if raw_name != '':
                    (closest_appID, closest_distance) = find_closest_appID(raw_name, steamspy_database,
                                                                           num_closest_neighbors)

                    element = dict()
                    element['input_name'] = raw_name
                    element['matched_appID'] = closest_appID
                    element['matched_name'] = [steamspy_database[appID]['name'] for appID in closest_appID]
                    element['match_distance'] = closest_distance

                    matches[raw_name] = element

    return matches


def display_matches(matches):
    # Index of the neighbor used to sort keys of the matches dictionary
    neighbor_reference_index = 0

    sorted_keys = sorted(matches.keys(),
                         key=lambda x: matches[x]['match_distance'][neighbor_reference_index] / (
                                 1 + len(matches[x]['input_name'])))

    for game in sorted_keys:
        element = matches[game]

        dist_reference = element['match_distance'][neighbor_reference_index]
        game_name = element['input_name']

        if dist_reference > 0 and check_database_of_problematic_game_names(game_name):

            print('\n' + game_name
                  + ' (' + 'length:' + str(len(game_name)) + ')'
                  + ' ---> ', end='')
            for neighbor_index in range(len(element['match_distance'])):
                dist = element['match_distance'][neighbor_index]
                print(element['matched_name'][neighbor_index]
                      + ' (appID: ' + element['matched_appID'][neighbor_index]
                      + ' ; ' + 'distance:' + str(dist) + ')', end='\t')

    return


def get_hard_coded_appID_dict():
    # Hard-coded list of game names which are wrongly matched with Levenshtein distance (cf. wrong_matches.txt)

    hard_coded_dict = {
        "Death of the Outsider": "614570",
        "Hellblade": "414340",
        "Nioh": "485510",
        "Nioh: Complete Edition": "485510",
        "Okami HD": "587620",
        "Okami": "587620",
        "PUBG": "578080",
        "Resident Evil 7": "418370",
        "Resident Evil VII Biohazard": "418370",
        "Resident Evil VII": "418370",
        "Telltale's Guardians of the Galaxy": "579950",
        "Total War: Warhammer 2": "594570",
        "Total war:warhammer 2": "594570",
        "Trails in the Sky the 3rd": "436670",
        "Turok 2": "405830",
        "Wolfenstein II": "612880",
    }

    return hard_coded_dict


def check_database_of_problematic_game_names(game_name):
    hard_coded_dict = get_hard_coded_appID_dict()

    is_a_problematic_game_name = bool(game_name in hard_coded_dict.keys())

    return is_a_problematic_game_name


def find_hard_coded_appID(game_name_input):
    hard_coded_dict = get_hard_coded_appID_dict()

    hard_coded_appID = hard_coded_dict[game_name_input]

    return hard_coded_appID


def main():
    filename = 'votes_with_ids/steam_resetera_2017_goty_votes.csv'
    file_encoding = 'ansi'

    data = load_input(filename, file_encoding)

    raw_votes = parse_votes(data)

    steamspy_database = getTodaysSteamSpyData()
    num_closest_neighbors = 3

    matches = precompute_matches(raw_votes, steamspy_database, num_closest_neighbors)

    display_matches(matches)

    normalized_votes = normalize_votes(raw_votes, matches)

    # TODO apply https://github.com/bradbeattie/python-vote-core

    return


if __name__ == '__main__':
    main()
