# Pie Extended

[![Tests](https://github.com/hipster-philology/nlp-pie-taggers/actions/workflows/test.yml/badge.svg)](https://github.com/hipster-philology/nlp-pie-taggers/actions/workflows/test.yml)
[![Documentation](https://github.com/hipster-philology/nlp-pie-taggers/actions/workflows/docs.yml/badge.svg)](https://hipster-philology.github.io/nlp-pie-taggers/)
[![PyPI](https://img.shields.io/pypi/v/pie-extended?style=flat-square)](https://pypi.org/project/pie-extended/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3883589.svg)](https://doi.org/10.5281/zenodo.3883589)

Extension for [Pie](https://github.com/emanjavacas/pie) (through [PaPie](https://github.com/lascivaroma/PaPie)) to
include taggers with their models and pre/postprocessors: normalization, tokenization, disambiguation, output
formatting. The person who gets a model tags a text in one command and gets the output its authors intended.

**Documentation: <https://hipster-philology.github.io/nlp-pie-taggers/>**

## Quick start

Python 3.12 or later is needed.

```bash
pip install pie-extended --extra-index-url https://download.pytorch.org/whl/cpu   # the extra index: no GPU needed
pie-extended list                                  # the available models
pie-extended download lasla                        # the files of a model
pie-extended install-addons lasla                  # what it needs besides, if anything
pie-extended tag lasla your_file.txt --tasks lemma,pos
```

The output is written next to the file (`your_file-pie.txt`): a TSV with one line per token.

```text
token       lemma  pos     SpaceAfter
Arma        arma   NOMcom  _
uirumque    uir    NOMcom  No
{uirumque}  que    CON     _
cano        cano   ADJqua  No
```

From Python:

```python
from pie_extended.cli.utils import get_tagger, get_pipeline

tagger = get_tagger("lasla", tasks=["lemma", "pos"])
iterator, processor = get_pipeline("lasla", tagger)
print(tagger.tag_str("Arma uirumque cano", iterator=iterator, processor=processor))
```

## Models

Latin, Ancient Greek, Old, Middle, Classical and Early Modern French, Middle Dutch, Occitan, Old Castilian (placeholder)
and Eastern, Western and Classical Armenian. Some of them run through spaCy ([GreCy](https://github.com/jmyerston/greCy)).
The documentation lists them, with what is specific to each.

If you trained models and want some help sharing them with Pie Extended, open an issue :)

## Documentation

| | |
|---|---|
| [Presentation](https://hipster-philology.github.io/nlp-pie-taggers/) | What Pie Extended does |
| [Install](https://hipster-philology.github.io/nlp-pie-taggers/install.html) | The package and the models |
| [Tagger usage](https://hipster-philology.github.io/nlp-pie-taggers/tagger.html) | Tag files from a terminal |
| [API usage](https://hipster-philology.github.io/nlp-pie-taggers/api-usage.html) | Tag from Python, build a pipeline, add a model |
| [API](https://hipster-philology.github.io/nlp-pie-taggers/api/index.html) | Reference of the classes and functions |
| [Citation](https://hipster-philology.github.io/nlp-pie-taggers/citation.html) | How to cite the software and the models |

To build it yourself: `pip install -e ".[docs]"`, then `make docs` (the result is in `docs/_build/html`).

## Cite as

```bibtex
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

Please also cite the models you use: see [Citation](https://hipster-philology.github.io/nlp-pie-taggers/citation.html).
