# Tagger usage

`pie-extended` is the command that tags files from a terminal. It has six commands:

| Command | What it does |
|---|---|
| `pie-extended list` | Lists the available models (add `--full` for authors, description and link) |
| `pie-extended download MODEL` | Downloads the files of a model |
| `pie-extended install-addons MODEL` | Installs what a model needs besides its files, if anything |
| `pie-extended tag MODEL FILE...` | Tags one or several files |
| `pie-extended details MODEL` | Prints the characters the model knows |
| `pie-extended build-lexicons CATEGORY FILE...` | Builds the lexicons of a disambiguator from an annotated corpus (see {doc}`api-usage`) |

```text
$ pie-extended list
Available Models:
    - lasla (lat) : LASLA-ENC
    - fro (fro) : Ancien Francais (ENC)
    - fr (fr) : Français classique et moderne
    - frm (frm) : Moyen Français (ENC)
    ...
```

## Tag a file

```bash
pie-extended download lasla
pie-extended install-addons lasla
pie-extended tag lasla text.txt
```

The result is written **next to the file**, with `-pie` before the extension: `text.txt` gives `text-pie.txt`. You can
give as many files as you want, the model is loaded once for all of them. If a file fails, the next ones are still
tagged: the command only stops after `--allow-n-failures` failures (5 by default), and `--debug` stops at the first
one and shows the error.

### The output

The output is a TSV file: the columns are separated by tabs (shown aligned here). The first line names the columns, and
there is one line per token:

```text
token       lemma  pos     morph               Dis  treated   SpaceAfter
Arma        arma   NOMcom  Case=Acc|Numb=Plur  _    Arma      _
uirumque    uir    NOMcom  Case=Acc|Numb=Sing  _    uirumque  No
{uirumque}  que    CON     MORPH=empty         _    uirumque  _
```

Lines end with `\r\n`. The columns are the ones the model predicts (`lemma`, `pos`, `morph`... they depend on the
model), plus:

`treated`
: What the model actually saw: some models normalize the text before tagging it (`u`/`v`, `i`/`j`, accents, apostrophes...)
  and give your original spelling back in `token`. Only models that normalize have this column.

