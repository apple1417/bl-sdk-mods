import argparse
import gzip
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compresses a json file, removing all whitespace then gzipping."
    )
    parser.add_argument(
        "file",
        type=argparse.FileType("r"),
        help="The file to compress."
    )
    parser.add_argument(
        "output",
        nargs="?",
        help=(
            "The output file. If not specified, defaults to the input file with an extra \".gz\""
            " extension."
        )
    )
    parser.add_argument(
        "-s", "--sort-keys",
        action="store_true",
        help="If to sort json keys before compressing."
    )
    args = parser.parse_args()

    output = args.output or args.file.name + ".gz"
    with gzip.open(output, "wt", encoding="utf8") as gzfile:
        json.dump(
            json.load(args.file),
            gzfile,
            indent=None,
            separators=(",", ":"),
            sort_keys=args.sort_keys
        )
