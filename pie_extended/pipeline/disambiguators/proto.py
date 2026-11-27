from typing import Tuple, List, Dict


class Disambiguator:
    """ Function or class that takes a list of words and returns the disambiguated list of words as tuples"""
    # Tasks that must be tagged for the disambiguator to work
    required: Tuple[str, ...] = ()

    def can_run(self, tasks: List[str]) -> bool:
        """ Disambiguation is skipped when some of the tasks it needs were not tagged """
        return all(task in tasks for task in self.required)

    def __call__(self, sent, tasks) -> Tuple[List[str], List[Dict[str, str]]]:
        raise NotImplementedError
