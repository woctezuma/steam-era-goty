from bayesian_goty import load_input
from download_json import getTodaysSteamSpyData
from steamspy_utils import compute_all_name_distances, get_release_date_as_str, get_release_year


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


def constrain_appID_search_by_year(dist, sorted_appIDS, release_year, max_num_tries_for_year):
    filtered_sorted_appIDS = sorted_appIDS.copy()

    if release_year is not None:
        first_match = filtered_sorted_appIDS[0]
        dist_reference = dist[first_match]

        if dist_reference > 0:
            # Check release year to remove possible mismatches. For instance, with input Warhammer 2 and two choices:
            # Warhammer & Warhammer II, we would only keep the game released in the target year (2017), which is the sequel.
            is_the_first_match_released_in_a_wrong_year = True
            iter_count = 0
            while is_the_first_match_released_in_a_wrong_year and (iter_count < max_num_tries_for_year):
                first_match = filtered_sorted_appIDS[0]
                matched_release_year = get_release_year(first_match)

                is_the_first_match_released_in_a_wrong_year = bool(matched_release_year != int(release_year))
                if is_the_first_match_released_in_a_wrong_year:
                    filtered_sorted_appIDS.pop(0)

                iter_count += 1
            # Reset if we could not find a match released in the target year
            if is_the_first_match_released_in_a_wrong_year:
                filtered_sorted_appIDS = sorted_appIDS

    return filtered_sorted_appIDS


def apply_hard_coded_fixes_to_appID_search(game_name_input, filtered_sorted_appIDS, num_closest_neighbors):
    closest_appID = [find_hard_coded_appID(game_name_input)]
    if num_closest_neighbors > 1:
        closest_appID.extend(filtered_sorted_appIDS[0:(num_closest_neighbors - 1)])

    return closest_appID


def find_closest_appID(game_name_input, steamspy_database, num_closest_neighbors=1,
                       release_year=None, max_num_tries_for_year=2):
    (dist, sorted_appIDS) = compute_all_name_distances(game_name_input, steamspy_database)

    filtered_sorted_appIDS = sorted_appIDS

    if release_year is not None:
        filtered_sorted_appIDS = constrain_appID_search_by_year(dist, sorted_appIDS, release_year,
                                                                max_num_tries_for_year)

    closest_appID = filtered_sorted_appIDS[0:num_closest_neighbors]

    if check_database_of_problematic_game_names(game_name_input):
        closest_appID = apply_hard_coded_fixes_to_appID_search(game_name_input, filtered_sorted_appIDS,
                                                               num_closest_neighbors)

    closest_distance = [dist[appID] for appID in closest_appID]

    return (closest_appID, closest_distance)


def precompute_matches(raw_votes, steamspy_database, num_closest_neighbors=1,
                       release_year=None, max_num_tries_for_year=2):
    seen_game_names = set()
    matches = dict()

    for voter in raw_votes.keys():
        for (position, raw_name) in raw_votes[voter].items():
            if raw_name not in seen_game_names:
                seen_game_names.add(raw_name)

                if raw_name != '':
                    (closest_appID, closest_distance) = find_closest_appID(raw_name, steamspy_database,
                                                                           num_closest_neighbors,
                                                                           release_year, max_num_tries_for_year)

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

    print()

    return


