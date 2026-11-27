# Pie Extended

**Pie Extended** is an extension for [Pie](https://github.com/emanjavacas/pie) (it uses
[PaPie](https://github.com/lascivaroma/PaPie), a fork of Pie) that turns trained models into tools one can use on raw
text, with the pre-processing and post-processing they were trained with.

Pie is a wonderful tool to train models. And most of the time, it will be enough. What Pie Extended proposes is to
provide you with the necessary tools to *share* your models with customized pre- and post-processing, so that the
person who gets the model tags a text in one command and gets the output the authors intended.

## What it does

A model of Pie Extended is a package made of the model files and of the code around them. The code is a pipeline:

```text
  your text
      │
      ▼
  1. data iterator    normalization, sentence and word tokenization,
      │               exclusion of the tokens that must not be tagged
      ▼
  2. tagger           the model(s), then the disambiguation
      │
      ▼
  3. processor        rename and merge columns, apply rules, split enclitics, SpaceAfter
      │
      ▼
  4. formatter        TSV
```

You can customize each of these steps:

- the **normalization** of your text (spelling variants, abbreviations, references that must not reach the model),
- the **sentence and word tokenization**,
- which tokens are **excluded** from tagging and given back untouched (punctuation, references...),
- the **disambiguation** of what the model predicts (for example with the help of a lexicon),
- the **post-processing** of the predictions: rename, merge columns (morphological features into one `morph`), apply
  rules, split enclitics...
- the **output formatting**.

On top of that, every model gets for free:

- `--tasks lemma,pos`: ask only for some of the columns. The models (and the decoders) that are not needed are not
  loaded nor run;
- a `SpaceAfter` column, that tells whether a token is followed by a space in your text, to rebuild it;
- quantization and an embedding cache, to run on a CPU.

A model does not have to be a Pie model: a [spaCy pipeline](backends.md) can be put behind
the same processing pipeline.

(vocabulary)=
## Vocabulary

A few words mean different things depending on the type of model, so here is how they are used in this documentation.

**Model**
: What you ask the command for (`lasla`, `grc_grecy`): a Python package made of the files of the model, and of the code
  around it.

**Backend**
: What runs the predictions: **Pie** (the model is a set of files, one network per task), **spaCy** (the model is a
  spaCy pipeline) or **composite** (each task comes from the engine that is best at it: the lemma from a lemmatizer, the
  part of speech from a spaCy pipeline). See {doc}`backends`.

**Tagger**
: The Python object that runs the model on tokens: `ExtensibleTagger` (Pie) or `SpacyTagger` (spaCy).

**Pipeline**: two different things
: *The pipeline* of Pie Extended is the processing: a data iterator (it tokenizes) and a processor (it builds the columns
  of the output). It is what `get_pipeline` gives, and it does not depend on the backend. A *spaCy pipeline* is a spaCy
  model, such as `grc_perseus_trf`: it is what the spaCy backend runs. When it is the latter, the documentation says
  *spaCy pipeline*.

**Task** and **column**
: A *task* is what a model computes (`lemma`, `Case`). A *column* is what is written (`lemma`, `morph`, that merges
  several tasks, `treated`, `SpaceAfter`). `--tasks` and `get_tagger(tasks=...)` take **columns**: Pie Extended works out
  which tasks, and so which models, are needed. `add_model` and the constructor of a tagger take **tasks**.

| | Pie model | spaCy model |
|---|---|---|
| What *the model* is | files (`.tar`), one for each task | the name of a spaCy pipeline |
| What `--model_path` takes | files and tasks: `"<lemma.tar,lemma><pos.tar,pos>"` | the name: `grc_proiel_sm` (or `"<grc_proiel_sm,lemma,pos>"`) |
| What `pie-extended download` does | fetches the files | nothing |
| What `pie-extended install-addons` does | nothing, or what the model needs (`hy_xcl`) | installs the spaCy pipeline |

## Quick start

```bash
pip install pie-extended --extra-index-url https://download.pytorch.org/whl/cpu
pie-extended download lasla
echo "Arma uirumque cano, Troiae qui primus ab oris." > text.txt
pie-extended tag lasla text.txt --tasks lemma,pos --no-space-after
cat text-pie.txt
```

```text
token       lemma   pos
Arma        arma    NOMcom
uirumque    uir     NOMcom
{uirumque}  que     CON
cano        cano    ADJqua
,           ,       PUNC
Troiae      Troia   NOMpro
qui         qui1    PROrel
primus      primus  ADJord
ab          ab      PRE
oris        ora     NOMcom
.           .       PUNC
```

`uirumque` is two rows: the enclitic `que` is split off, as the model of Latin (`lasla`) was trained to.

## Where to go next

```{toctree}
:maxdepth: 2
:caption: Contents

install
tagger
api-usage
backends
api/index
models
citation
```

- {doc}`install`: install the package and the models;
- {doc}`tagger`: tag files from a terminal;
- {doc}`api-usage`: tag texts from Python, build a pipeline, add a model;
- {doc}`backends`: Pie and spaCy backends, change the pipeline of a model, add a spaCy model;
- {doc}`api/index`: reference of the classes and functions;
- {doc}`models`: the available models, and what is specific to each;
- {doc}`citation`: how to cite Pie Extended and the models.
