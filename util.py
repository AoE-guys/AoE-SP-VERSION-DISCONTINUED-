import os
from typing import Callable, Dict, List, Tuple


def read_mod_file(file_name: str) -> Dict[str, str]:
    """Read a .mod file and return the data as a dictionary."""

    file_data = {}
    with open(file_name, "r") as file:
        lines = file.readlines()
        for line in lines:
            split = line.split("=")
            trimmed = list(map(lambda s: s.strip().replace('"', ""), split))
            file_data[trimmed[0]] = trimmed[1]

    return file_data


def find_mod_directory() -> Tuple[str, str]:
    """Find the mod directory from the first seen .mod file."""

    for file_name in os.listdir("."):
        if file_name.endswith(".mod"):
            mod_file = read_mod_file(file_name)
            return (file_name, mod_file["user_dir"])

    raise FileNotFoundError("No .mod file found in directory.")


MOD_FILE, MOD_DIRECTORY = find_mod_directory()


def is_good_ext(extensions: List[str]) -> Callable[[str], bool]:
    """Provide a callback that verifies
    that the given file has an accepted file extension.
    """

    endings = ["." + s for s in extensions]

    def func(file_name: str) -> bool:
        return any([good for good in endings if file_name.endswith(good)])

    return func


def process_directory(directory: str,
                      extensions: List[str],
                      handler: Callable[[str], None]) -> None:
    """Process an entire directory recursively
    and apply a callback onto each file if
    the file extension matches what is accepted.
    """

    for dirpath, dirnames, file_names in os.walk(directory):
        for name in filter(is_good_ext(extensions), file_names):
            file_path = os.path.join(dirpath, name)
            handler(file_path)
