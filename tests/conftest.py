# Helpers run in a subprocess by test_spacy_tagger and test_soter (they need spaCy): never collected, not even by
# `pytest --doctest-modules tests`, which imports every file.
collect_ignore = ["spacy_compare.py", "soter_check.py"]
