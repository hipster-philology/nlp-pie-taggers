from typing import List, Callable, Dict


class Formatter:  # Default is TSV
    """ The CSV formatter necessarily starts with form in its header.

    """
    format_line: Callable[[Dict[str, str]], List[str]]

    def __init__(self, tasks: List[str]):
        self.tasks: List[str] = tasks

        # With post-processing, the order of the dictionary cannot be trusted: columns are taken by name
        self.format_line = self.format_line_3_6

    def format_line_3_6(self, annotation: Dict[str, str]) -> List[str]:
        """ Format the tags """
        return [annotation["form"]] + [annotation[task] for task in self.tasks]

    def write_line(self, formatted):
        return "\t".join(formatted) + "\r\n"

    def write_footer(self) -> str:
        return ""

    def get_headers(self):
        return ["token"] + self.tasks

    def write_headers(self)-> str:
        """ Format the headers """
        return self.write_line(self.get_headers())
