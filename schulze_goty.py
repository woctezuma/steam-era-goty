import steampi.calendar
import steampi.text_distances
import steamspypi.api

from bayesian_goty import load_input


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


def constrain_app_id_search_by_year(dist, sorted_app_ids, release_year, max_num_tries_for_year):
    filtered_sorted_app_ids = sorted_app_ids.copy()

    if release_year is not None:
        first_match = filtered_sorted_app_ids[0]
        dist_reference = dist[first_match]

        if dist_reference > 0:
            # Check release year to remove possible mismatches. For instance, with input Warhammer 2 and two choices:
            # Warhammer & Warhammer II, we would only keep the game released in the target year (2017), i.e. the sequel.
            is_the_first_match_released_in_a_wrong_year = True
            iter_count = 0
            while is_the_first_match_released_in_a_wrong_year and (iter_count < max_num_tries_for_year):
                first_match = filtered_sorted_app_ids[0]
                matched_release_year = steampi.calendar.get_release_year(first_match)

                is_the_first_match_released_in_a_wrong_year = bool(matched_release_year != int(release_year))
                if is_the_first_match_released_in_a_wrong_year:
                    filtered_sorted_app_ids.pop(0)

                iter_count += 1
            # Reset if we could not find a match released in the target year
            if is_the_first_match_released_in_a_wrong_year:
                filtered_sorted_app_ids = sorted_app_ids

    return filtered_sorted_app_ids


def apply_hard_coded_fixes_to_app_id_search(game_name_input, filtered_sorted_app_ids, num_closest_neighbors):
    closest_app_id = [find_hard_coded_app_id(game_name_input)]
    if num_closest_neighbors > 1:
        closest_app_id.extend(filtered_sorted_app_ids[0:(num_closest_neighbors - 1)])

    return closest_app_id


def find_closest_app_id(game_name_input, steamspy_database, num_closest_neighbors=1,
                        release_year=None, max_num_tries_for_year=2):
    (sorted_app_ids, dist) = steampi.text_distances.find_most_similar_game_names(game_name_input, steamspy_database)

    filtered_sorted_app_ids = sorted_app_ids

    if release_year is not None:
        filtered_sorted_app_ids = constrain_app_id_search_by_year(dist, sorted_app_ids, release_year,
                                                                  max_num_tries_for_year)

    closest_app_id = filtered_sorted_app_ids[0:num_closest_neighbors]

    if check_database_of_problematic_game_names(game_name_input):
        closest_app_id = apply_hard_coded_fixes_to_app_id_search(game_name_input, filtered_sorted_app_ids,
                                                                 num_closest_neighbors)

    closest_distance = [dist[app_id] for app_id in closest_app_id]

    return closest_app_id, closest_distance


