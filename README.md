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

But on top of that, it provides a quick and easy way to use others models ! For example, in a shell :

```bash
pie-extended download lasla
pie-extended install-addons lasla
pie-extended tag laslsa your_file.txt
```

will give you access to all you need !

## Warning

This is an extremely early build, subject to change here and there. But it is functional !