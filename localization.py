import collections
import csv
import os
import sys
import textwrap
from typing import Iterable, List, Tuple, TypeVar

import click

from util import MOD_DIRECTORY, process_directory

COLUMNS = ("Key", "English", "French", "German", "Polish", "Spanish", "Italian",
           "Swedish", "Czech", "Hungarian", "Dutch", "Portuguese", "Russian", "Finnish")

EXTENSIONS = ["csv"]

maxInt = sys.maxsize

while True:
    # decrease the maxInt value by factor 10 
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)

Row = List[str]
L = TypeVar("L", bound="Localization")
LG = TypeVar("LG", bound="LocalizationGroup")
Assoc = Tuple[str, Row]
AssocList = List[Assoc]


def get_name(file_path: str) -> str:
    file_name, _ = os.path.splitext(file_path)
    return os.path.basename(file_name)


class LocalizationGroup:
    """A grouping of localization files in the game."""

    def __init__(self: LG) -> None:
        """Initialize file path to localization dictionary,
        duplicates to an empty default dictionary,
        and all_removed to an empty list.
        """

        self.localizations = {}
        self.duplicates = collections.defaultdict(list)
        self.all_removed = []
        self.prompt_file = True

    def set_prompt_file(self: LG, prompt_file: bool) -> None:
        """Set the flag that enables displaying the prompt
        to open files containing duplicate entries for some key.
        """

        self.prompt_file = prompt_file

    def add(self: LG, local: L) -> None:
        """Add a localization entry to the group."""

        file_path = local.file_path
        self.localizations[file_path] = local

        for key, entry in local.entries.items():
            self.duplicates[key].append((file_path, entry))

        for key, entries in local.duplicates.items():
            for entry in entries:
                self.duplicates[key].append((file_path, entry))

    def filter(self: LG) -> None:
        """Deduplicates all registered localization files in the group."""

        self.drop_uniques()

        if len(self.duplicates) == 0:
            click.echo("No duplicates to remove found.")
            return

        items = self.duplicates.items()
        total_duplicates = sum(map(lambda tup: len(tup[1]), items))
        click.secho(f"There are {total_duplicates} duplicates to be processed." +
                    " Press <Ctrl+C> to exit and save progress at any time.",
                    fg="bright_black")

        for key, assoc in items:
            removed = self.drop_duplicates(key, assoc)
            self.all_removed.append((key, removed))

    def prompt_export(self: LG) -> None:
        """Prompt to export changed entries to their files."""

        if len(self.all_removed) == 0:
            return

        self.echo_removed()

        export_style = click.style("Do you want to save your changes?",
                                   fg="bright_green")
        if click.confirm(export_style):
            self.export()

    def export(self: LG) -> None:
        """Export all updated records to their respective files."""

        for local in self.localizations.values():
            local.export()

    def drop_uniques(self: LG) -> None:
        """Drop all entries that are designated as duplicate
        while only having one, unique occurrence.
        """

        self.duplicates = {k: v for (k, v) in self.duplicates.items()
                           if len(v) != 1}

    def echo_removed(self: LG) -> None:
        """Display all removed keys from the provided file path."""
        for removed in self.all_removed:
            key, assoc = removed
            for entry in assoc:
                file_path, _ = entry

                key_style = click.style(key, fg="bright_blue")
                file_style = click.style(
                    get_name(file_path), fg="bright_yellow")
                click.echo("Removed duplicate key " +
                           f"{key_style} from {file_style}.")

    def drop_duplicates(self: LG, key: str, assoc: AssocList) -> AssocList:
        """Drop all duplicated entries for
        the provided key and return the removed entries.
        """

        self.echo_entries(key, assoc)
        return self.prompt_deduplication(key, assoc)

    def echo_entries(self: LG, key: str, assoc: AssocList) -> None:
        """Display all found entries for the specified key."""

        click.secho(f"{len(assoc)} ", fg="bright_cyan", nl=False)
        click.secho(f"total entries found for key ", fg="white", nl=False)
        click.secho(key, fg="bright_blue", nl=False)
        click.secho(".\n", fg="white")

    def prompt_deduplication(self: LG, key: str, assoc: AssocList) -> AssocList:
        """Display a prompt to deduplicate specified entries."""

        for index, local in enumerate(assoc):
            file_path, entry = local
            entry_style = click.style(f"Entry {index + 1}", fg="bright_blue")
            file_style = click.style(get_name(file_path), fg="bright_yellow")

            entry_str = Localization.to_str(entry)
            wrapped = textwrap.wrap(entry_str,
                                    width=110,
                                    replace_whitespace=False)

            nt = "\n\t"
            local_style = click.style(nt + nt.join(wrapped), fg="white")

            click.echo(f"{entry_style} {file_style}{local_style}\n")

        self.prompt_files(assoc)

        choice_style = click.style("Which entry should be chosen?",
                                   fg="bright_red")

        choice_type = click.IntRange(1, index + 1)
        choice_suffix = click.style(": ", fg="bright_red")

        chosen_entry = click.prompt(choice_style,
                                    type=choice_type,
                                    prompt_suffix=choice_suffix)

        click.echo()

        assoc_removed = assoc[:chosen_entry - 1] + assoc[chosen_entry:]
        self.deduplicate(key, assoc[chosen_entry - 1], assoc_removed)
        return assoc_removed

    def prompt_files(self: LG, assoc: AssocList) -> None:
        """Display a prompt to open the provided files."""

        if not self.prompt_file:
            return

        file_names = set(map(lambda tup: tup[0], assoc))

        file_names_repr = ", ".join(file_names)
        ending = "this file" if len(file_names) == 1 else "these files"

        end_style = click.style(f"Do you want to open {ending}?",
                                fg="bright_green")
        if click.confirm(end_style):
            for file_name in file_names:
                click.launch(file_name)

    def deduplicate(self: LG, key: str, chosen: Assoc, assoc_removed: AssocList) -> None:
        """Drop duplicated entries and emplace the chosen entry
        over the original incase it is a duplicate.
        """

        file_path, entry = chosen
        self.localizations[file_path].entries[key] = entry

        for assoc in assoc_removed:
            file_path, entry = assoc
            local = self.localizations[file_path]
            local.drop_entry(key, entry)


