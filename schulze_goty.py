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
            list_without_punctuation = re.split('\W+', raw_name)
            name_without_punctuation = ' '.join(list_without_punctuation).strip()

            votes[voter_name][position] = name_without_punctuation

    return votes


def main():
    filename = 'votes_with_ids/steam_resetera_2017_goty_votes.csv'
    file_encoding = 'ansi'

    data = load_input(filename, file_encoding)

    votes = parse_votes(data)

    print(votes)

    # TODO check game names for typos

    # TODO apply https://github.com/bradbeattie/python-vote-core

    return


if __name__ == '__main__':
    main()
