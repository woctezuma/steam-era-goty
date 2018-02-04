import re

from bayesian_goty import load_input


def parse_votes(data, num_games_per_voter=5):
    votes = dict()

    for element in data:
        tokens = re.split('(;)', element)

        voter_name = tokens[0]
        voted_games = [tokens[2 * (i + 1)] for i in range(num_games_per_voter)]

        votes[voter_name] = dict()
        for i in range(len(voted_games)):
            position = num_games_per_voter - i

            raw_name = voted_games[i]

            # Remove punctuation
            list_without_punctuation = re.split('\W+', raw_name)
            # Remove small words
            word_limit = 3
            filtered_list = [word.strip() for word in list_without_punctuation if len(word) > word_limit]
            name_without_punctuation = ' '.join(filtered_list).strip()

            # Lower case
            formatted_name = name_without_punctuation.lower()

            formatted_name = fix_typos(formatted_name)

            votes[voter_name][position] = formatted_name.strip()

    return votes


def fix_typos(game_name):
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


def list_all_game_names(votes):
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
        votes.pop(voter)

    return votes


def main():
    filename = 'votes_with_ids/steam_resetera_2017_goty_votes.csv'
    file_encoding = 'ansi'

    data = load_input(filename, file_encoding)

    votes = parse_votes(data)

    # To check game names for typos or duplicates. If a problem is detected, then you have to edit fix_typos()
    game_names = list_all_game_names(votes)

    votes = remove_invalid_voters(votes)

    # TODO apply https://github.com/bradbeattie/python-vote-core

    return


if __name__ == '__main__':
    main()
