import re
from pathlib import Path

from compute_bayesian_rating import choose_prior, compute_bayesian_score

EXPECTED_LIST_LENGTH: int = 2


def load_input(filename: str, file_encoding: str = "utf8") -> list[str]:
    data = []

    with Path(filename).open(encoding=file_encoding) as f:
        for raw_line in f:
            line = raw_line.strip()
            # Remove empty lines and comments
            if line and line[0:2] != "# ":
                data.append(line)

    return data


def parse_data(data: list[str]) -> dict[str, dict]:
    observations: dict[str, dict] = {}

    for element in data:
        my_list = element.rsplit("(")
        if not (len(my_list) == EXPECTED_LIST_LENGTH):
            raise AssertionError

        # Split at '|' to have the rank of the game at the head of the list
        first_part = my_list[0].split("|")
        # Remove the rank of the game
        game_name_list = first_part[1:]
        # Concatenate the remaining elements with '|'
        game_name = "|".join(game_name_list)  # Remove leading and trailing whitespaces
        game_name = game_name.strip()

        second_part = my_list[1]
        # Reference: https://stackoverflow.com/a/1059601
        tokens = re.split(r"\W+", second_part)
        rating_sum = int(tokens[1 + tokens.index("Score")])
        num_votes = int(tokens[1 + tokens.index("Votes")])

        observations[game_name] = {}
        observations[game_name]["score"] = rating_sum / num_votes
        observations[game_name]["num_votes"] = num_votes

    return observations


def compute_ranking(observations: dict[str, dict], prior: dict) -> list[str]:
    for game_name, game in observations.items():
        observations[game_name]["bayesian_score"] = compute_bayesian_score(game, prior)

    return sorted(
        observations.keys(),
        key=lambda x: observations[x]["bayesian_score"],
        reverse=True,
    )


def print_ranking(
    ranking: list[str],
    observations: dict[str, dict],
    prior: dict,
) -> None:
    print("Game of the Year Votes\n")

    for rank, entry in enumerate(ranking):
        game_name = entry.strip()
        sum_scores = (
            observations[game_name]["score"] * observations[game_name]["num_votes"]
        )
        votes = observations[game_name]["num_votes"]
        aps = observations[game_name]["score"]
        bayesian_score = observations[game_name]["bayesian_score"]

        sentence = "{0:3} | {1} (Score: {2:.0f} | Votes: {3} | APS: {4:.2f} | Bayesian Rating: {5:.2f})"
        print(
            sentence.format(
                rank + 1,
                game_name,
                sum_scores,
                votes,
                aps,
                bayesian_score,
            ),
        )

    sentence = "\nNB: Bayesian Prior (Score: {0:.2f} | Votes: {1:.2f})"
    print(sentence.format(prior["score"], prior["num_votes"]))


def main() -> bool:
    filename = "data/steam_resetera_2017_goty.txt"

    data = load_input(filename)

    observations = parse_data(data)

    verbose = False
    prior = choose_prior(observations, verbose=verbose)

    ranking = compute_ranking(observations, prior)

    print_ranking(ranking, observations, prior)

    return True


if __name__ == "__main__":
    main()
