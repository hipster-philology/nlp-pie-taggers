from collections import namedtuple
import os

Metadata = namedtuple("Metadata", ["title", "lang", "authors", "description", "link"])

_File = namedtuple("File", ["url", "name"])


class File(_File):
    def __str__(self):
        return self.name


PATH = os.getenv(
    "PIE_EXTENDED_DOWNLOADS",
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "downloads"
        )
    )
)


def get_path(module, file):
    return os.path.join(PATH, module, file)


class ObjectCreator:
    """ Some objects should be reset everytime a new tagging is done. To make this easier
    we provide this class that keeps in memory the initialization parameters."""
    def __init__(self, cls, *args, **kwargs):
        self.cls = cls
        self.args = args
        self.kwargs = kwargs

    def create(self):
        return self.cls(*self.args, **self.kwargs)


def roman_number(inp: str) -> int:
    """
    Source: https://stackoverflow.com/questions/19308177/converting-roman-numerals-to-integers-in-python
    Author: https://stackoverflow.com/users/1201737/r366y
    :param num:
    :return:

    >>> roman_number("XXIV")
    24
    """
    roman_numerals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    for i, c in enumerate(inp.upper()):
        if (i+1) == len(inp) or roman_numerals[c] >= roman_numerals[inp[i+1]]:
            result += roman_numerals[c]
        else:
            result -= roman_numerals[c]
    return result
