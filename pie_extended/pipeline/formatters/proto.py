from typing import List, Iterable, Callable, Dict
import sys


class Formatter:  # Default is TSV
    """ The CSV formatter necessarily starts with form in its header.

    """
    format_line: Callable[[Dict[str, str]], List[str]]

    def __init__(self, tasks: List[str]):
        self.tasks: List[str] = tasks

        # Before 3.7, order of dictionary is not guaranteed
        # Cf. https://mail.python.org/pipermail/python-dev/2017-December/151283.html
        self.format_line = self.format_line_3_6
        # With post-processing, it's better to not trust order
        #else:
        #    self.format_line = self.format_line_3_7

    def format_line_3_6(self, annotation: Dict[str, str]) -> List[str]:
        """ Format the tags """
        return [annotation["form"]] + [annotation[task] for task in self.tasks]

    def format_line_3_7(self, annotation: Dict[str, str]) -> List[str]:
        """ Format the tags """
        return list(annotation.values())

    def write_line(self, formatted):
        return "\t".join(formatted) + "\r\n"

    def write_sentence_beginning(self) -> str:
        return ""

    def write_sentence_end(self) -> str:
        return ""

    def write_footer(self) -> str:
        return ""

    def get_headers(self):
        return ["token"] + self.tasks

    def write_headers(self)-> str:
        """ Format the headers """
        return self.write_line(self.get_headers())
