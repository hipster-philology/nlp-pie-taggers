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

A model does not have to be a Pie model: a [spaCy pipeline](tagger.md#other-tools-spacy-and-grecy) can be put behind
the same pipeline.

## Quick start

```bash
pip install pie-extended --extra-index-url https://download.pytorch.org/whl/cpu
pie-extended download lasla
pie-extended install-addons lasla
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
api/index
models
citation
```

- {doc}`install`: install the package and the models;
- {doc}`tagger`: tag files from a terminal;
- {doc}`api-usage`: tag texts from Python, build a pipeline, add a model;
- {doc}`api/index`: reference of the classes and functions;
- {doc}`models`: the available models, and what is specific to each;
- {doc}`citation`: how to cite Pie Extended and the models.
