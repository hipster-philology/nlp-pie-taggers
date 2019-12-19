import os
from typing import Tuple, Iterable

import requests

from .. import models
from ..utils import Metadata, PATH, get_path
from ..tagger import ExtensibleTagger
from pie.utils import model_spec


def download(module):
    lemmatizer = getattr(models, module)
    os.makedirs(os.path.join(PATH, module), exist_ok=True)
    yield len(lemmatizer.DOWNLOADS)
    for file in lemmatizer.DOWNLOADS:

        data = requests.get(file.url)
        new_path = get_path(module, file.name)

        with open(new_path, "wb") as f:
            f.write(data.content)
        yield file.name


def get_list() -> Iterable[Tuple[str, Metadata]]:
    for module in dir(models):
        desc = getattr(getattr(models, module), "DESC", None)
        if desc:
            yield module, desc


def get_tagger(model: str) -> ExtensibleTagger:
    module = getattr(models, model)
    disambiguator = getattr(module, "Disambiguator", None)
    tagger = ExtensibleTagger(disambiguation=disambiguator)
    for model, tasks in model_spec(getattr(module, "Models")):
        tagger.add_model(model, *tasks)
    return tagger


def tag_file(model: str, tagger: ExtensibleTagger, fpath):
    module = getattr(models, model)
    iterator = getattr(module, "Iterator", None)
    formatter = getattr(module, "Formatter", None)
