from ...utils import Metadata, File, get_path
from ...prototypes import ObjectCreator

from autocat import NeedsDisambiguation, StraightAutodisambiguation, CategoryAutodisambiguation, GroupAutodisambiguation

__all__ = ["DESC", "DOWNLOADS", "Disambiguator"]
DESC = Metadata(
    "LASLA-ENC",
    "lat",
    ["Thibault Clérice"],
    "Model trained on LASLA data without disambiguation",
    "https://github.com/chartes/deucalion-model-lasla"
)

DOWNLOADS = [
    File("https://github.com/chartes/deucalion-model-lasla/raw/master/latin-straight.json", "latin-straight.json"),
    File("https://github.com/chartes/deucalion-model-lasla/raw/master/latin-pos.json", "latin-pos.json"),
    File("https://github.com/chartes/deucalion-model-lasla/raw/master/latin-needs.json", "latin-needs.json"),
    File("https://github.com/chartes/deucalion-model-lasla/raw/master/model.tar", "model.tar")
]

Models = "<{},lemma,Voice,Mood,Deg,Numb,Person,Tense,Case,Gend,pos>".format(get_path("lasla", "model.tar"))


def _get_disambiguator():
    pos = CategoryAutodisambiguation.from_file(
        get_path("lasla", "latin-pos.json"), category_key="pos", lemma_key="lemma")
    straight = StraightAutodisambiguation.from_file(
        get_path("lasla", "latin-straight.json"), lemma_key="lemma")
    impossible = NeedsDisambiguation.from_file(
        get_path("lasla", "latin-needs.json"), lemma_key="lemma")
    return GroupAutodisambiguation(lemma_key="lemma", categorizers=(straight, pos, impossible))

Disambiguator: ObjectCreator = ObjectCreator(_get_disambiguator)
