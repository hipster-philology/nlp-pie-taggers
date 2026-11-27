import os
import sys
from typing import Tuple, Iterable, List, Union, Optional
from importlib import import_module

import requests

from .. import models
from ..utils import Metadata, PATH, get_path
from ..tagger import ExtensibleTagger
from ..utils import ObjectCreator
from ..pipeline.postprocessor.proto import SelectTasksProcessor
from pie.utils import model_spec


def check(model: str, force: bool = False) -> bool:
    """ Check if files are available for a given model """
    module = get_model(model)
    return False not in [
        os.path.exists(
            get_path(model, file.name)
        )
        for file in module.DOWNLOADS
    ] or force


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


def resolve_tasks(model: str, requested: Iterable[str], spec: List[Tuple[str, List[str]]]
                  ) -> Tuple[List[str], List[Tuple[str, List[str]]]]:
    """ Finds out which models/tasks need to be run to produce the requested output columns

    :param model: Module name of the language
    :param requested: Output columns wanted (case insensitive), e.g. ["lemma", "POS"]
    :param spec: Parsed model specification [(path, [tasks])]
    :return: Canonical output columns and the reduced model specification. Models for which no task
        is needed are dropped, so that they are neither loaded nor run.

    :raises ValueError: If a requested column does not exist for this language
    """
    imports = get_imports(get_model(model))
    available = sorted({task for _, tasks in spec for task in tasks})

    # What the processor would output when everything is tagged
    probe = imports.get_iterator_and_processor()[1]
    outputs = list(probe.set_tasks(available))

    lookup = {name.lower(): name for name in outputs}
    selected, unknown = [], []
    for name in requested:
        found = lookup.get(name.strip().lower())
        if found is None:
            unknown.append(name)
        elif found not in selected:
            selected.append(found)
    if unknown:
        raise ValueError("Unknown task(s) {} for {}. Available: {}".format(
            ", ".join(unknown), model, ", ".join(outputs)))

    needed = set(probe.required_tasks(selected, available))
    disambiguator = getattr(imports, "Disambiguator", None)
    # The disambiguation modifies the lemma: it is only worth its (costly) tasks if the lemma is wanted
    if disambiguator is not None and "lemma" in [s.lower() for s in selected]:
        needed.update(getattr(disambiguator, "required", ()))

    reduced = []
    for path, tasks in spec:
        kept = [task for task in tasks if task in needed]
        if kept:
            reduced.append((path, kept))
    return selected, reduced


def get_tagger(model: str, batch_size: int = 16, device="cpu", model_path=None,
               quantize: bool = True, cache: bool = True, tasks: Optional[Iterable[str]] = None,
               cache_size: Optional[int] = None, num_threads: Optional[int] = None) -> ExtensibleTagger:
    """ Retrieve the tagger

    :param model: Module of the tagger
    :param batch_size: Size of the batch
    :param device: Device to use (cuda/cpu)
    :param model_path: Path to the model if you want to override the package one
    :param quantize: Use Int8 quantization (cpu only)
    :param cache: Use cache
    :param tasks: Only compute these output columns (e.g. ["lemma", "POS"]). Models that are not needed
        for them are not loaded. None means everything.
    :param cache_size: Size of the embedding cache
    :param num_threads: Number of torch threads
    :return: Tagger
    """
    module = get_model(model)
    spec = list(model_spec(model_path or getattr(module, "Models")))
    selected = None
    if tasks:
        selected, spec = resolve_tasks(model, tasks, spec)

    disambiguator = getattr(get_imports(module), "Disambiguator", None)
    if isinstance(disambiguator, ObjectCreator):
        disambiguator = disambiguator.create()
    tagger = ExtensibleTagger(disambiguation=disambiguator, batch_size=batch_size, device=device,
                              quantize=quantize, cache=cache, cache_size=cache_size, num_threads=num_threads)
    for path, model_tasks in spec:
        tagger.add_model(path, *model_tasks)
    # Output columns to keep when writing (hidden dependencies such as lemma for clitic splitting are dropped)
    tagger.selected_outputs = selected
    return tagger


def get_pipeline(
        model: str, tagger: ExtensibleTagger,
        reset_exclude_patterns: bool = False,
        exclude_patterns: Optional[Iterable[str]] = None,
        max_tokens: int = 256):
    """ Builds the (iterator, processor) couple for a model, ready to be reused over several files

    Reuse is safe because `ExtensibleTagger.iter_tag_token` resets the processor chain and the tokenizer
    before each document (memory of the tokenizer, cursor of the memorizing processor, ...).

    :param model: Module name of the model
    :param tagger: Tagger that will be used (gives the subset of outputs, if any)
    :param reset_exclude_patterns: Remove all pre-registered token exclusion regular expressions
    :param exclude_patterns: New exclude patterns to add to the data iterator (Does not require reset)
    :param max_tokens: Maximum sentence length
    """
    module = get_model(model)
    iterator, processor = getattr(get_imports(module), "get_iterator_and_processor")(max_tokens=max_tokens)
    selected = getattr(tagger, "selected_outputs", None)
    if selected:
        processor = SelectTasksProcessor(processor, selected)
    # Remove first pattern
    if reset_exclude_patterns:
        iterator.reset_patterns()

    # Add new
    for pattern in exclude_patterns or []:
        iterator.add_pattern(pattern)
    return iterator, processor


def tag_file(
        model: str, tagger: ExtensibleTagger,
        fpath: str,
        reset_exclude_patterns: bool = False,
        exclude_patterns: List[str] = None,
        no_tokenizer: bool = False,
        max_tokens: int = 256,
        pipeline: Optional[Tuple] = None):
    """ Tag a file with a given model

    :param model: Module name of the model
    :param tagger: Tagger that should be used
    :param fpath: Path to the file to edit
    :param reset_exclude_patterns: Remove all pre-registered token exclusion regular expressions
    :param exclude_patterns: New exclude patterns to add to the data iterator (Does not require reset)
    :param no_tokenizer: Does not use usual tokenizers (new line = word separator, two new lines = sentence_
    :param pipeline: (iterator, processor) built by `get_pipeline` to reuse over several files. When given,
        `reset_exclude_patterns`, `exclude_patterns` and `max_tokens` were applied at its creation
        and are ignored here.
    """
    if pipeline is None:
        pipeline = get_pipeline(model, tagger, reset_exclude_patterns=reset_exclude_patterns,
                                exclude_patterns=exclude_patterns, max_tokens=max_tokens)
    iterator, processor = pipeline
    tagger.tag_file(fpath, iterator=iterator, processor=processor, no_tokenizer=no_tokenizer)
    return True


def get_addons(model: str):
    """ Runs the `addons` function from a module """
    module = get_model(model)
    addons = getattr(get_imports(module), "addons", lambda: print("No add-ons needed for " + model))
    return addons()
