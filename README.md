# Pie Extended

[![Build Status](https://travis-ci.org/hipster-philology/nlp-pie-taggers.svg?branch=master)](https://travis-ci.org/hipster-philology/nlp-pie-taggers)
[![Coverage Status](https://coveralls.io/repos/github/hipster-philology/nlp-pie-taggers/badge.svg?branch=master)](https://coveralls.io/github/hipster-philology/nlp-pie-taggers?branch=master)
![PyPI](https://img.shields.io/pypi/v/pie-extended?style=flat-square)

**Warning**: This software is only compatible with up to Python 3.7 for the moment.

Extension for [`pie`](https://github.com/emanjavacas/pie) to include taggers with their models and pre/postprocessors.

Pie is a wonderful tool to train models. And most of the time, it will be enough. What `pie_extended` is proposing here 
is to provide you with the necessary tools to share your models with customized pre- and post-processing.

The current system provide an easier access to adding **customized**:
- normalization of your text,
- sentence tokenization,
- word tokenization,
- disambiguation,
- output formatting

## Cite as

```
@software{thibault_clerice_2020_3883590,
  author       = {Clérice, Thibault},
  title        = {Pie Extended, an extension for Pie with pre-processing and post-processing},
  month        = jun,
  year         = 2020,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.3883589},
  url          = {https://doi.org/10.5281/zenodo.3883589}
}
```

## Current supported languages

- Classical Latin (Modele: `lasla`)
- Ancient Greek (Modele: `grc`)
- Old French (Modele: `fro`)
- Early Modern French (Modele: `freem`)
- Classical French (Modele: `fr`)

If you trained models and want some help sharing them with Pie Extended, open an issue :)

## Install

To install, simply do `pip install pie-extended`. Then, look at all available models.

## Run on terminal

But on top of that, it provides a quick and easy way to use others models ! For example, in a shell :

```bash
pie-extended download lasla
pie-extended install-addons lasla
pie-extended tag lasla your_file.txt
```

will give you access to all you need !

## Python API

You can run the lemmatizer in your own scripts and retrieve token annotations as dictionaries:

```python
from typing import List
from pie_extended.cli.utils import get_tagger, get_model, download

# In case you need to download
do_download = False
if do_download:
    for dl in download("lasla"):
        x = 1

# model_path allows you to override the model loaded by another .tar
model_name = "lasla"
tagger = get_tagger(model_name, batch_size=256, device="cpu", model_path=None)

sentences: List[str] = ["Lorem ipsum dolor sit amet, consectetur adipiscing elit. "]
# Get the main object from the model (: data iterator + postprocesor
from pie_extended.models.lasla.imports import get_iterator_and_processor
for sentence_group in sentences:
    iterator, processor = get_iterator_and_processor()
    print(tagger.tag_str(sentence_group, iterator=iterator, processor=processor) )
```

will result in

```python
[{'form': 'lorem', 'lemma': 'lor', 'POS': 'NOMcom', 'morph': 'Case=Acc|Numb=Sing', 'treated': 'lorem'},
 {'form': 'ipsum', 'lemma': 'ipse', 'POS': 'PROdem', 'morph': 'Case=Acc|Numb=Sing', 'treated': 'ipsum'},
 {'form': 'dolor', 'lemma': 'dolor', 'POS': 'NOMcom', 'morph': 'Case=Nom|Numb=Sing', 'treated': 'dolor'},
 {'form': 'sit', 'lemma': 'sum1', 'POS': 'VER', 'morph': 'Numb=Sing|Mood=Sub|Tense=Pres|Voice=Act|Person=3',
  'treated': 'sit'},
 {'form': 'amet', 'lemma': 'amo', 'POS': 'VER', 'morph': 'Numb=Sing|Mood=Sub|Tense=Pres|Voice=Act|Person=3',
  'treated': 'amet'}, {'form': ',', 'lemma': ',', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': ','},
 {'form': 'consectetur', 'lemma': 'consector2', 'POS': 'VER',
  'morph': 'Numb=Sing|Mood=Sub|Tense=Pres|Voice=Dep|Person=3', 'treated': 'consectetur'},
 {'form': 'adipiscing', 'lemma': 'adipiscor', 'POS': 'VER', 'morph': 'Tense=Pres|Voice=Dep', 'treated': 'adipiscing'},
 {'form': 'elit', 'lemma': 'elio', 'POS': 'VER', 'morph': 'Numb=Sing|Mood=Ind|Tense=Pres|Voice=Act|Person=3',
  'treated': 'elit'}, {'form': '.', 'lemma': '.', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '.'}]
```

## Add a model

- Create a package in `./pie_extended/models/`. Exemple: `foo`.
- Add the name of the package in `./pie_extended/models/__init__.py` in the variable `modules`.
- In the module `pie_extended.models.foo`, we should find the following variable:
    - `Models` : a string with filenames and tasks for Pie.
    - `DESC`: a METADATA object that bears information about the model
    - `DOWNLOADS`: A list of file to download.
    
```python
from pie_extended.utils import Metadata, File, get_path

DESC = Metadata(
    "Foo"
    "language",
    ["Author 1", "Author 2"],
    "A readable description",
    "A link to more information"
)

DOWNLOADS = [
    File("/a/link/to/a/file", "local_name_of_the_file.tar")
]


Models = "<{},task1,task2><{},lemma,pos>".format(
    get_path("foo", "local_name_of_the_file.tar")
)

```
- In the module `pie_extended.models.foo.imports`, we should find the following content:
    1. `get_iterator_and_processor`: a function that returns a `DataIterator` and a `Processor` 
    2. (optionally) `addons`: a function that installs add-ons
    3. (optionally) `Disambiguator`: a disambiguator instance (or an object creator that returns one)

Check for a simple example in `pie_extended.models.fro.imports` and a more complex one 
in `pie_extended.models.lasla.imports`


## Install development version (⚠ for development only)

Clone the repository, create an environment, and then

```bash
python setup.py develop
```

## Warning

This is an extremely early build, subject to change here and there. But it is functional !