`SpaceAfter`
: `No` if the next token is written right after this one in your text, `_` otherwise. See [below](#rebuild-the-text).

A token can take **several lines**: `uirumque` is cut in `uir` and the enclitic `que` because the model of Latin was
trained that way. The first line gets `SpaceAfter` = `No`, as the second one is written right after it.

Punctuation and other excluded tokens (references, tags...) are not tagged: they are given back with a fixed
value (`PUNC`, `_`...) chosen by the model.

## Choose the columns

`--tasks` asks for some of the columns only:

```bash
pie-extended tag lasla text.txt --tasks lemma,pos
```

```text
token     lemma  pos     SpaceAfter
Arma      arma   NOMcom  _
uirumque  uir    NOMcom  No
...
```

This is not only a display option. A Pie model is one network *per task* (25 for Eastern Armenian, 9 for Latin...): the
ones that are not needed are **not loaded** and not run, which saves time and memory. The names are the ones of
the columns, case does not matter, and an unknown name gives the list of the valid ones.

## Rebuild the text

`SpaceAfter` is on by default. It lets you write your text back from the tokens: `token` followed by a space unless
`SpaceAfter` is `No`. Use `--no-space-after` to remove it:

```bash
pie-extended tag lasla text.txt --tasks lemma,pos --no-space-after
```

```{note}
`SpaceAfter` cannot be computed from text that is already tokenized: the spaces were lost. `--no-tokenizer` (below)
therefore requires `--no-space-after`.
```

## Tokenization and excluded tokens

By default, the model decides how the text is cut into sentences and words, and which tokens must not be tagged.
You can change this:

`--no-tokenizer`
: Your text is already tokenized: **one word per line, and an empty line between two sentences**. Use it with
  `--no-space-after`.

`--add-pattern REGEXP`
: Tokens that match this regular expression are excluded from tagging. Can be given several times.

`--reset-exclude-patterns`
: Forget the patterns that the model excludes by default (usually punctuation and references).

`--max-tokens N`
: Longest sentence given to the model (64 by default): longer ones are cut. Long sentences are slow and often bad.

## Speed and memory

On a CPU, the models are quantized (int8) and a cache remembers the representation of the words already seen,
which makes tagging faster and the models lighter without noticeable change of the output:

`--batch_size N`
: Sentences tagged together (16 by default).

`--no-quantize`, `--no-cache`, `--cache-size N`
: Turn quantization (CPU only) and the cache off, or change the size of the cache.

`--num-threads N`
: Number of threads used by PyTorch.

`--device cuda`
: Run on a GPU (quantization is then turned off, with a warning).

## Run another model

`--model_path` runs another model than the one of the package, **without touching any code**. For a Pie model, give
the files and what each one gives, in groups `<file,task,task...>`:

```bash
pie-extended tag lasla text.txt --model_path "<my_lemma.tar,lemma><my_pos.tar,pos>"
```

For a model that runs a spaCy pipeline (`grc_grecy`), the name of the pipeline is enough: see below.

## Other tools (spaCy and GreCy)

A model does not have to run through Pie: a spaCy pipeline can be put behind the same iterators, processors and
options (`--tasks`, `SpaceAfter`...). `grc_grecy` is the first one: Ancient Greek with
[GreCy](https://github.com/jmyerston/greCy). How this works, and how to change or add a spaCy model in the code, is in
{doc}`backends`.

```bash
pip install "pie-extended[grecy]"       # spaCy, spacy-transformers and GreCy
pie-extended install-addons grc_grecy   # installs the spaCy pipeline of the model: grc_perseus_trf (about 480 MB)
```

The pipeline of `grc_grecy` is `grc_perseus_trf`: the GreCy pipeline for the Perseus treebank, with a transformer.
It is the heaviest of the family (see below for lighter ones). It is set in the code of the model, see
{ref}`change-the-pipeline` if you want another one for everybody.

The tasks are `lemma`, `pos` (universal POS), `tag` (language specific POS) and `morph` (UD features). Here, lemma and
POS only, and no `SpaceAfter`:

```bash
echo "ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν." > demo.txt
pie-extended tag grc_grecy demo.txt --tasks lemma,pos --no-space-after
cat demo-pie.txt
```

```text
token  lemma  pos
ἐν     ἐν     ADP
ἀρχῇ   ἀρχή   NOUN
ἦν     εἰμί   AUX
ὁ      ὁ      DET
λόγος  λόγος  NOUN
,      ,      PUNCT
καὶ    καί    CCONJ
```

### Another lemmatizer: Sôtêr

`grc_soter` takes the lemma from Sôtêr, a very small lemmatizer of Ancient Greek, and the part of speech from a light
spaCy pipeline. The two do not come from the same tool, and it is explained on the page of the {doc}`backends`:

```bash
pip install "pie-extended[soter]"
pie-extended install-addons grc_soter
pie-extended tag grc_soter demo.txt --tasks lemma,pos
```

### Run a specific pipeline

`pie-extended tag grc_grecy` runs the pipeline of the model (`grc_perseus_trf`). To run another one for a run, install it
and give its name to `--model_path`:

```bash
pie-extended tag grc_grecy demo.txt --model_path grc_proiel_sm
```

That is all: the code is not touched, and you get the same columns as with the default (`lemma`, `morph`, `pos`, `tag`),
`--tasks` and the other options work as usual. If the pipeline is not installed, the command says so.

GreCy provides six pipelines: `grc_perseus_{sm,lg,trf}` and `grc_proiel_{sm,lg,trf}`, trained on two treebanks (Perseus
and PROIEL) in three sizes: `sm` (small, a 43 MB download), `lg` (with word vectors, 264 MB) and `trf` (transformer,
476 MB). Install the one you want from its wheel, for example the small PROIEL one:

```bash
pip install "https://github.com/jmyerston/greCy/releases/download/v3.8.2/grc_proiel_sm-3.8.2-py3-none-any.whl"
```

`python -m grecy install grc_proiel_sm` does the same, but it needs `pip` in your environment. (The transformer ones
also need `spacy-transformers`, which is in the extra `grecy`.)

The treebanks do not follow the same conventions: `pos` is the universal part of speech, but `tag` and `morph` follow
the ones of the treebank, so changing the pipeline changes the **values** you get. The article `ὁ`, with the small
pipelines:

| Pipeline | `pos` | `tag` | `morph` |
|---|---|---|---|
| `grc_proiel_sm` | `DET` | `S-` | `Case=Nom\|Definite=Def\|Gender=Masc\|Number=Sing\|PronType=Dem` |
| `grc_perseus_sm` | `DET` | `P-` | `Case=Nom\|Gender=Masc\|Number=Sing` |

To offer fewer tasks than the model does, use the full syntax, with the tasks after the name of the pipeline:
`--model_path "<grc_proiel_sm,lemma,pos>"` (`--tasks lemma,pos` does the same for one run).

```{warning}
Two different GreCy pipelines cannot be loaded in the same Python process (spaCy refuses to register their components
twice): use one pipeline per run. You can *install* several, but do not ask spaCy for the list of the installed
pipelines (`spacy.util.get_installed_models()` fails then): use `pip list | grep grc`.
```

If a pipeline is not installed, the command says so and how to install it: `pie-extended install-addons MODEL` installs
the pipeline that a model runs by default, any other one has to be installed with pip.

## Reference of the commands

This part is generated from the code of the command.

```{eval-rst}
.. click:: pie_extended.cli.main:pie_ext
   :prog: pie-extended
   :nested: full
```
