# Backends

This page is for the people who **write or change a model**: what a backend is, how the spaCy one runs a pipeline, and
how to change the pipeline of `grc_grecy`, add another spaCy pipeline as a model, or add a task. To tag texts, read
{doc}`tagger` (command line) and {doc}`api-usage` (Python).

The **backend** is the part that turns tokens into predictions. Everything else (the data iterator, the processors,
`SpaceAfter`, `--tasks`, the formatter) is the same for all of them. There are two:

| | Pie (the default) | spaCy |
|---|---|---|
| In the package of the model | `Backend` is not set | `Backend = "spacy"` |
| Tagger | {class}`~pie_extended.tagger.ExtensibleTagger` | {class}`~pie_extended.spacy_tagger.SpacyTagger` |
| `Models` | `<file,task,task><file,task>`: one network per file | `<pipeline,task,task>`: the name of **one** spaCy pipeline, that gives all the tasks |
| Tasks | what the files were trained for | `lemma`, `pos`, `tag`, `morph` |
| What the model needs | `pie-extended download` (the files) | `pie-extended install-addons` (the pipeline, with pip) |

{func}`~pie_extended.cli.utils.get_tagger` reads `Backend` in the package of the model and builds the matching tagger.
A third kind, **composite** (`Backend = "composite"`), takes each task from the engine that is best at it: see
[Combine engines](#combine-engines-a-lemmatizer-and-a-spacy-pipeline).

## How the spaCy backend runs a pipeline

- **Words, not text.** The words come from the data iterator, and are given to spaCy as already tokenized documents:
  the tokenizer of spaCy is never used. The tokenizer of the model has to give what the pipeline was *trained* on (for
  GreCy, the apostrophe of an elision is written U+02BC for the model, and your spelling is kept in `token`: see
  `pie_extended.models.grc_grecy.tokenizer`).
- **Tasks are attributes of the tokens.** `lemma`, `pos`, `tag` and `morph` are the attributes `lemma_`, `pos_`, `tag_`
  and `morph` of a spaCy token (`morph` is `_` when it is empty). They are listed in `SpacyTagger.EXTRACTORS`.
- **Only what is useless is skipped.** The components that never give a task (the parser, the named entities...,
  `SpacyTagger.UNUSED_COMPONENTS`) are not run, the others are: pipelines differ (the transformer ones of GreCy have a
  `morpheus_lemmatizer` that the small ones lack, and skipping it changes lemmas). The gain is small, because the
  encoder costs far more than the parser.
- **One pipeline per tagger.** A pipeline that is not installed raises `PipelineNotFound`, a `FileNotFoundError` whose
  message tells how to install it: the command shows it.

### Why words, and not the text?

spaCy could be given the raw text, and tokenize it itself. We send words instead, and it was measured why (GreCy
pipelines against the Universal Dependencies treebanks they are trained on, dev sets; the treebanks are
non-commercial, so they are not part of the repository):

| | spaCy's tokenizer, on the text | Our tokenizer |
|---|---|---|
| Sentences with exactly the tokens of the treebank (Perseus, 1137 sentences) | 99.6% | 99.8% |

The tokens are the same for practical purposes, and when they are, **the predictions are the same**: with
`grc_perseus_trf` on 400 sentences, the lemma (93.52%) and the part of speech (89.58%) are identical whether the model
receives the text, our words, or our words with the real spacing (the small pipelines too). So the raw text brings
nothing. What it costs is the normalization done before the model:

| Elided words of PROIEL (90), `grc_proiel_trf` | Lemma right |
|---|---|
| Apostrophe written U+02BC (what we send; your spelling stays in `token`) | 100% |
| As the treebank writes it (`’`) | 57% |
| The raw text, tokenized by spaCy | 54% |

GreCy only understands the elision when its apostrophe is U+02BC, and real texts hardly ever write it so. Sending the text
would also give up the tokens that are excluded from tagging, `treated`, `SpaceAfter` and our sentences. (Take the
absolute numbers with care: the treebanks are the data of the pipelines, and only the *differences* between the lines
are the point.)

(change-the-pipeline)=
## Change the pipeline of `grc_grecy`

The name of the pipeline is written **once**, in the package of the model:

```python
# pie_extended/models/grc_grecy/__init__.py
SpacyModel = "grc_perseus_trf"
Models = "<{},lemma,morph,pos,tag>".format(SpacyModel)
```

It is the pipeline that `pie-extended tag grc_grecy` runs, *and* the one that `pie-extended install-addons grc_grecy`
installs: `addons()` in `imports.py` reads `SpacyModel` too. To run another pipeline:

1. **Change `SpacyModel`** to the name of a GreCy pipeline: `grc_perseus_{sm,lg,trf}` or `grc_proiel_{sm,lg,trf}`
   (the Perseus one with a transformer, `grc_perseus_trf`, is the default).
2. **Install it**: `pie-extended install-addons grc_grecy`. It takes the wheel of the pipeline in the releases of GreCy,
   of the version `GRECY_VERSION` in `imports.py` (change it when GreCy publishes a new one).
3. **Check what it needs.** The transformer pipelines need `spacy-transformers`, which is in the extra `grecy` of
   `pyproject.toml`. If you choose a pipeline without a transformer, you can remove it from there.
4. **Check the tasks** of `Models`: they must be given by the pipeline. The `sm` and `trf` pipelines of both treebanks
   give the four of the default (the tests check it); the `lg` ones were not tried.
5. **Run the tests**: `pytest tests/test_spacy_tagger.py`. They use the pipeline of `SpacyModel` and compare the
   result with plain spaCy for every GreCy pipeline that is installed (they are skipped without spaCy or without the
   pipeline).
6. **Tell your users what changes.** The treebanks follow different conventions: the values of `tag` and `morph` are
   not the same from a pipeline of Perseus to one of PROIEL (see {doc}`tagger`).

### Choose the spaCy pipeline: `get_tagger`, or the tagger itself

There are two levels, and they do the same thing with a different amount of help.

**With `get_tagger`**, the usual way: the name of the model gives its package, and `model_path` replaces what it runs.

```python
tagger = get_tagger("grc_grecy", model_path="grc_proiel_sm", tasks=["lemma", "pos"])
iterator, processor = get_pipeline("grc_grecy", tagger, space_after=False)
```

`get_tagger` does five things: it finds the package of the model, and its `Backend`; it turns the name of the spaCy
pipeline into the full `<pipeline,tasks>` of the model; it works out, from the **columns** you ask for with `tasks`, the
**tasks** that have to be computed (and drops the models that are not needed); it makes the disambiguator of the model,
if it has one; and it keeps the columns in `tagger.selected_outputs`, that {func}`~pie_extended.cli.utils.get_pipeline`
reads afterwards.

**With the tagger itself**: a `SpacyTagger` takes the spaCy pipeline and the tasks in its constructor, and a Pie tagger
takes its files with `ExtensibleTagger().add_model("lemma.tar", "lemma")`, one call for each file.

```python
from pie_extended.cli.utils import get_pipeline
from pie_extended.spacy_tagger import SpacyTagger

tagger = SpacyTagger(pipeline="grc_proiel_sm", tasks=["lemma", "pos"])
tagger.selected_outputs = ["lemma", "pos"]          # the columns: see below
iterator, processor = get_pipeline("grc_grecy", tagger, space_after=False)
```

The processing pipeline (the data iterator and the processor, see the {ref}`vocabulary <vocabulary>`) does not depend on
the spaCy pipeline: the same one works with any GreCy pipeline.

```{admonition} Tasks are computed, columns are written
:class: important
The `tasks` of the constructor are what the spaCy pipeline **computes**. The columns that **appear** are
`tagger.selected_outputs` (`None`: all of them). Without it, the output also has the columns that are not tasks, such as
`treated`, which is what you want for a tagger made by hand if you did not ask for columns. `get_tagger(tasks=...)` sets it
for you, so `treated` is left out when you ask for `lemma` and `pos`: setting it by hand, as above, gives exactly the same
output (a test checks it).
```

For a Pie model, `get_tagger` is the way: only it knows how to find the tasks that the post-processing needs. (The Latin
model needs `lemma` to split its enclitics, even when you do not ask for it: the column is hidden, but computed.)

Nothing has to be changed for **one run**: `--model_path grc_proiel_sm` on the command line (or `model_path="grc_proiel_sm"`
in {func}`~pie_extended.cli.utils.get_tagger`) runs another pipeline without touching the code, with the tasks of the
model (see {doc}`tagger`).

```{warning}
Two different GreCy pipelines cannot be loaded in the same Python process: spaCy refuses to register their components
twice. A tagger loads one, but a script that compares pipelines has to use one process for each (see
`tests/spacy_compare.py`).
```

## Add another spaCy pipeline as a model

A spaCy model is a package like the others (see [Add a model](api-usage.md#add-a-model)), with three differences: `Backend`, the
name of the pipeline in `Models`, and an `addons()` that installs the pipeline. Here, with `foo_spacy`:

```python
# pie_extended/models/foo_spacy/__init__.py
from ...utils import Metadata

DESC = Metadata("Foo (spaCy)", "foo", ["Author 1", "Author 2"], "A readable description", "https://example.org/foo")

DOWNLOADS = []          # a spaCy pipeline is a Python package: nothing to download

Backend = "spacy"       # get_tagger builds a SpacyTagger

SpacyModel = "foo_core_news_sm"                          # the name of the pipeline: written once
Models = "<{},lemma,pos,morph>".format(SpacyModel)       # the pipeline, then the tasks it gives
```

```python
# pie_extended/models/foo_spacy/imports.py
import subprocess
import sys

from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.pipeline.tokenizers.simple_tokenizer import SimpleTokenizer

from . import SpacyModel


def get_iterator_and_processor(max_tokens=256):
    # spaCy receives words: tokenize like the data the pipeline was trained on
    return DataIterator(tokenizer=SimpleTokenizer(), max_tokens=max_tokens), ProcessorPrototype()


def addons(name: str = None) -> bool:
    """ What `pie-extended install-addons foo_spacy` runs: install the pipeline """
    return subprocess.call([sys.executable, "-m", "pip", "install", name or SpacyModel]) == 0
```

Then add `"foo_spacy"` to `modules` in `pie_extended/models/__init__.py`, and `spacy` (and what the pipeline needs) to
an extra of `pyproject.toml`: spaCy is an optional dependency, imported only when the pipeline is loaded. The model is
used as any other, and gives what *its* pipeline predicts:

```python
tagger = get_tagger("foo_spacy", tasks=["lemma", "pos"])
iterator, processor = get_pipeline("foo_spacy", tagger, space_after=False)

for token in tagger.tag_str("A text.", iterator=iterator, processor=processor):
    print(token)           # {'form': 'A', 'lemma': ..., 'pos': ...}
```

## Add a task to the spaCy backend

A task is an attribute of the token: add it to `EXTRACTORS`, and stop skipping the component that gives it. For the
dependency labels:

```python
from pie_extended.spacy_tagger import SpacyTagger


class DependencyTagger(SpacyTagger):
    EXTRACTORS = {**SpacyTagger.EXTRACTORS, "dep": lambda token: token.dep_}
    UNUSED_COMPONENTS = SpacyTagger.UNUSED_COMPONENTS - {"parser"}   # the parser gives a task now


tagger = DependencyTagger()
tagger.add_model("grc_perseus_sm", "lemma", "dep")
tagged, tasks = tagger.tag([["ἐν", "ἀρχῇ", "ἦν", "ὁ", "λόγος"]])
print(tasks)
print(tagged[0])
```

```python
['dep', 'lemma']
[('ἐν', ('case', 'ἐν')), ('ἀρχῇ', ('ROOT', 'ἀρχή')), ('ἦν', ('cop', 'εἰμί')), ('ὁ', ('det', 'ὁ')), ('λόγος', ('nsubj', 'λόγος'))]
```

`get_tagger` builds a `SpacyTagger` for `Backend = "spacy"`: use your class directly, as here, with the iterator and the
processor of the model (`get_pipeline` accepts any tagger). The tasks are sorted, as Pie does.

For the reference of the class: {class}`~pie_extended.spacy_tagger.SpacyTagger`.

(combine-engines)=
## Combine engines: a lemmatizer and a spaCy pipeline

Not every task has to come from the same tool. `grc_soter` takes the **lemma** from
[Sôtêr mini](https://huggingface.co/Zual/soter-mini), a lemmatizer of Ancient Greek of 1.9 million parameters
(Apache-2.0), and the **part of speech** from a light GreCy pipeline:

```bash
pip install "pie-extended[soter]"
pie-extended install-addons grc_soter     # the spaCy pipeline, and Sôtêr (7.5 MB, kept in the cache of Hugging Face)
pie-extended tag grc_soter demo.txt
```

```text
token  lemma  pos    treated  SpaceAfter
ἐν     ἐν     ADP    ἐν       _
ἀρχῇ   ἀρχή   NOUN   ἀρχῇ     _
ἦν     εἰμί   AUX    ἦν       _
ὁ      ὁ      DET    ὁ        _
λόγος  λόγος  NOUN   λόγος    No
,      ,      PUNCT  ,        _
```

### How it is written

A {class}`~pie_extended.composite_tagger.CompositeTagger` has several engines, and each task is given by one of them.
They are written as the other models (`<name,tasks>`), in `Models` or in `--model_path`:

| Name | Engine | Gives |
|---|---|---|
| `soter:Zual/soter-mini` | the lemmatizer Sôtêr ({class}`~pie_extended.soter.SoterLemmatizer`) | `lemma` |
| `soter:Zual/soter-mini#proiel` | the same, with the lemmas of the convention of PROIEL (`#ptnk`: PTNK) | `lemma` |
| `grc_perseus_sm`, any other name | a spaCy pipeline ({class}`~pie_extended.spacy_tagger.SpacyTagger`) | `lemma`, `pos`, `tag`, `morph` |

So `grc_soter` is only this, in `pie_extended/models/grc_soter/__init__.py`:

```python
Backend = "composite"
Models = "<soter:Zual/soter-mini,lemma><grc_perseus_sm,pos>"
```

and any other combination is a `--model_path` away, with no code to change, for `grc_soter` as for `grc_grecy`. For
example the lemmas of PROIEL, and the morphology of the pipeline as well:

```bash
pie-extended tag grc_grecy demo.txt --model_path "<soter:Zual/soter-mini#proiel,lemma><grc_proiel_sm,pos,morph>"
```

The conventions of lemmatization differ between the treebanks: Sôtêr gives the one of Perseus (the entries of the LSJ), and
restores the other ones from a table of its repository. The verb of `εἶπεν` is `εἶπον` for Perseus and `λέγω` for PROIEL:
with `#proiel` you get `λέγω`.

`get_tagger` makes a `CompositeTagger` when the model has `Backend = "composite"`, or when the tasks of a spaCy model come
from several entries. A task given by two engines is an error, and is found before anything is loaded.

**Only what is asked for is loaded.** The columns that you ask for decide which engines are needed:
`--tasks pos` never loads Sôtêr, and `--tasks lemma` never loads spaCy.

### What the combination gives

Against the treebank of Perseus (400 sentences of the dev set, the tokens are the gold ones for every engine, CPU):

| | Lemma | UPOS |
|---|---|---|
| Sôtêr mini | **94.6%** | |
| `grc_perseus_sm` (light) | 92.8% | 81.6% |
| `grc_perseus_trf` (default of `grc_grecy`) | 93.5% | **89.6%** |
| `grc_soter`: lemma of Sôtêr, part of speech of `grc_perseus_sm` | **94.6%** | 81.6% |

The lemma is better with Sôtêr, and the part of speech is **8 points worse** with the light pipeline than with the
transformer, and less steady on rare forms: the light pipeline calls the elided `διʼ` an adjective, with a right lemma.
Choose the pipeline of the part of speech accordingly (`--model_path "<soter:Zual/soter-mini,lemma><grc_perseus_trf,pos>"`
puts the transformer back). The lemma is also the slow part: about 4 ms for a token (12 threads), ten times the whole of the
light pipeline. Take the numbers with care: these treebanks are data of the pipelines, and only the *differences* matter.

### Each engine reads its own apostrophe

The engines do not agree on the apostrophe of an elision (`δι᾽`), and this was measured on the 90 elided words of PROIEL:

| Apostrophe given to the engine | Sôtêr: lemma right | GreCy: lemma right |
|---|---|---|
| U+2019 `’` (as in the treebanks) | **100%** | 57% |
| ASCII `'` | 89% | |
| U+02BC `ʼ` | 46% | **100%** |

The tokenizer gives U+02BC (GreCy needs it), so Sôtêr converts every apostrophe to U+2019, and the text to NFC (it works
on bytes, and gives gibberish for decomposed accents), **inside** the engine: whichever tokenizer a model uses, each engine
gets what it was trained on. Your spelling stays in `token`.

### What it needs

- `transformers` (`pip install "pie-extended[soter]"`, with spaCy and GreCy for the part of speech);
- Sôtêr is downloaded from Hugging Face the first time (7.5 MB, in `~/.cache/huggingface`, or `HF_HOME`). With
  `HF_HUB_OFFLINE=1` nothing is downloaded: run `pie-extended install-addons grc_soter` first;
- Sôtêr only gives `lemma`. Two GreCy pipelines cannot be combined (see above): the spaCy engine of a combination is one;
- the options of Sôtêr (the context of 8 words, the batch, the device) are those of
  {class}`~pie_extended.soter.SoterLemmatizer`. `--device cuda` was not tried.
