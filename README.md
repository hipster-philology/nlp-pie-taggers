# Pie Extended

[![Build Status](https://travis-ci.org/hipster-philology/nlp-pie-taggers.svg?branch=master)](https://travis-ci.org/hipster-philology/nlp-pie-taggers)
[![Coverage Status](https://coveralls.io/repos/github/hipster-philology/nlp-pie-taggers/badge.svg?branch=master)](https://coveralls.io/github/hipster-philology/nlp-pie-taggers?branch=master)
![PyPI](https://img.shields.io/pypi/v/pie-extended?style=flat-square)

**Requirements**: Python 3.12 or later (tested on 3.12, 3.13 and 3.14), PaPie 0.6.1 or later (it allows recent PyTorch versions, hence recent Pythons).

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

- Classical Latin (Model: `lasla`)
- Ancient Greek (Model: `grc`)
- Old French (Model: `fro`)
- Middle French (Model: `frm`)
- Early Modern French (Model: `freem`)
- Classical French (Model: `fr`)
- Old Dutch (Model: `dum`)
- Old Occitan (Model: `old_occ`)
- Old Castilian (Model: `osp`, dummy models)
- Eastern Armenian (Model: `hy_hye`)
- Western Armenian (Model: `hy_hyw`)
- Classical Armenian (Model: `hy_xcl`)

If you trained models and want some help sharing them with Pie Extended, open an issue :)

### Armenian

`hy_hye` (Eastern, `hye`), `hy_hyw` (Western, `hyw`) and `hy_xcl` (Classical, `xcl`) are the Pie models of
[Vidal-Gorène et al. (2024)](https://aclanthology.org/2024.nlp4dh-1.42/): one Pie model per task, so
`--tasks lemma,pos` loads 2 models instead of 25 or 30. They share one tokenizer (`ArmenianTokenizer`) that follows
the tokenization of their Universal Dependencies treebanks:

- punctuation (`։ ՝ « » ( ) , ...`) and hyphens are tokens of their own;
- the marks written on a vowel (`Մի՞թե`, `թե՛`) become a token after their word (`Միթե`, `՞`). `SpaceAfter` is `No`
  for the word, since the mark was written inside it;
- numbers (`1.000`) and ellipsis stay in one piece, the Western apostrophe stays on its clitic (`կ՚`, `ուզեմ`);
- sentences end with `։ : ! ? …`, not with a dot (initials, abbreviations and numbers).

On the dev sets of the Eastern and Western treebanks, the tokenizer gives the gold words of 99.5% and 99.4% of the
sentences.

**Classical Armenian** needs one more step. Its treebank (and so the model, which asks for pre-tokenized input) makes
the clitics words of their own: `զմեղս` -> `զ`, `մեղս`; `յանապատին` -> `յ`, `անապատի`, `ն`. No rule can do it (many
words begin with `զ` or end with `ն`), so a small model learns where the treebank cuts:

```bash
pie-extended install-addons hy_xcl   # downloads the treebank, learns in a few seconds, keeps 160 KB
```

On the test set of the treebank, this finds the cuts with an F1 of 97.3%, and the words of 90% of the sentences are
exactly the ones of the treebank (13% without it). The treebank is CC BY-NC-SA 4.0: what is learned stays on your
machine, it is not distributed with Pie Extended. Without this step the clitics are not split, and a warning says so.
`tests/data/armenian_ud_sample.json` contains a few sentences of the Eastern and Western treebanks
([UD_Armenian-ArmTDP](https://github.com/UniversalDependencies/UD_Armenian-ArmTDP) and
[UD_Western_Armenian-ArmTDP](https://github.com/UniversalDependencies/UD_Western_Armenian-ArmTDP), CC BY-SA 4.0).

## Install

To install, simply do `pip install pie-extended`. Then, look at all available models.

### WARNING: if you don't have a GPU or CUDA

Please, in case of doubt, run `pip install pie-extended  --extra-index-url https://download.pytorch.org/whl/cpu`


## Run on terminal

But on top of that, it provides a quick and easy way to use others models ! For example, in a shell :

```bash
pie-extended download lasla
pie-extended install-addons lasla
pie-extended tag lasla your_file.txt
```

will give you access to all you need !

Useful options of `pie-extended tag`:

- `--tasks lemma,POS`: only output (and only load/run the models needed for) these columns.
- `--space-after / --no-space-after`: the last column, `SpaceAfter`, tells if a token is followed by a space in the
  original text. It is `No` when the next token is glued to it (`virumque` in `virumque: cano`) and `_` otherwise
  (and for the last token of a text). It is on by default, but cannot be used with `--no-tokenizer` (the original
  spacing of pre-tokenized input is lost): use `--no-tokenizer --no-space-after`.
- `--no-quantize`, `--no-cache`, `--cache-size`, `--num-threads`: tune speed/memory.

In Python, `get_pipeline(model, tagger)` builds the iterator and processor (with the `SpaceAfter` column unless
`space_after=False`) once, so that you can reuse them over several texts. The processors given by
`get_iterator_and_processor()` do not output it: wrap them with `SpaceAfterProcessor(processor)` to get it.

## Using other tools (spaCy, GreCy)

A model does not have to run through Pie. `pie_extended.spacy_tagger.SpacyTagger` runs a spaCy pipeline behind
the same iterators, processors and options (`--tasks`, `SpaceAfter`...). `grc_grecy` is the first one:
Ancient Greek with [GreCy](https://github.com/jmyerston/greCy).

```bash
pip install pie-extended[grecy]
pie-extended install-addons grc_grecy   # installs the spaCy pipeline (grc_proiel_sm)
pie-extended tag grc_grecy your_file.txt --tasks lemma,pos
```

Tasks are `lemma`, `pos` (universal POS), `tag` (language specific POS) and `morph` (UD features).
To add another spaCy model, create a model package with `Backend = "spacy"` and a `Models` string whose "path" is
the name of the spaCy pipeline (see `pie_extended/models/grc_grecy`).

### Demo: lemma and POS only

In a shell, `--tasks lemma,pos` keeps these two columns and `--no-space-after` removes the `SpaceAfter` column:

```bash
echo "ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν." > demo.txt
pie-extended tag grc_grecy demo.txt --tasks lemma,pos --no-space-after
cat demo-pie.txt   # the output is written next to the input (tab separated, \r\n line endings)
```

```
token	lemma	pos
ἐν	ἐν	ADP
ἀρχῇ	ἀρχή	NOUN
ἦν	εἰμί	AUX
ὁ	ὁ	DET
λόγος	λόγος	NOUN
,	,	PUNCT
καὶ	καί	CCONJ
```

The same in Python, writing the TSV on the standard output:

```python
import sys
from pie_extended.cli.utils import get_pipeline, get_tagger

tagger = get_tagger("grc_grecy", tasks=["lemma", "pos"])  # tasks=None: lemma, morph, pos, tag
iterator, processor = get_pipeline("grc_grecy", tagger, space_after=False)

text = "ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν."
for line in tagger.iter_tag(text, iterator, processor=processor):
    sys.stdout.write(line.replace("\r\n", "\n"))
```

Without `--no-space-after` (`space_after=False`), a last `SpaceAfter` column is `No` when the next token is glued to
the token (`λόγος` followed by a comma) and `_` otherwise.

### Using a larger model

The default pipeline is `grc_proiel_sm`. GreCy also provides `grc_proiel_{sm,lg,trf}` and `grc_perseus_{sm,lg,trf}`.
Install the pipeline you want (the `trf` ones also need `spacy-transformers`) and select it with the same
`<pipeline,tasks>` syntax as the other models:

```bash
pip install spacy-transformers
pip install "https://github.com/jmyerston/greCy/releases/download/v3.8.2/grc_proiel_trf-3.8.2-py3-none-any.whl"
pie-extended tag grc_grecy demo.txt --tasks lemma,pos --no-space-after \
    --model_path "<grc_proiel_trf,lemma,morph,pos,tag>"
```

```python
tagger = get_tagger("grc_grecy", tasks=["lemma", "pos"], model_path="<grc_proiel_trf,lemma,morph,pos,tag>")
```

Two different GreCy pipelines cannot be loaded in the same Python process (spaCy refuses to register their components
twice): use one pipeline per run.

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
pip install -e .
```

## Warning

This is an extremely early build, subject to change here and there. But it is functional !
