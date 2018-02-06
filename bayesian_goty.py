import re

import matplotlib.pyplot as plt
import numpy as np


def load_input(filename, file_encoding='utf8'):
    data = []

    with open(filename, 'r', encoding=file_encoding) as f:
        for line in f.readlines():
            line = line.strip()
            # Remove empty lines and comments
            if len(line) > 0 and line[0:2] != '# ':
                data.append(line)

    return data


def parse_data(data):
    observations = dict()

    for element in data:
        my_list = element.rsplit('(')
        assert (len(my_list) == 2)

        # Split at '|' to have the rank of the game at the head of the list
        first_part = my_list[0].split('|')
        # Remove the rank of the game
        game_name_list = first_part[1:]
        # Concatenate the remaining elements with '|'
        game_name = '|'.join(game_name_list) \
            # Remove leading and trailing whitespaces
        game_name = game_name.strip()

        second_part = my_list[1]
        # Reference: https://stackoverflow.com/a/1059601
        tokens = re.split('\W+', second_part)
        rating_sum = int(tokens[1 + tokens.index('Score')])
        num_votes = int(tokens[1 + tokens.index('Votes')])

        observations[game_name] = dict()
        observations[game_name]['score'] = rating_sum / num_votes
        observations[game_name]['num_votes'] = num_votes

    return observations


def choose_prior(observations, verbose=False):
    prior = dict()

    scores = [game['score'] for game in observations.values()]
    votes = [game['num_votes'] for game in observations.values()]

    # Data visualization to help choose a good prior
    if verbose:
        score_max = np.max(scores)
        vote_max = np.max(votes)

        print('Highest average score:')
        print([game_name for game_name in observations.keys() if observations[game_name]['score'] >= score_max])

        print('Highest number of votes:')
        print([game_name for game_name in observations.keys() if observations[game_name]['num_votes'] >= vote_max])

        plt.figure()
        plt.scatter(scores, votes)
        plt.xlabel('Average Score')
        plt.ylabel('Number of votes')
        plt.show()

    # TODO: Important choices below. How do you choose a good prior? Median? Average?
    prior['score'] = np.median(scores)
    prior['num_votes'] = np.average(votes)

    return prior


def compute_bayesian_score(game, prior):
    bayesian_score = (prior['num_votes'] * prior['score'] + game['num_votes'] * game['score']) \
                     / (prior['num_votes'] + game['num_votes'])

    return bayesian_score


def compute_ranking(observations, prior):
    for game_name, game in observations.items():
        observations[game_name]['bayesian_score'] = compute_bayesian_score(game, prior)

    ranking = sorted(observations.keys(), key=lambda x: observations[x]['bayesian_score'], reverse=True)

    return ranking


def print_ranking(ranking, observations, prior):
    print('Game of the Year Votes\n')

    for rank, entry in enumerate(ranking):
        game_name = entry.strip()
        sum_scores = observations[game_name]['score'] * observations[game_name]['num_votes']
        votes = observations[game_name]['num_votes']
        aps = observations[game_name]['score']
        bayesian_score = observations[game_name]['bayesian_score']

        sentence = '{0:3} | {1} (Score: {2:.0f} | Votes: {3} | APS: {4:.2f} | Bayesian Rating: {5:.2f})'
        print(sentence.format(rank + 1, game_name, sum_scores, votes, aps, bayesian_score))

    sentence = '\nNB: Bayesian Prior (Score: {0:.2f} | Votes: {1:.2f})'
    print(sentence.format(prior['score'], prior['num_votes']))

    return


def main():
    filename = 'data/steam_resetera_2017_goty.txt'

    data = load_input(filename)

    observations = parse_data(data)

    verbose = False
    prior = choose_prior(observations, verbose)

    ranking = compute_ranking(observations, prior)

    print_ranking(ranking, observations, prior)


if __name__ == '__main__':
    main()
