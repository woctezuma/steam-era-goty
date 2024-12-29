import re

import schulze
import steampi.calendar
import steampi.text_distances
import steamspypi.api
from bayesian_goty import load_input
from utils import get_release_year_for_problematic_app_id


def parse_votes(data: list[str], num_games_per_voter: int = 5) -> dict[str, dict]:
    raw_votes = {}

    for element in data:
        tokens = re.split(r"(;)", element)

        voter_name = tokens[0]
        voted_games = [tokens[2 * (i + 1)] for i in range(num_games_per_voter)]

        raw_votes[voter_name] = {}
        for i, game_name in enumerate(voted_games):
            position = num_games_per_voter - i

            raw_votes[voter_name][position] = game_name

    return raw_votes


def normalize_votes(
    raw_votes: dict[str, dict], matches: dict[str, dict]
) -> dict[str, dict]:
    # Index of the first neighbor
    neighbor_reference_index = 0

    normalized_votes = {}

    for voter_name in raw_votes:
        normalized_votes[voter_name] = {}
        normalized_votes[voter_name]["ballots"] = {}
        normalized_votes[voter_name]["distances"] = {}
        for position, game_name in raw_votes[voter_name].items():
            if game_name in matches:
                normalized_votes[voter_name]["ballots"][position] = matches[game_name][
                    "matched_appID"
                ][neighbor_reference_index]
                normalized_votes[voter_name]["distances"][position] = matches[
                    game_name
                ]["match_distance"][neighbor_reference_index]
            else:
                normalized_votes[voter_name]["ballots"][position] = None
                normalized_votes[voter_name]["distances"][position] = None

    return normalized_votes


def constrain_app_id_search_by_year(
    dist: dict[str, int],
    sorted_app_ids: list[str],
    release_year: str | None,
    max_num_tries_for_year: int,
) -> list[str]:
    filtered_sorted_app_ids = sorted_app_ids.copy()

    if release_year is not None:
        first_match = filtered_sorted_app_ids[0]
        dist_reference = dist[first_match]

        if dist_reference > 0:
            # Check release year to remove possible mismatches. For instance, with input Warhammer 2 and two choices:
            # Warhammer & Warhammer II, we would only keep the game released in the target year (2017), i.e. the sequel.
            is_the_first_match_released_in_a_wrong_year = True
            iter_count = 0
            while is_the_first_match_released_in_a_wrong_year and (
                iter_count < max_num_tries_for_year
            ):
                first_match = filtered_sorted_app_ids[0]
                try:
                    matched_release_year = steampi.calendar.get_release_year(
                        first_match,
                    )
                except ValueError:
                    matched_release_year = get_release_year_for_problematic_app_id(
                        app_id=first_match,
                    )

                is_the_first_match_released_in_a_wrong_year = bool(
                    matched_release_year != int(release_year),
                )
                if is_the_first_match_released_in_a_wrong_year:
                    filtered_sorted_app_ids.pop(0)

                iter_count += 1
            # Reset if we could not find a match released in the target year
            if is_the_first_match_released_in_a_wrong_year:
                filtered_sorted_app_ids = sorted_app_ids

    return filtered_sorted_app_ids


def apply_hard_coded_fixes_to_app_id_search(
    game_name_input: str,
    filtered_sorted_app_ids: list[str],
    num_closest_neighbors: int,
) -> list[str]:
    closest_app_id = [find_hard_coded_app_id(game_name_input)]
    if num_closest_neighbors > 1:
        closest_app_id.extend(filtered_sorted_app_ids[0 : (num_closest_neighbors - 1)])

    return closest_app_id


def find_closest_app_id(
    game_name_input: str,
    steamspy_database: dict[str, dict],
    num_closest_neighbors: int = 1,
    release_year: str | None = None,
    max_num_tries_for_year: int = 2,
) -> tuple[list[str], list[int]]:
    (sorted_app_ids, dist) = steampi.text_distances.find_most_similar_game_names(
        game_name_input,
        steamspy_database,
    )

    filtered_sorted_app_ids = sorted_app_ids

    if release_year is not None:
        filtered_sorted_app_ids = constrain_app_id_search_by_year(
            dist,
            sorted_app_ids,
            release_year,
            max_num_tries_for_year,
        )

    closest_app_id = filtered_sorted_app_ids[0:num_closest_neighbors]

    if check_database_of_problematic_game_names(game_name_input):
        closest_app_id = apply_hard_coded_fixes_to_app_id_search(
            game_name_input,
            filtered_sorted_app_ids,
            num_closest_neighbors,
        )

    closest_distance = [dist[app_id] for app_id in closest_app_id]

    return closest_app_id, closest_distance