def get_hard_coded_appID_dict():
    # Hard-coded list of game names which are wrongly matched with Levenshtein distance (cf. output/wrong_matches.txt)

    hard_coded_dict = {
        "Death of the Outsider": "614570",
        "Hellblade": "414340",
        "Nioh": "485510",
        "Nioh: Complete Edition": "485510",
        # "Okami HD": "587620",
        "Okami": "587620",
        "PUBG": "578080",
        "Resident Evil 7": "418370",
        "Resident Evil VII Biohazard": "418370",
        "Resident Evil VII": "418370",
        "Telltale's Guardians of the Galaxy": "579950",
        # "Total War: Warhammer 2": "594570",
        # "Total war:warhammer 2": "594570",
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


def adapt_votes_format_for_schulze_computations(normalized_votes):
    candidate_names = set()

    for voter in normalized_votes.keys():
        current_ballots = normalized_votes[voter]['ballots']
        for position in sorted(current_ballots.keys()):
            appID = current_ballots[position]
            if appID is not None:
                candidate_names.add(appID)

    weighted_ranks = []

    for voter in normalized_votes.keys():
        current_ballots = normalized_votes[voter]['ballots']
        current_ranking = []
        currently_seen_candidates = set()
        for position in sorted(current_ballots.keys()):
            appID = current_ballots[position]
            if appID is not None:
                current_ranking.append([appID])
                currently_seen_candidates.add(appID)

        remaining_appIDs = candidate_names.difference(currently_seen_candidates)
        current_ranking.append(remaining_appIDs)

        current_weight = 1
        weighted_ranks.append((current_ranking, current_weight))

    candidate_names = list(candidate_names)

    return (candidate_names, weighted_ranks)


def compute_schulze_ranking(normalized_votes, steamspy_database):
    # Reference: https://github.com/mgp/schulze-method

    import schulze

    (candidate_names, weighted_ranks) = adapt_votes_format_for_schulze_computations(normalized_votes)

    schulze_ranking = schulze.compute_ranks(candidate_names, weighted_ranks)

    print_schulze_ranking(schulze_ranking, steamspy_database)

    return schulze_ranking


def print_schulze_ranking(schulze_ranking, steamspy_database):
    print()

    for (rank, appID_group) in enumerate(schulze_ranking):
        for appID in appID_group:
            game_name = steamspy_database[appID]['name']

            appID_release_date = get_release_date_as_str(appID)
            if appID_release_date is None:
                appID_release_date = 'an unknown date'

            print('{0:2} | '.format(rank + 1)
                  + game_name.strip()
                  + ' (appID: ' + appID
                  + ', released on ' + appID_release_date + ')'
                  )

    return


def print_ballot_distribution_for_given_appid(appID_group, normalized_votes):
    for appID in appID_group:

        ballot_distribution = None

        for voter_name in normalized_votes.keys():
            current_ballots = normalized_votes[voter_name]['ballots']

            if ballot_distribution is None:
                ballot_distribution = [0 for position in range(len(current_ballots))]

            positions = sorted(current_ballots.keys())

            for index in range(len(ballot_distribution)):
                if current_ballots[positions[index]] == appID:
                    ballot_distribution[index] += 1

        print('\nappID:' + appID, end='\t')
        print('counts of ballots with rank 1, 2, ..., 5:\t', ballot_distribution)

    return


def filter_out_votes_for_wrong_release_years(normalized_votes, target_release_year):
    # Objecive: remove appID which gathered votes but were not released during the target release year

    print()

    release_years = dict()
    removed_appIDs = []

    for voter in normalized_votes.keys():
        current_ballots = normalized_votes[voter]['ballots']

        current_ballots_list = []
        for position in sorted(current_ballots.keys()):
            appID = current_ballots[position]
            if appID is not None:
                if appID not in release_years.keys():
                    release_years[appID] = get_release_year(appID)
                if release_years[appID] == int(target_release_year):
                    current_ballots_list.append(appID)
                else:
                    if appID not in removed_appIDs:
                        print('AppID ' + appID + ' was removed because it was released in ' + str(release_years[appID]))
                        removed_appIDs.append(appID)

        for i in range(len(current_ballots_list)):
            position = i + 1
            normalized_votes[voter]['ballots'][position] = current_ballots_list[i]
        for i in range(len(current_ballots_list), len(current_ballots.keys())):
            position = i + 1
            normalized_votes[voter]['ballots'][position] = None

    return normalized_votes


def main():
    filename = 'data/anonymized_votes/steam_resetera_2017_goty_votes.csv'
    file_encoding = 'ansi'

    data = load_input(filename, file_encoding)

    raw_votes = parse_votes(data)

    steamspy_database = getTodaysSteamSpyData()
    num_closest_neighbors = 3

    release_year = '2017'
    # The following parameter can only have an effect if it is strictly greater than 1.
    max_num_tries_for_year = 2

    matches = precompute_matches(raw_votes, steamspy_database, num_closest_neighbors,
                                 release_year, max_num_tries_for_year)

    display_matches(matches)

    normalized_votes = normalize_votes(raw_votes, matches)

    normalized_votes = filter_out_votes_for_wrong_release_years(normalized_votes, release_year)

    schulze_ranking = compute_schulze_ranking(normalized_votes, steamspy_database)

    num_appID_groups_to_display = 3
    for appID_group in schulze_ranking[0:num_appID_groups_to_display]:
        print_ballot_distribution_for_given_appid(appID_group, normalized_votes)

    return


if __name__ == '__main__':
    main()
