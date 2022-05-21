from __future__ import annotations

from typing import List, Optional, Tuple

ParsingResultsTuple = Tuple[Optional[int], Optional[str], List[str]]

class BLCMMParserError(RuntimeError):
    ...

def parse(file_path: str) -> ParsingResultsTuple: ...
def parse_string(str: str) -> ParsingResultsTuple: ...
