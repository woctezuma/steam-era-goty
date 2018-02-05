def load_votes(data, num_games_per_voter=5):
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


def parse_votes(raw_votes, steamspy_database):
    parsed_votes = dict()

    for voter_name in raw_votes.keys():
        parsed_votes[voter_name] = dict()
        for (position, game_name) in raw_votes[voter_name].items():

            if game_name != '':
                inferred_appID = find_closest_appID(game_name, steamspy_database)

                parsed_votes[voter_name][position] = inferred_appID
            else:
                parsed_votes[voter_name][position] = None

    return parsed_votes


def find_closest_appID(game_name_input, steamspy_database):
    from Levenshtein import distance

    dist = dict()

    for appID in steamspy_database.keys():
        str = steamspy_database[appID]['name']
        dist[appID] = distance(game_name_input, str)

    sorted_appIDS = sorted(dist.keys(), key=lambda x: dist[x])

    closest_appID = int(sorted_appIDS[0])

    return closest_appID


def check_game_name_matching(raw_votes, parsed_votes, steamspy_database):
    for voter in parsed_votes.keys():
        for (position, appID_int) in parsed_votes[voter].items():
            if appID_int is not None:
                appID = str(appID_int)
                print('appID:' + appID + '\t' + steamspy_database[appID]['name'] + '\t' + raw_votes[voter][position])

    return


def main():
    filename = 'votes_with_ids/steam_resetera_2017_goty_votes.csv'
    file_encoding = 'ansi'

    from download_json import getTodaysSteamSpyData

    steamspy_database = getTodaysSteamSpyData()

    from bayesian_goty import load_input

    data = load_input(filename, file_encoding)

    raw_votes = load_votes(data)

    parsed_votes = parse_votes(raw_votes, steamspy_database)

    check_game_name_matching(raw_votes, parsed_votes, steamspy_database)

    # TODO apply https://github.com/bradbeattie/python-vote-core

    return


if __name__ == '__main__':
    main()
