# Installation

## Requirements

- Python **3.12 or later** (tested on 3.12, 3.13 and 3.14);
- [PaPie](https://github.com/lascivaroma/PaPie) (a fork of Pie) 0.6.1 or later, installed with Pie Extended. It brings
  [PyTorch](https://pytorch.org/): this is what decides which Python versions can be used.

## Install the package

```bash
pip install pie-extended
```

```{admonition} No GPU, no CUDA?
:class: tip
By default, pip downloads a PyTorch built for CUDA, which is large. If you only have a CPU (or if you are in doubt),
ask for the CPU build:

    pip install pie-extended --extra-index-url https://download.pytorch.org/whl/cpu
```

This gives you the `pie-extended` command and the `pie_extended` Python package. Check it with:

```bash
pie-extended list
```

### Optional dependencies

| Extra | Command | What for |
|---|---|---|
| `grecy` | `pip install "pie-extended[grecy]"` | Models run through spaCy (`grc_grecy`, see {doc}`tagger`) |
| `docs` | `pip install "pie-extended[docs]"` | Build this documentation |

## Install the models

The files of the models are not part of the package: they are downloaded on demand, in the folder `downloads` of
the package, **for each model you need**.

```bash
pie-extended download lasla        # the files of the model
pie-extended install-addons lasla  # what the model needs besides (lexicons, spaCy pipeline, ...), if anything
```

Which command does what depends on the model:

- `download` fetches the files listed by the model (a Pie model is one file per task: `lemma.tar`, `pos.tar`...);
- `install-addons` runs the extra installation of the model, if it has one. For example `hy_xcl` learns from a
  treebank how to split the clitics of Classical Armenian, and `grc_grecy` installs a spaCy pipeline.

{doc}`models` tells what each model needs.

```{admonition} A note on safety
:class: warning
A Pie model is a file produced by PyTorch, and PyTorch files can contain code. With **torch 2.6 or later** (the default
with a recent PaPie), loading refuses to run any code it finds. With torch 2.4 and 2.5, which PaPie still allows, it
does not: only download the models of authors you trust.
```

## Install the development version

Clone the repository, create an environment, and then:

```bash
pip install -e ".[docs]" --extra-index-url https://download.pytorch.org/whl/cpu
pip install pytest pytest-cov
pie-extended download lasla     # needed by some of the tests
pytest --doctest-modules tests pie_extended
```

Build this documentation with `make docs`: the result is in `docs/_build/html`
(`make docs-serve` serves it on <http://localhost:8000>).

## Release a new version

Releases are published on [PyPI](https://pypi.org/project/pie-extended/) by a workflow, when a tag is pushed:

1. change `version` in `pyproject.toml` and commit it;
2. `git tag vX.Y.Z` (the tag must be `v` followed by that version) and `git push origin vX.Y.Z`.

The workflow runs the tests on every supported Python, builds the package, checks that the tag is the version, and
publishes it. Nothing is published if one of these fails. No password is stored: PyPI trusts the workflow
(*trusted publishing*, set up once in the settings of the project on PyPI).
