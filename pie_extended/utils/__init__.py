from collections import namedtuple

Metadata = namedtuple("Metadata", ["title", "lang", "authors", "description", "link"])
File = namedtuple("File", ["url", "name"])
