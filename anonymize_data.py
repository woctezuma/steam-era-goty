import pathlib
import re
from pathlib import Path

from bayesian_goty import load_input
from faker import Faker


def anonymize(data, author_name_token_index=0):
    fake = Faker("fr_FR")

    anonymized_data = []

    for element in data:
        tokens = re.split(r"(;)", element)
        tokens[author_name_token_index] = fake.name()

        line = "".join(tokens)

        anonymized_data.append(line)

    return anonymized_data


def write_output(anonymized_data, output_filename, file_encoding) -> None:
    data_path = pathlib.Path(output_filename).parent

    pathlib.Path(data_path).mkdir(parents=True, exist_ok=True)

    with Path(output_filename).open("w", encoding=file_encoding) as outfile:
        for element in anonymized_data:
            print(element, file=outfile)


def main() -> None:
    input_filename = "data/votes_with_ids/steam_resetera_2017_goty_votes.csv"
    output_filename = "data/anonymized_votes/steam_resetera_2017_goty_votes.csv"
    file_encoding = "cp1252"

    data = load_input(input_filename, file_encoding)

    # Assumption: the name of the author appears as the first token on each line of data
    author_name_token_index = 0

    anonymized_data = anonymize(data, author_name_token_index)

    write_output(anonymized_data, output_filename, file_encoding)


if __name__ == "__main__":
    main()