def precompute_matches(
    raw_votes: dict[str, list[str]],
    steamspy_database: dict[str, dict],
    num_closest_neighbors: int = 1,
    release_year: str | None = None,
    max_num_tries_for_year: int = 2,
) -> dict[str, dict]:
    seen_game_names = set()
    matches = {}

    for voter in raw_votes:
        for raw_name in raw_votes[voter].values():
            if raw_name not in seen_game_names:
                seen_game_names.add(raw_name)

                if raw_name:
                    (closest_app_id, closest_distance) = find_closest_app_id(
                        raw_name,
                        steamspy_database,
                        num_closest_neighbors,
                        release_year,
                        max_num_tries_for_year,
                    )

                    element = {}
                    element["input_name"] = raw_name
                    element["matched_appID"] = closest_app_id
                    element["matched_name"] = [
                        steamspy_database[appID]["name"] for appID in closest_app_id
                    ]
                    element["match_distance"] = closest_distance

                    matches[raw_name] = element

    return matches


def display_matches(matches: dict[str, dict]) -> None:
    # Index of the neighbor used to sort keys of the matches dictionary
    neighbor_reference_index = 0

    sorted_keys = sorted(
        matches.keys(),
        key=lambda x: matches[x]["match_distance"][neighbor_reference_index]
        / (1 + len(matches[x]["input_name"])),
    )

    for game in sorted_keys:
        element = matches[game]

        dist_reference = element["match_distance"][neighbor_reference_index]
        game_name = element["input_name"]

        if dist_reference > 0 and check_database_of_problematic_game_names(game_name):
            print(
                "\n"
                + game_name
                + " ("
                + "length:"
                + str(len(game_name))
                + ")"
                + " ---> ",
                end="",
            )
            for neighbor_index in range(len(element["match_distance"])):
                dist = element["match_distance"][neighbor_index]
                print(
                    element["matched_name"][neighbor_index]
                    + " (appID: "
                    + element["matched_appID"][neighbor_index]
                    + " ; "
                    + "distance:"
                    + str(dist)
                    + ")",
                    end="\t",
                )

    print()


