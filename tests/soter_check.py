""" Run in a subprocess by test_soter: tags with the real models of `grc_soter`.

The preset uses `grc_perseus_sm`: a process cannot load two different GreCy pipelines (spaCy raises E004 on the duplicate
`grecy_*` factories), and the other tests of spaCy load `grc_perseus_trf`. Hence the subprocess (as `spacy_compare.py`).

Usage: python tests/soter_check.py -> prints a JSON of what the model gives for some texts
"""
import json
import warnings

warnings.simplefilter("ignore")

from pie_extended.cli.utils import get_pipeline, get_tagger  # noqa: E402


def tag(text, **kwargs):
    tagger = get_tagger("grc_soter", **kwargs)
    iterator, processor = get_pipeline("grc_soter", tagger, space_after=False)
    return tagger, tagger.tag_str(text, iterator=iterator, processor=processor)


def main() -> None:
    out = {}
    _, out["beginning"] = tag("ἐν ἀρχῇ ἦν ὁ λόγος")
    _, out["card"] = tag("Ἀλέξανδρος ἐγένετο βασιλεύς")
    _, out["elision"] = tag("πάντα δι' αὐτοῦ ἐγένετο")
    tagger, out["lemma_only"] = tag("ἐν ἀρχῇ", tasks=["lemma"])
    out["lemma_only_engines"] = [type(engine).__name__ for engine, _ in tagger.engines]
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
