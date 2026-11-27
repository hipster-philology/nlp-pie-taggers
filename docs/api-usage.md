# API usage

Everything the command line does is available from Python, so that you can tag texts in your own scripts, get the
annotations as dictionaries, and build your own pipelines. This page goes from the simplest call to adding a model;
the {doc}`api/index` lists every class and function.

## Tag a text

Two objects are needed. The **tagger** holds the models (it is loaded once, which is slow). The **pipeline** is made of
a data iterator, that cuts the text into sentences and words, and of a processor, that builds the columns from what the
tagger predicts (it is cheap and can be reused). This is the processing pipeline of Pie Extended, not a spaCy pipeline:
see the {ref}`vocabulary <vocabulary>`.

```python
from pie_extended.cli.utils import get_tagger, get_pipeline

text = "Arma uirumque cano, Troiae qui primus ab oris."

tagger = get_tagger("lasla", batch_size=16, device="cpu")
iterator, processor = get_pipeline("lasla", tagger)

for token in tagger.tag_str(text, iterator=iterator, processor=processor)[:3]:
    print(token)
```

```python
{'form': 'Arma', 'lemma': 'arma', 'pos': 'NOMcom', 'morph': 'Case=Acc|Numb=Plur', 'Dis': '_', 'treated': 'Arma', 'SpaceAfter': '_'}
{'form': 'uirumque', 'lemma': 'uir', 'pos': 'NOMcom', 'morph': 'Case=Acc|Numb=Sing', 'Dis': '_', 'treated': 'uirumque', 'SpaceAfter': 'No'}
{'lemma': 'que', 'treated': 'uirumque', 'morph': 'MORPH=empty', 'pos': 'CON', 'form': '{uirumque}', 'Dis': '_', 'SpaceAfter': '_'}
```

`tag_str` returns a list with one dictionary per output line. `form` is the token as written in your text. As on the
command line, one token can give several lines (here `uirumque` and its enclitic `que`).

{func}`~pie_extended.cli.utils.get_tagger` loads the models of a language. Besides the name of the model, it takes:

`device`, `batch_size`
: Where the models run (`"cpu"` or `"cuda"`), and how many sentences are tagged together.

`tasks`
: The **columns** you want, for example `["lemma", "pos"]`. The models that are not needed to give them are not loaded.
  (A tagger made by hand takes *tasks*, what a model computes: see {doc}`backends`.)

`quantize`, `cache`, `cache_size`, `num_threads`
: Speed and memory, see {doc}`tagger`.

`model_path`
: Another model than the one of the package. For a Pie model, its files and tasks:
  `"<file.tar,lemma><other.tar,pos>"`. For a spaCy model, the name of the pipeline is enough:
  `model_path="grc_proiel_sm"` (see {doc}`backends`).

## Choose the columns

```python
tagger = get_tagger("lasla", tasks=["lemma", "pos"])
iterator, processor = get_pipeline("lasla", tagger, space_after=False)
```

Pass the **same tagger** to {func}`~pie_extended.cli.utils.get_pipeline`: it knows which columns were asked for and
makes the pipeline output only these ones (and a `SpaceAfter` column, unless `space_after=False`).

## Stream the result

`tag_str` waits for the whole text. For long texts, or to write a file, get the result as it comes:

`iter_tag`
: Yields the lines of the TSV, header first (as the command line writes them).

```python
import sys

for line in tagger.iter_tag(text, iterator, processor=processor):
    sys.stdout.write(line.replace("\r\n", "\n"))
```

```text
token       lemma  pos
Arma        arma   NOMcom
uirumque    uir    NOMcom
{uirumque}  que    CON
cano        cano   ADJqua
,           ,      PUNC
Troiae      Troia  NOMpro
...
```

`iter_tag_token`
: Yields one dictionary per output line, like `tag_str`, but lazily. With `empty_token_on_sent_break=True`, a `None`
  tells when a sentence ends.

```python
tagger = get_tagger("lasla", tasks=["lemma"])
iterator, processor = get_pipeline("lasla", tagger, space_after=False)

for token in tagger.iter_tag_token("Arma cano. Troiae qui.", iterator, processor, empty_token_on_sent_break=True):
    print(token)
```

