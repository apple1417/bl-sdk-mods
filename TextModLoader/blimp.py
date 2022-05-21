from typing import Dict, Iterable, List, Tuple


def parse_blimp_tags(comments: Iterable[str]) -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Parses out the BLIMP tags stored in a comment block.

    Args:
        comments: A list of extracted comments.
    Returns:
        A dict mapping each found BLIMP tag to a list of it's encountered values.
        A list of all lines that were found not to have a tag.
    """

    found_tags: Dict[str, List[str]] = {}
    untagged_lines = []

    for line in comments:
        if not line:
            continue
        if line[0] != "@":
            untagged_lines.append(line)
            continue
        tag, _, data = line.partition(" ")
        tag = tag.lower()

        if tag == "@":
            continue

        if tag not in found_tags:
            found_tags[tag] = []
        found_tags[tag].append(data)

    return found_tags, untagged_lines


""" Make calling this file work as a BLIMP tester program. """
if __name__ == "__main__":
    import json
    import sys

    import tml_parser  # type: ignore

    _, _, comments = tml_parser.parse_string(sys.stdin.read())
    tags, _ = parse_blimp_tags(comments)

    sys.stdout.write(json.dumps(tags))
    exit(0)
