from typing import List, Iterable


class Formatter:  # Default is TSV
    def __init__(self, tasks: List[str]):
        self.tasks: List[str] = tasks

    def format_line(self, token: str, tags: Iterable[str], ignored=False) -> List[str]:
        """ Format the tags"""
        return [token] + list(tags)

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
