from typing import Tuple, Iterable
from .. import models
from ..utils import Metadata
import requests
import os


PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "downloads"
    )
)


def download(module):
    lemmatizer = getattr(models, module)
    os.makedirs(os.path.join(PATH, module), exist_ok=True)
    yield len(lemmatizer.DOWNLOADS)
    for file in lemmatizer.DOWNLOADS:
        data = requests.get(file.url)
        new_path = os.path.join(
            PATH, module, file.name
        )
        with open(new_path, "wb") as f:
            f.write(data.content)
        yield file.name


def get_list() -> Iterable[Tuple[str, Metadata]]:
    for module in dir(models):
        desc = getattr(getattr(models, module), "DESC", None)
        if desc:
            yield module, desc
