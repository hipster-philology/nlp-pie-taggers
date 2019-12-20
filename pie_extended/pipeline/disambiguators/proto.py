from typing import Tuple, List, Dict


class Disambiguator:
    """ Function or class that takes a list of words and returns the disambiguated list of words as tuples"""
    def __call__(self, sent, tasks) -> Tuple[List[str], List[Dict[str, str]]]:
        raise NotImplementedError