# A global localization group.
localization_group = LocalizationGroup()


class Localization:
    """A model for any localization file in the game."""

    def __init__(self: L, file_path: str) -> None:
        """Initialize file path, entries, and duplicates
        with the file contents provided.
        """

        self.file_path = file_path
        self.entries = {}
        self.duplicates = collections.defaultdict(list)

        with open(file_path, "r", encoding="latin-1") as file:
            reader = csv.reader(file, delimiter=";")
            next(reader)  # drop the header

            keys = set()
            for row in reader:
                first = row[0]

                trimmed = row[:len(COLUMNS)]

                cleaned = [self.clean_junk(value) for value in trimmed]
                cleaned.extend([""] * (len(COLUMNS) - len(cleaned)))

                head, *tail = cleaned

                if first not in keys:
                    keys.add(first)
                    self.entries[head] = tail
                else:
                    self.duplicates[head].append(tail)

    def export(self: L) -> None:
        """Write a localization file over
        its csv file with updated records.
        """

        with open(self.file_path, "wb") as file:
            header = bytes(Localization.to_str(COLUMNS), "latin-1")
            file.write(header + b"\n")

            for key, entry in self.entries.items():
                output = bytes(Localization.to_str([key] + entry), "latin-1")
                file.write(output + b"\n")

    def drop_entry(self: L, key: str, entry: Row) -> None:
        """Drop a key from the model if the provided entry matches."""

        self.duplicates.pop(key, None)

        if key in self.entries and entry == self.entries[key]:
            self.entries.pop(key)

    def clean_junk(self: L, value: str) -> str:
        """Return True if a string contains only x's and comma's,
        otherwise False.
        """

        chars = set(value.lower())
        chars.discard("x")
        chars.discard(",")
        return "" if len(chars) == 0 else value

    @classmethod
    def to_str(self: L, entry: Iterable[str]) -> str:
        """Output an iterable row as a semi-colon joined string with
        an extra semi-colon at the end.
        """

        return ";".join(entry) + ";"


def clean_localization(file_path: str) -> None:
    """Registers all localization models with the global group."""

    localization = Localization(file_path)
    localization_group.add(localization)


@click.command()
@click.option("--file/--no-file",
              default=True,
              help="Prompt to open the files containing duplicates.")
def main(file):
    """Start the localization cleanup program.
    For more information, do `python localization.py --help`.
    """

    directory = os.path.join(MOD_DIRECTORY, "localisation")
    process_directory(directory, EXTENSIONS, clean_localization)

    localization_group.set_prompt_file(file)

    try:
        localization_group.filter()
    except click.Abort:
        click.echo()

    try:
        localization_group.prompt_export()
    except click.Abort:
        pass


if __name__ == "__main__":
    main()
