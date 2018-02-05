import re

from bayesian_goty import load_input
from download_json import getTodaysSteamSpyData


def load_votes(data, num_games_per_voter=5):
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


def parse_votes(raw_votes):
    steamspy_database = getTodaysSteamSpyData()

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


def format_game_name(raw_name, word_limit=3):
    # Remove punctuation
    list_without_punctuation = re.split('\W+', raw_name)
    # Remove small words
    filtered_list = [word.strip() for word in list_without_punctuation if len(word) > word_limit]
    name_without_punctuation = ' '.join(filtered_list).strip()

    # Lower case
    formatted_name = name_without_punctuation.lower()

    # Manual fixes of typos
    formatted_name = manually_fix_typos(formatted_name)

    # Final strip
    formatted_name = formatted_name.strip()

    return formatted_name


def manually_fix_typos(game_name):
    # Objective: fix common typos

    game_name = game_name.replace('ii', '2')
    game_name = game_name.replace('orginal', 'original')
    game_name = game_name.replace('collossus', 'colossus')
    game_name = game_name.replace('eith', 'edith')
    game_name = game_name.replace('nemunera', 'numenera')
    game_name = game_name.replace('assassins', 'assassin')
    game_name = game_name.replace('the new colossus', '')
    game_name = game_name.replace('senua sacrifice', '')
    game_name = game_name.replace('bride moon', '')
    game_name = game_name.replace('complete edition', '')
    game_name = game_name.replace('playerunkown', 'playerunknown')
    game_name = game_name.replace('player unknown', 'playerunknown')
    game_name = game_name.replace('pubg', 'playerunknown battlegrounds')
    game_name = game_name.replace('biohazard', '')
    game_name = game_name.replace('resident evil   resident evil', 'resident evil')

    if game_name == 'trails' or game_name == 'legend heroes trails':
        game_name = 'legend heroes trails in the sky'

    return game_name


def list_all_game_names_for_check(votes):
    # To manually check game names for typos or duplicates. If a problem is detected, then you have to edit manually_fix_typos()

    game_names = set()

    for vote_per_voter in votes.values():
        for position_per_vote in vote_per_voter.values():
            game_names.add(position_per_vote)

    game_names = sorted(game_names)

    return game_names


def remove_invalid_voters(votes):
    invalid_voters = set()

    for voter in votes.keys():
        positions_per_vote = list(votes[voter].values())
        for position_per_vote in positions_per_vote:
            if position_per_vote != '' and len(
                    [game_name for game_name in positions_per_vote if game_name == position_per_vote]) > 1:
                invalid_voters.add(voter)
                print(voter)
                break

    for voter in invalid_voters:
        print('Voter ' + voter + ' has casted an invalid ballot.')
        votes.pop(voter)

    return votes


def find_closest_appID(game_name_input, steamspy_database):
    from Levenshtein import distance

    dist = dict()

    for appID in steamspy_database.keys():
        str = steamspy_database[appID]['name']
        dist[appID] = distance(game_name_input, str)

    sorted_appIDS = sorted(dist.keys(), key=lambda x: dist[x])

    closest_appID = int(sorted_appIDS[0])

    return closest_appID


def check_string_matching(parsed_votes, raw_votes):
    steamspy_database = getTodaysSteamSpyData()

    for voter in parsed_votes.keys():
        for (position, appID_int) in parsed_votes[voter].items():
            if appID_int is not None:
                appID = str(appID_int)
                print('appID:' + appID + '\t' + steamspy_database[appID]['name'] + '\t' + raw_votes[voter][position])

    return


def main():
    filename = 'votes_with_ids/steam_resetera_2017_goty_votes.csv'
    file_encoding = 'ansi'

    data = load_input(filename, file_encoding)

    raw_votes = load_votes(data)

    parsed_votes = parse_votes(raw_votes)

    check_string_matching(parsed_votes, raw_votes)

    # TODO apply https://github.com/bradbeattie/python-vote-core

    return


if __name__ == '__main__':
    main()
