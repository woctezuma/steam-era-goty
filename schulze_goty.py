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


def normalize_votes(raw_votes, steamspy_database):
    normalized_votes = dict()

    for voter_name in raw_votes.keys():
        normalized_votes[voter_name] = dict()
        normalized_votes[voter_name]['ballots'] = dict()
        normalized_votes[voter_name]['distances'] = dict()
        for (position, game_name) in raw_votes[voter_name].items():

            if game_name != '':
                (closest_appID, closest_distance) = find_closest_appID(game_name, steamspy_database)

                normalized_votes[voter_name]['ballots'][position] = closest_appID
                normalized_votes[voter_name]['distances'][position] = closest_distance
            else:
                normalized_votes[voter_name]['ballots'][position] = None
                normalized_votes[voter_name]['distances'][position] = None

    return normalized_votes


def find_closest_appID(game_name_input, steamspy_database):
    from Levenshtein import distance

    dist = dict()

    for appID in steamspy_database.keys():
        str = steamspy_database[appID]['name']
        dist[appID] = distance(game_name_input, str)

    sorted_appIDS = sorted(dist.keys(), key=lambda x: dist[x])

    closest_appID_str = sorted_appIDS[0]

    closest_appID = int(closest_appID_str)
    closest_distance = dist[closest_appID_str]

    return (closest_appID, closest_distance)


def build_matches_for_display(raw_votes, normalized_votes, steamspy_database):
    matches = []
    for voter in normalized_votes.keys():
        for (position, appID_int) in normalized_votes[voter]['ballots'].items():
            if appID_int is not None:
                appID = str(appID_int)
                element = dict()
                element['input_name'] = raw_votes[voter][position]
                element['matched_appID'] = appID
                element['matched_name'] = steamspy_database[appID]['name']
                element['match_distance'] = normalized_votes[voter]['distances'][position]
                matches.append(element)

    return matches


def display_matches(matches):
    matches = sorted(matches, key=lambda x: x['match_distance'])

    for element in matches:
        dist = element['match_distance']
        if dist > 0:
            print(element['input_name']
                  + '-> appID:' + element['matched_appID']
                  + ' ; name: ' + element['matched_name']
                  + '(' + 'distance:' + str(dist) + ')')

    return


def main():
    filename = 'votes_with_ids/steam_resetera_2017_goty_votes.csv'
    file_encoding = 'ansi'

    from download_json import getTodaysSteamSpyData

    steamspy_database = getTodaysSteamSpyData()

    from bayesian_goty import load_input

    data = load_input(filename, file_encoding)

    raw_votes = parse_votes(data)

    normalized_votes = normalize_votes(raw_votes, steamspy_database)

    matches = build_matches_for_display(raw_votes, normalized_votes, steamspy_database)

    display_matches(matches)

    # TODO apply https://github.com/bradbeattie/python-vote-core

    return


if __name__ == '__main__':
    main()
