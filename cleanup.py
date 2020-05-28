from typing import List

from util import MOD_DIRECTORY, process_directory

EXTENSIONS = ["txt", "lua", "map", "csv"]


def clean_line(line: str) -> str:
    """Clean a line by replacing tabs with four spaces
    and using Unix line endings solely.
    """

    return line.replace(b"\t", b"    ").rstrip() + b"\n"


def clean_file(file_path: str) -> None:
    """Clean the entire file by replacing tabs with spaces,
    replacing Windows line endings with Unix line endings,
    and removing trailing whitespace. We also adjust the file
    such that it follows style rules.
    """

    file_changed = False
    with open(file_path, "r+b") as file:
        lines = file.readlines()
        for index, line in enumerate(lines):
            cleaned = clean_line(line)
            if cleaned.isspace():
                cleaned = b"\n"

            if cleaned != line:
                file_changed = True

            lines[index] = cleaned

        style_changed = clean_style(lines)

        if style_changed:
            file_changed = True

        # wipe the file and rewrite
        file.seek(0)
        file.truncate()
        file.writelines(lines)

    if file_changed:
        print(f"Cleaned {file_path}")


def clean_style(lines: List[str]) -> bool:
    """Adjust the file information to be stylistically cleaner.
    This leaves no newlines at the start of the file and only one
    at the end of the file.
    """

    style_changed = False

    # remove any extra newlines at the start of the file
    while lines and lines[0].isspace():
        del lines[0]
        style_changed = True

    # remove any extra newlines at the end of the file.
    while lines and lines[-1].isspace():
        del lines[-1]
        style_changed = True

    # add a newline to the end of the file if not exists.
    if lines and not lines[-1].endswith(b"\n"):
        lines[-1] += "\n"
        style_changed = True

    return style_changed


if __name__ == '__main__':
    process_directory(MOD_DIRECTORY, EXTENSIONS, clean_file)
