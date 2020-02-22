# Pie Extended

[![Build Status](https://travis-ci.org/hipster-philology/nlp-pie-taggers.svg?branch=master)](https://travis-ci.org/hipster-philology/nlp-pie-taggers)
[![Coverage Status](https://coveralls.io/repos/github/hipster-philology/nlp-pie-taggers/badge.svg?branch=master)](https://coveralls.io/github/hipster-philology/nlp-pie-taggers?branch=master)
![PyPI](https://img.shields.io/pypi/v/pie-extended?style=flat-square)

Extension for [`pie`](https://github.com/emanjavacas/pie) to include taggers with their models and pre/postprocessors.

Pie is a wonderful tool to train models. And most of the time, it will be enough. What `pie_extended` is proposing here 
is to provide you with the necessary tools to share your models with customized pre- and post-processing.

The current system provide an easier access to adding **customized**:
- normalization of your text,
- sentence tokenization,
- word tokenization,
- disambiguation,
- output formatting

## Install

To install, simply do `pip install pie-extended`. Then, look at all available models.

## Run on terminal

But on top of that, it provides a quick and easy way to use others models ! For example, in a shell :

```bash
pie-extended download lasla
pie-extended install-addons lasla
pie-extended tag laslsa your_file.txt
```

will give you access to all you need !

## Python API

You can run the lemmatizer in your own scripts and retrieve token annotations as dictionaries:

```python
from typing import List
from pie_extended.cli.sub import get_tagger, get_model, download

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
from pie_extended.models.lasla import get_iterator_and_processor
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

ToDo: Documentation

## Warning

This is an extremely early build, subject to change here and there. But it is functional !