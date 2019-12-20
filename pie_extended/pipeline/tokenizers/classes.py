from typing import Callable, Iterable, List

Tokenizer = Callable[[str, bool], Iterable[List[str]]]


