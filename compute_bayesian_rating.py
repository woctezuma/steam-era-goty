# Objective: choose a prior and compute a Bayesian rating

import matplotlib.pyplot as plt
import numpy as np


def choose_prior(observations: dict[str, dict], *, verbose: bool = False) -> dict:
    prior = {}

    scores = [
        game["score"] for game in observations.values() if game["score"] is not None
    ]
    votes = [
        game["num_votes"]
        for game in observations.values()
        if game["num_votes"] is not None
    ]

    # Data visualization to help choose a good prior
    if verbose:
        score_max = np.max(scores)
        vote_max = np.max(votes)

        print("Highest average score:")
        print(
            [
                game_name
                for game_name in observations
                if observations[game_name]["score"] >= score_max
            ],
        )

        print("Highest number of votes:")
        print(
            [
                game_name
                for game_name in observations
                if observations[game_name]["num_votes"] >= vote_max
            ],
        )

        plt.figure()
        plt.scatter(scores, votes)
        plt.xlabel("Average Score")
        plt.ylabel("Number of votes")
        plt.show()

    # TODO: Important choices below. How do you choose a good prior? Median? Average?
    prior["score"] = np.average(scores)
    prior["num_votes"] = np.median(votes)

    return prior


def compute_bayesian_score(game: dict, prior: dict) -> float:
    return (prior["num_votes"] * prior["score"] + game["num_votes"] * game["score"]) / (
        prior["num_votes"] + game["num_votes"]
    )


def main() -> bool:
    prior = {}
    prior["score"] = 0.7
    prior["num_votes"] = pow(10, 3)

    # Loop over the number of reviews
    for num_reviews in [pow(10, n) for n in range(5)]:
        # Display the Bayesian rating of a game with as many positive and negative reviews
        game = {}
        game["score"] = 0.5
        game["num_votes"] = num_reviews

        bayesian_rating = compute_bayesian_score(game, prior)
        print(
            "#reviews = "
            + str(num_reviews)
            + "\tBayesian rating = "
            + str(bayesian_rating),
        )

    return True


if __name__ == "__main__":
    main()