```python
{'form': 'Arma', 'lemma': 'arma', 'pos': 'NOMcom', 'Dis': '_', 'treated': 'Arma'}
{'form': 'cano', 'lemma': 'cano', 'pos': 'VER', 'Dis': '_', 'treated': 'cano'}
{'form': '.', 'lemma': '.', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--', 'Dis': '_'}
None
{'form': 'Troiae', 'lemma': 'Troia', 'pos': 'NOMpro', 'Dis': '_', 'treated': 'Troiae'}
...
```

```{note}
The dictionaries are the ones of the model, **before** the choice of the columns: here `pos` and `Dis` are present
although only `lemma` was asked for, as the model needs them. The columns of the TSV (`processor.tasks`) are the ones that
were asked for.
```

`tag_file`
: Reads a file and writes the TSV next to it (`text.txt` gives `text-pie.txt`), as the command does. See
  {func}`~pie_extended.cli.utils.tag_file`.

## Tag many texts

The tagger and the pipeline are made to be reused: load them once, then tag as many texts as you want. The pipeline
forgets everything about a text before the next one.

```python
tagger = get_tagger("lasla")
iterator, processor = get_pipeline("lasla", tagger)

for path in paths:
    with open(path, encoding="utf-8") as f:
        annotations = tagger.tag_str(f.read(), iterator=iterator, processor=processor)
```

## Rebuild the text with `SpaceAfter`

Every token is given the `SpaceAfter` value: `No` if the next token is written right after it, `_` if a space (or the end
of the text) follows. To write a text back:

```python
annotations = tagger.tag_str(text, iterator=iterator, processor=processor)
rebuilt = "".join(a["form"] + ("" if a["SpaceAfter"] == "No" else " ") for a in annotations)
```

It cannot be known from pre-tokenized text: `no_tokenizer=True` raises an error unless the pipeline was built with
`space_after=False`.

## Build a pipeline by hand

{func}`~pie_extended.cli.utils.get_pipeline` is a shortcut. A model's `get_iterator_and_processor()` gives the two
parts, and you can make your own. The pipeline is:

```text
text ─▶ tokenizer ─▶ DataIterator ─▶ tagger ─▶ (disambiguator) ─▶ processor ─▶ dictionaries ─▶ formatter ─▶ TSV
```

- a {class}`~pie_extended.pipeline.tokenizers.simple_tokenizer.SimpleTokenizer` cuts the text into sentences and words;
  a {class}`~pie_extended.pipeline.tokenizers.memorizing.MemorizingTokenizer` also remembers what it changed;
- a {class}`~pie_extended.pipeline.iterators.proto.DataIterator` uses it, and decides which tokens are excluded from
  tagging (they are put back in the output);
- a **processor** turns what the tagger predicts into dictionaries. Processors are *chained*: each one wraps the
  previous one and changes its output.

To try this without any model, use the fake tagger, that gives `lemma0`, `pos0`, `lemma1`... to the tokens it receives:

```python
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.tokenizers.simple_tokenizer import SimpleTokenizer
from pie_extended.pipeline.postprocessor.proto import RenamedTaskProcessor
from pie_extended.testing_utils import FakeAutoTag

iterator = DataIterator(tokenizer=SimpleTokenizer(), exclude_patterns=[r"^\W+$"])  # punctuation is not tagged
processor = RenamedTaskProcessor({"pos": "POS"})                                   # a column is renamed
tagger = FakeAutoTag(["lemma", "pos"])

for token in tagger.tag_str("Salve, mundus.", iterator=iterator, processor=processor):
    print(token)
```

```python
{'form': 'Salve', 'lemma': 'lemma0', 'POS': 'pos0'}
{'form': ',', 'lemma': '_', 'POS': '_'}
{'form': 'mundus', 'lemma': 'lemma1', 'POS': 'pos1'}
{'form': '.', 'lemma': '_', 'POS': '_'}
```

### Processors

The processors of `pie_extended.pipeline.postprocessor` ({doc}`api/pipeline`) can be chained in any order:

| Processor | What it does |
|---|---|
| `ProcessorPrototype` | Gives the predictions as they are |
| `RenamedTaskProcessor` | Renames columns (Pie refuses a dot in a task name: `PERS.` is `PERS` for it) |
| `GlueProcessor` | Merges columns into one (`Case`, `Numb`... into `morph`) |
| `MemoryzingProcessor` | Adds the `treated` column: what the model saw, when the tokenizer changed the word |
| `RuleBasedProcessor` | Applies *your* rules to every line |
| `SplitterPostProcessor` | Splits a line in several (enclitics: `uirumque` -> `uir`, `que`) |
| `SpaceAfterProcessor` | Adds the `SpaceAfter` column. Must be the outermost one |

