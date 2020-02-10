import os
from typing import Tuple, Iterable, Generator, Union
from importlib import import_module

import requests

from .. import models
from ..utils import Metadata, PATH, get_path
from ..tagger import ExtensibleTagger
from ..utils import ObjectCreator
from pie.utils import model_spec


def get_model(model):
    return import_module("{}.{}".format(models.__name__, model))


def download(module) -> Iterable[Union[str, int]]:
    lemmatizer = get_model(module)
    os.makedirs(os.path.join(PATH, module), exist_ok=True)
    yield len(lemmatizer.DOWNLOADS)
    for file in lemmatizer.DOWNLOADS:

        data = requests.get(file.url)
        new_path = get_path(module, file.name)

        with open(new_path, "wb") as f:
            f.write(data.content)
        yield file.name


def get_list() -> Iterable[Tuple[str, Metadata]]:
    for module in models.modules:
        desc = getattr(get_model(module), "DESC", None)
        if desc:
            yield module, desc


def get_tagger(model: str, batch_size: int = 16, device="cpu", model_path=None) -> ExtensibleTagger:
    module = get_model(model)
    disambiguator = getattr(module, "Disambiguator", None)
    if isinstance(disambiguator, ObjectCreator):
        disambiguator = disambiguator.create()
    tagger = ExtensibleTagger(disambiguation=disambiguator, batch_size=batch_size, device=device)
    model_spec_string = model_path or getattr(module, "Models")
    for model, tasks in model_spec(model_spec_string):
        tagger.add_model(model, *tasks)
    return tagger


def tag_file(model: str, tagger: ExtensibleTagger, fpath):
    module = get_model(model)
    iterator, formatter = getattr(module, "get_iterator_and_formatter")()
    tagger.tag_file(fpath, iterator=iterator, formatter_class=formatter)
    return True


def get_addons(model: str):
    """ Runs the `addons` function from a module """
    module = get_model(model)
    addons = getattr(module, "addons", lambda : True)
    return addons()
