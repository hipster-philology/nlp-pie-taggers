import os
import sys
from typing import Tuple, Iterable, List, Union
from importlib import import_module

import requests

from .. import models
from ..utils import Metadata, PATH, get_path
from ..tagger import ExtensibleTagger
from ..utils import ObjectCreator
from pie.utils import model_spec

def get_model(model: str):
    """ Retrieve a module given a string

    :param model: Module Name
    :return: Module
    """
    return import_module("{}.{}".format(models.__name__, model))


def get_imports(module):
    return import_module("{}.{}".format(module.__name__, "imports"))


def _download(url, filename):
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')


def download(module: str) -> Iterable[Union[str, int]]:
    """ Download dependencies for the given module

    :param module: Module for which to download models and static files in general
    """
    lemmatizer = get_model(module)
    os.makedirs(os.path.join(PATH, module), exist_ok=True)
    yield len(lemmatizer.DOWNLOADS)
    for file in lemmatizer.DOWNLOADS:

        new_path = get_path(module, file.name)
        _download(file.url, new_path)
        yield file.name


def get_list() -> Iterable[Tuple[str, Metadata]]:
    """ Retrieve a list of available modules
    """
    for module in models.modules:
        desc = getattr(get_model(module), "DESC", None)
        if desc:
            yield module, desc


def get_tagger(model: str, batch_size: int = 16, device="cpu", model_path=None) -> ExtensibleTagger:
    """ Retrieve the tagger

    :param model: Module of the tagger
    :param batch_size: Size of the batch
    :param device: Device to use (cuda/cpu)
    :param model_path: Path to the model if you want to override the package one
    :return: Tagger
    """
    module = get_model(model)

    disambiguator = getattr(get_imports(module), "Disambiguator", None)
    if isinstance(disambiguator, ObjectCreator):
        disambiguator = disambiguator.create()
    tagger = ExtensibleTagger(disambiguation=disambiguator, batch_size=batch_size, device=device)
    model_spec_string = model_path or getattr(module, "Models")
    for model, tasks in model_spec(model_spec_string):
        tagger.add_model(model, *tasks)
    return tagger


def tag_file(
        model: str, tagger: ExtensibleTagger,
        fpath: str,
        reset_exclude_patterns: bool = False,
        exclude_patterns: List[str] = None):
    """ Tag a file with a given model

    :param model: Module name of the model
    :param tagger: Tagger that should be used
    :param fpath: Path to the file to edit
    :param reset_exclude_patterns: Remove all pre-registered token exclusion regular expressions
    :param exclude_patterns: New exclude patterns to add to the data iterator (Does not require reset)
    """
    module = get_model(model)
    iterator, processor = getattr(get_imports(module), "get_iterator_and_processor")()
    # Remove first pattern
    if reset_exclude_patterns:
        iterator.reset_patterns()

    # Add new
    if exclude_patterns:
        for pattern in exclude_patterns:
            iterator.add_pattern(pattern)

    tagger.tag_file(fpath, iterator=iterator, processor=processor)
    return True


def get_addons(model: str):
    """ Runs the `addons` function from a module """
    module = get_model(model)
    addons = getattr(get_imports(module), "addons", lambda: print("No add-ons needed for " + model))
    return addons()
