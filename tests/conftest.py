# Helper run in a subprocess by test_spacy_tagger (needs spaCy and arguments): never collected, not even by
# `pytest --doctest-modules tests`, which imports every file.
collect_ignore = ["spacy_compare.py"]
