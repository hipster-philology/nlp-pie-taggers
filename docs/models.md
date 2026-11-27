# Models

The table is generated from the code of the package, so it always lists the models you have installed. Each model has
a *More* link to its documentation or its publication: please cite it when you use it (see {doc}`citation`).

```{include} _generated/models_table.md
```

Every model is a Python package: the files of the model, and the code that tokenizes the text and builds the output.
{doc}`install` tells how to download them, and {doc}`api-usage` how to add yours.

## What to know about each model

### Latin (`lasla`)

Nine Pie models, one per task (`lemma`, `pos`, `Case`, `Numb`, `Gend`, `Deg`, `Mood_Tense_Voice`, `Person`, `Dis`).
The morphological tasks are merged in one `morph` column.

- The text is **normalized** before tagging (`u`/`v`, `i`/`j`, numbers, abbreviations): `token` is your spelling,
  `treated` what the model saw.
- **Enclitics** (`-que`, `-ne`, `-ue`...) are split: `uirumque` gives two lines.
- Homographs are **disambiguated** with lexicons (`sum1`, `qui1`), that are downloaded with the model. The `Dis` column
  tells how a decision was taken. If you ask for columns without `lemma`, the disambiguation is skipped.

### French (`fro`, `frm`, `fr`, `freem`) and Middle Dutch (`dum`)

Old French (`fro`), Middle French (`frm`), Classical French (`fr`) and Early Modern French (`freem`). Their
morphological tasks (`MODE`, `TEMPS`, `PERS`, `NOMB`, `GENRE`, `CAS`, and `DEGRE`) are merged in `morph`. `fro`, `frm`
and `freem` share the same post-processing. `dum` has only `lemma` and `pos` and cuts the text on spaces.

### Ancient Greek (`grc`, `grc_grecy`)

`grc` is a Pie model with ten tasks. `grc_grecy` runs the [GreCy](https://github.com/jmyerston/greCy) spaCy pipelines
instead: see {doc}`tagger` for how to install and choose one. Its tasks are `lemma`, `pos`, `tag` and `morph` (UD
features). Elisions (`δι'`) are kept in their word, and the apostrophe is given to the model as U+02BC, as GreCy
requires: your spelling stays in `token`.

### Occitan (`occ_cont`) and Old Castilian (`osp`)

`occ_cont` has a tokenizer for contemporary Occitan. `osp` is only a **proof of concept**: its models are placeholders,
do not rely on its output.

### Armenian (`hy_hye`, `hy_hyw`, `hy_xcl`)

Eastern (`hye`), Western (`hyw`) and Classical (`xcl`) Armenian are the Pie models of Vidal-Gorène, Tomeh and
Khurshudyan (2024), trained on the [Universal Dependencies](https://universaldependencies.org/) treebanks. There is one
Pie model per task, 25, 30 and 15 of them: `--tasks lemma,pos` loads only two.

They expect **tokenized input like the treebanks**, so they share a tokenizer
({class}`~pie_extended.models.hy_hye.tokenizer.ArmenianTokenizer`) that does the same:

- punctuation (`։ ՝ « » ( ) , ...`) and hyphens are tokens of their own;
- the marks written on a vowel (`Մի՞թե`, `թե՛`) become a token after their word (`Միթե`, `՞`). `SpaceAfter` is `No`
  for the word, since the mark was written inside it;
- numbers (`1.000`) and ellipsis stay in one piece, the Western apostrophe stays on its clitic (`կ՚`, `ուզեմ`);
- sentences end with `։ : ! ? …`, not with a dot (initials, abbreviations and numbers).

On the dev sets of the Eastern and Western treebanks, the tokenizer gives exactly the words of the treebank for 99.5% and
99.4% of the sentences.

```{admonition} Classical Armenian: learn the clitics first
:class: important
The treebank of Classical Armenian makes the clitics words of their own (`զմեղս` gives `զ`, `մեղս`; `յանապատին` gives
`յ`, `անապատի`, `ն`) and the model expects them cut. No rule can do it (many words begin with `զ` or end with `ն`),
so a small model learns where the treebank cuts:

    pie-extended install-addons hy_xcl

It downloads the treebank, learns in a few seconds and keeps 160 KB. On the test set of the treebank, the cuts are found
with an F1 of 97.3%, and 90% of the sentences have exactly the words of the treebank (13% without it).

The treebank is licensed CC BY-NC-SA 4.0: what is learned **stays on your machine**, it is not distributed with
Pie Extended. Without this step the clitics are not split, and a warning says so.
```

The Eastern and Western treebanks (CC BY-SA 4.0) are the source of a few example sentences used to test the tokenizer
(`tests/data/armenian_ud_sample.json`).