Rules are written by subclassing {class}`~pie_extended.pipeline.postprocessor.rulebased.RuleBasedProcessor`:

```python
from typing import Dict
from pie_extended.pipeline.postprocessor.rulebased import RuleBasedProcessor

class Numbers(RuleBasedProcessor):
    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        if annotation["form"].isdigit():
            annotation["POS"] = "NUM"
        return annotation

processor = Numbers(head_processor=RenamedTaskProcessor({"pos": "POS"}))
iterator = DataIterator(tokenizer=SimpleTokenizer())

for token in FakeAutoTag(["lemma", "pos"]).tag_str("anno 2024", iterator=iterator, processor=processor):
    print(token)
```

```python
{'form': 'anno', 'lemma': 'lemma0', 'POS': 'pos0'}
{'form': '2024', 'lemma': 'lemma1', 'POS': 'NUM'}
```

Wrap a processor in {class}`~pie_extended.pipeline.postprocessor.spacing.SpaceAfterProcessor` to get `SpaceAfter`:

```python
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.pipeline.postprocessor.spacing import SpaceAfterProcessor

iterator = DataIterator(tokenizer=SimpleTokenizer())
processor = SpaceAfterProcessor(ProcessorPrototype())

for token in FakeAutoTag(["lemma"]).tag_str("Salve, mundus.", iterator=iterator, processor=processor):
    print(token)
```

```python
{'form': 'Salve', 'lemma': 'lemma0', 'SpaceAfter': 'No'}
{'form': ',', 'lemma': 'lemma1', 'SpaceAfter': '_'}
{'form': 'mundus', 'lemma': 'lemma2', 'SpaceAfter': 'No'}
{'form': '.', 'lemma': 'lemma3', 'SpaceAfter': '_'}
```

### Tokenizers

A tokenizer cuts the text with `sentence_tokenizer(text)`, which yields lists of words. A tokenizer that does not
output the words *as they are written* (it detaches a character from its word, for example, as the
{class}`Armenian one <pie_extended.models.hy_hye.tokenizer.ArmenianTokenizer>` does) must also tell how each token is
written, through `surface_tokens()`, so that `SpaceAfter` can be computed:

```python
from pie_extended.models.hy_hye.tokenizer import ArmenianTokenizer

tokenizer = ArmenianTokenizer()
print(list(tokenizer.sentence_tokenizer("Մի՞թե այդպես է։")))
print(tokenizer.surface_tokens())
```

```python
[['Միթե', '՞', 'այդպես', 'է', '։']]
['Մի՞թե', '', 'այդպես', 'է', '։']
```

The question mark was written *inside* `Մի՞թե`: it becomes a token of its own, written nowhere (an empty string).

## Add a model

A model is a Python package in `pie_extended/models/`. Call it `foo`:

1. Create the package `pie_extended/models/foo/`.
2. Add `"foo"` to the list `modules` of `pie_extended/models/__init__.py`. **Without this, the command does not see
   the model.**
3. In `pie_extended/models/foo/__init__.py`, define:

   `DESC`
   : A {class}`~pie_extended.utils.Metadata`: name, language (an ISO 639 code when there is one), authors, description
     and a link. It feeds `pie-extended list` and the table of {doc}`models`.

   `DOWNLOADS`
   : The files to download, a list of {class}`~pie_extended.utils.File` (URL, local name). `[]` if there is nothing.

   `Models`
   : A string telling which file gives which task: `<file,task,task><file,task>`. Use
     {func}`~pie_extended.utils.get_path` for the files.

   ```python
   from pie_extended.utils import Metadata, File, get_path

   DESC = Metadata(
       "Foo",
       "foo",                                       # language
       ["Author 1", "Author 2"],
       "A readable description",
       "A link to more information"
   )

   DOWNLOADS = [
       File("https://example.org/lemma.tar", "lemma.tar"),
       File("https://example.org/pos.tar", "pos.tar"),
   ]

   Models = "<{},lemma><{},pos>".format(
       get_path("foo", "lemma.tar"),
       get_path("foo", "pos.tar"),
   )
   ```