def get_hard_coded_app_id_dict() -> dict[str, str]:
    # Hard-coded list of game names which are wrongly matched with Levenshtein distance (cf. output/wrong_matches.txt)

    return {
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


def check_database_of_problematic_game_names(game_name: str) -> bool:
    hard_coded_dict = get_hard_coded_app_id_dict()

    return bool(game_name in hard_coded_dict)


def find_hard_coded_app_id(game_name_input: str) -> str:
    hard_coded_dict = get_hard_coded_app_id_dict()

    return hard_coded_dict[game_name_input]


def adapt_votes_format_for_schulze_computations(
    normalized_votes: dict[str, dict],
) -> tuple[list[str], list[tuple[list[str], int]]]:
    candidate_names = set()

    for voter in normalized_votes:
        current_ballots = normalized_votes[voter]["ballots"]
        for position in sorted(current_ballots.keys()):
            app_id = current_ballots[position]
            if app_id is not None:
                candidate_names.add(app_id)

    weighted_ranks = []

    for voter in normalized_votes:
        current_ballots = normalized_votes[voter]["ballots"]
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


def compute_schulze_ranking(
    normalized_votes: dict[str, dict], steamspy_database: dict[str, dict]
) -> list[str]:
    # Reference: https://github.com/mgp/schulze-method

    (candidate_names, weighted_ranks) = adapt_votes_format_for_schulze_computations(
        normalized_votes,
    )

    schulze_ranking = schulze.compute_ranks(candidate_names, weighted_ranks)

    print_schulze_ranking(schulze_ranking, steamspy_database)

    return schulze_ranking


def print_schulze_ranking(
    schulze_ranking: list[list[str]], steamspy_database: dict[str, dict]
) -> None:
    print()

    for rank, app_id_group in enumerate(schulze_ranking):

        def get_game_name(app_id: str) -> str:
            return steamspy_database[app_id]["name"]

        for app_id in sorted(app_id_group, key=get_game_name):
            game_name = get_game_name(app_id)

            app_id_release_date = steampi.calendar.get_release_date_as_str(app_id)
            if app_id_release_date is None:
                app_id_release_date = "an unknown date"

            print(
                f"{rank + 1:2} | "
                + game_name.strip()
                + " (appID: "
                + app_id
                + ", released on "
                + app_id_release_date
                + ")",
            )


def print_ballot_distribution_for_given_appid(
    app_id_group: list[str], normalized_votes: dict[str, dict]
) -> None:
    for app_id in app_id_group:
        ballot_distribution = None

        for voter_name in normalized_votes:
            current_ballots = normalized_votes[voter_name]["ballots"]

            if ballot_distribution is None:
                ballot_distribution = [0 for _ in range(len(current_ballots))]

            positions = sorted(current_ballots.keys())

            for index, position in enumerate(positions):
                if current_ballots[position] == app_id:
                    ballot_distribution[index] += 1

        print("\nappID:" + app_id, end="\t")
        print("counts of ballots with rank 1, 2, ..., 5:\t", ballot_distribution)


def filter_out_votes_for_wrong_release_years(
    normalized_votes: dict[str, dict], target_release_year: str
) -> dict[str, dict]:
    # Objective: remove appID which gathered votes but were not released during the target release year

    print()

    release_years = {}
    removed_app_ids = []

    for voter in normalized_votes:
        current_ballots = normalized_votes[voter]["ballots"]

        current_ballots_list = []
        for position in sorted(current_ballots.keys()):
            app_id = current_ballots[position]
            if app_id is not None:
                if app_id not in release_years:
                    try:
                        release_years[app_id] = steampi.calendar.get_release_year(
                            app_id,
                        )
                    except ValueError:
                        release_years[app_id] = get_release_year_for_problematic_app_id(
                            app_id=app_id,
                        )
                if release_years[app_id] == int(target_release_year):
                    current_ballots_list.append(app_id)
                elif app_id not in removed_app_ids:
                    print(
                        "AppID "
                        + app_id
                        + " was removed because it was released in "
                        + str(release_years[app_id]),
                    )
                    removed_app_ids.append(app_id)

        for i, current_ballot in enumerate(current_ballots_list):
            position = i + 1
            normalized_votes[voter]["ballots"][position] = current_ballot
        for i in range(len(current_ballots_list), len(current_ballots.keys())):
            position = i + 1
            normalized_votes[voter]["ballots"][position] = None

    return normalized_votes


def compute_steam_era_goty(
    ballot_year: str, ballot_filename: str | None = None
) -> None:
    release_year = str(ballot_year)

    if ballot_filename is None:
        ballot_filename = (
            "data/anonymized_votes/steam_resetera_" + release_year + "_goty_votes.csv"
        )

    file_encoding = "cp1252"  # Reference: https://stackoverflow.com/q/12468179

    data = load_input(ballot_filename, file_encoding)

    raw_votes = parse_votes(data)

    steamspy_database = steamspypi.load()
    num_closest_neighbors = 3

    # The following parameter can only have an effect if it is strictly greater than 1.
    max_num_tries_for_year = 2

    matches = precompute_matches(
        raw_votes,
        steamspy_database,
        num_closest_neighbors,
        release_year,
        max_num_tries_for_year,
    )

    display_matches(matches)

    normalized_votes = normalize_votes(raw_votes, matches)

    normalized_votes = filter_out_votes_for_wrong_release_years(
        normalized_votes,
        release_year,
    )

    schulze_ranking = compute_schulze_ranking(normalized_votes, steamspy_database)

    num_app_id_groups_to_display = 3
    for app_id_group in schulze_ranking[0:num_app_id_groups_to_display]:
        print_ballot_distribution_for_given_appid(app_id_group, normalized_votes)


def main() -> bool:
    ballot_year = "2017"

    compute_steam_era_goty(ballot_year)

    return True


if __name__ == "__main__":
    main()
