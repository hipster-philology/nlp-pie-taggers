from collections import namedtuple
import os


Metadata = namedtuple("Metadata", ["title", "lang", "authors", "description", "link"])

_File = namedtuple("File", ["url", "name"])


class File(_File):
    def __str__(self):
        return self.name


PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "downloads"
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