4. In `pie_extended/models/foo/imports.py`, define:

   `get_iterator_and_processor(max_tokens=256)`
   : Required. Returns the data iterator and the processor of the model.

   `addons()`
   : Optional. What `pie-extended install-addons` runs.

   `Disambiguator`
   : Optional. A {class}`~pie_extended.pipeline.disambiguators.proto.Disambiguator`, or an
     {class}`~pie_extended.utils.ObjectCreator` that builds one.

   ```python
   from pie_extended.pipeline.iterators.proto import DataIterator
   from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
   from pie_extended.pipeline.tokenizers.simple_tokenizer import SimpleTokenizer


   def get_iterator_and_processor(max_tokens=256):
       return DataIterator(tokenizer=SimpleTokenizer(), max_tokens=max_tokens), ProcessorPrototype()
   ```

5. Test it **without the model files**, with the fake tagger built from the `Models` string:

   ```python
   from pie_extended.cli.utils import get_model, get_imports
   from pie_extended.testing_utils import FakeAutoTag

   module = get_model("foo")
   tagger = FakeAutoTag.from_model_string(module.Models, batch_size=16)
   iterator, processor = get_imports(module).get_iterator_and_processor()
   print(tagger.tag_str("Un texte.", iterator=iterator, processor=processor))
   ```

For a short example, look at `pie_extended.models.dum` (no pre/post-processing), then `pie_extended.models.fro` (a
tokenizer, rules and merged columns) and `pie_extended.models.lasla` (enclitics and a disambiguator).
A model can also share the code of another: `frm` reuses `fro`'s `get_iterator_and_processor`.

### A disambiguator

Pie Extended comes with disambiguators built on lexicons
({mod}`~pie_extended.pipeline.disambiguators.lexicons`): a lexicon says, for a lemma, what to add to it (`qui1`,
`qui2`) depending on another annotation, usually the part of speech, so that the model does not have to learn it. The
lexicons are built from an annotated corpus (a TSV with the columns `lemma`, `pos` and `Dis`, the index of the
disambiguation) with `pie-extended build-lexicons pos corpus.tsv --prefix latin-`, which writes `latin-pos.json`,
`latin-straight.json` and `latin-needs.json`; `pie_extended.models.lasla.imports` shows how they are used.

You can also write your own.

A {class}`~pie_extended.pipeline.disambiguators.proto.Disambiguator` is called on each tagged sentence **before** the
processor, and can change the predictions. Latin, for example, uses a lexicon to decide between homographs. It receives
the sentence as `[(token, tags), ...]` and the list of the tasks, and gives the sentence back:

```python
from pie_extended.pipeline.disambiguators.proto import Disambiguator

class Copula(Disambiguator):
    required = ("lemma",)          # the tasks it needs: it is skipped if they were not asked for

    def __call__(self, sentence, tasks):
        lemma = tasks.index("lemma")
        return [
            (token, tuple("sum" if i == lemma and token == "est" else tag for i, tag in enumerate(tags)))
            for token, tags in sentence
        ]
```

To use it, give it to the tagger (a model does it with its `Disambiguator`, see above):

```python
tagger = FakeAutoTag(["lemma", "pos"])
tagger.disambiguation = Copula()

for token in tagger.tag_str("Roma est magna", iterator=DataIterator(tokenizer=SimpleTokenizer()),
                            processor=ProcessorPrototype()):
    print(token)
```

```python
{'form': 'Roma', 'lemma': 'lemma0', 'pos': 'pos0'}
{'form': 'est', 'lemma': 'sum', 'pos': 'pos1'}
{'form': 'magna', 'lemma': 'lemma2', 'pos': 'pos2'}
```

## Backends

A model does not have to run through Pie: a **backend** is what turns tokens into predictions, and a spaCy pipeline can
be put behind the same iterators, processors and options. {doc}`backends` explains how backends work, how to change the
pipeline of `grc_grecy` (`SpacyModel`), and how to add a model that runs a spaCy pipeline, or a task.

```python
tagger = get_tagger("grc_grecy", tasks=["lemma", "pos"])
iterator, processor = get_pipeline("grc_grecy", tagger, space_after=False)

text = "ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν."
for line in tagger.iter_tag(text, iterator, processor=processor):
    sys.stdout.write(line.replace("\r\n", "\n"))
```