def precompute_matches(raw_votes, steamspy_database, num_closest_neighbors=1,
                       release_year=None, max_num_tries_for_year=2):
    seen_game_names = set()
    matches = dict()

    for voter in raw_votes.keys():
        for (position, raw_name) in raw_votes[voter].items():
            if raw_name not in seen_game_names:
                seen_game_names.add(raw_name)

                if raw_name != '':
                    (closest_appID, closest_distance) = find_closest_app_id(raw_name, steamspy_database,
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


def get_hard_coded_app_id_dict():
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
    hard_coded_dict = get_hard_coded_app_id_dict()

    is_a_problematic_game_name = bool(game_name in hard_coded_dict.keys())

    return is_a_problematic_game_name


def find_hard_coded_app_id(game_name_input):
    hard_coded_dict = get_hard_coded_app_id_dict()

    hard_coded_app_id = hard_coded_dict[game_name_input]

    return hard_coded_app_id


def adapt_votes_format_for_schulze_computations(normalized_votes):
    candidate_names = set()

    for voter in normalized_votes.keys():
        current_ballots = normalized_votes[voter]['ballots']
        for position in sorted(current_ballots.keys()):
            app_id = current_ballots[position]
            if app_id is not None:
                candidate_names.add(app_id)

    weighted_ranks = []

    for voter in normalized_votes.keys():
        current_ballots = normalized_votes[voter]['ballots']
        current_ranking = []
        currently_seen_candidates = set()
        for position in sorted(current_ballots.keys()):
            app_id = current_ballots[position]
            if app_id is not None:
                current_ranking.append([app_id])
                currently_seen_candidates.add(app_id)

        remaining_app_ids = candidate_names.difference(currently_seen_candidates)
        current_ranking.append(remaining_app_ids)

        current_weight = 1
        weighted_ranks.append((current_ranking, current_weight))

    candidate_names = list(candidate_names)

    return candidate_names, weighted_ranks


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

        def get_game_name(app_id):
            return steamspy_database[app_id]['name']

        for appID in sorted(appID_group, key=get_game_name):
            game_name = get_game_name(appID)

            app_id_release_date = steampi.calendar.get_release_date_as_str(appID)
            if app_id_release_date is None:
                app_id_release_date = 'an unknown date'

            print('{0:2} | '.format(rank + 1)
                  + game_name.strip()
                  + ' (appID: ' + appID
                  + ', released on ' + app_id_release_date + ')'
                  )

    return


def print_ballot_distribution_for_given_appid(app_id_group, normalized_votes):
    for appID in app_id_group:

        ballot_distribution = None

        for voter_name in normalized_votes.keys():
            current_ballots = normalized_votes[voter_name]['ballots']

            if ballot_distribution is None:
                ballot_distribution = [0 for _ in range(len(current_ballots))]

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
    removed_app_ids = []

    for voter in normalized_votes.keys():
        current_ballots = normalized_votes[voter]['ballots']

        current_ballots_list = []
        for position in sorted(current_ballots.keys()):
            app_id = current_ballots[position]
            if app_id is not None:
                if app_id not in release_years.keys():
                    release_years[app_id] = steampi.calendar.get_release_year(app_id)
                if release_years[app_id] == int(target_release_year):
                    current_ballots_list.append(app_id)
                else:
                    if app_id not in removed_app_ids:
                        print('AppID ' + app_id + ' was removed because it was released in '
                              + str(release_years[app_id]))
                        removed_app_ids.append(app_id)

        for i in range(len(current_ballots_list)):
            position = i + 1
            normalized_votes[voter]['ballots'][position] = current_ballots_list[i]
        for i in range(len(current_ballots_list), len(current_ballots.keys())):
            position = i + 1
            normalized_votes[voter]['ballots'][position] = None

    return normalized_votes


def compute_steam_era_goty(ballot_year, ballot_filename=None):
    release_year = str(ballot_year)

    if ballot_filename is None:
        ballot_filename = 'data/anonymized_votes/steam_resetera_' + release_year + '_goty_votes.csv'

    file_encoding = 'cp1252'  # Reference: https://stackoverflow.com/q/12468179

    data = load_input(ballot_filename, file_encoding)

    raw_votes = parse_votes(data)

    steamspy_database = steamspypi.api.load()
    num_closest_neighbors = 3

    # The following parameter can only have an effect if it is strictly greater than 1.
    max_num_tries_for_year = 2

    matches = precompute_matches(raw_votes, steamspy_database, num_closest_neighbors,
                                 release_year, max_num_tries_for_year)

    display_matches(matches)

    normalized_votes = normalize_votes(raw_votes, matches)

    normalized_votes = filter_out_votes_for_wrong_release_years(normalized_votes, release_year)

    schulze_ranking = compute_schulze_ranking(normalized_votes, steamspy_database)

    num_app_id_groups_to_display = 3
    for appID_group in schulze_ranking[0:num_app_id_groups_to_display]:
        print_ballot_distribution_for_given_appid(appID_group, normalized_votes)


def main():
    ballot_year = '2017'

    compute_steam_era_goty(ballot_year)

    return True


if __name__ == '__main__':
    main()
