from flask_pie.testing import FakeTagger
from pie_extended.models.lasla.classes import get_iterator_and_formatter
from typing import List, Tuple

from unittest import TestCase


def make_fake_data(sentences: List[str], nb_tasks: int = 9) -> List[Tuple[str, List[str]]]:
    return [
        [
            (token, tuple([token, *["fake"]*nb_tasks]))
            for token in sentence.split()
        ]
        for sentence in sentences
    ]


def make_controller(sentences: List[str]):
    # Add the lemmatizer routes
    tagger = FakeTagger(
        make_fake_data(sentences),
        tasks="lemma,Voice,Mood,Deg,Numb,Person,Tense,Case,Gend,pos".split(",")
    )
    iterator, formatter = get_iterator_and_formatter,
    return tagger, iterator, formatter


class TestPonctuation(TestCase):
    def test_consecutive_dots(self):
        """Check that consecutive punctation does not break anything

        Found out the hard way it would break things
        """

        client = make_controller([
            "id enim ait turbabuntur a facie eius patris or phanorum et iudicis uiduarum",
            "causam turbationis hanc docuit quod pater"
        ])
        req = client.post(
            "/api/",
            data={"data": "id enim ait turbabuntur a facie eius patris or phanorum et iudicis uiduarum ."
                          "  .  causam turbationis hanc docuit quod pater"}
        )
        resp = req.data.decode()
        self.assertIn(
            "uiduarum	uiduarum	fake	Case=fake|Numb=fake|Deg=fake|Mood=fake|Tense=fake|Voice=fake|Person=fake"
            "	uiduarum\r\n"
            ".	.	PUNC	MORPH=empty	.\r\n"
            ".	.	PUNC	MORPH=empty	.",
            resp,
            "Punctuation should be reinserted and mostly should not break anything"
        )

    def test_leading_punctuation(self):
        """Check that consecutive punctation does not break anything

        Special case of consecutive dots, where sentences starts with it
        """
        client = make_controller([
            "id enim ait", "turbabuntur a facie eius patris or phanorum et iudicis uiduarum"
        ])
        req = client.post("/api/", data={"data": "( id enim ait ) turbabuntur a facie eius patris or phanorum et iudicis uiduarum .  ."})
        resp = req.data.decode()
        self.assertIn(
            "form	lemma	POS	morph	treated_token\r\n"
            "(	(	PUNC	MORPH=empty	(\r\n"
            "id	id	fake	Case=fake|Numb=fake|Deg=fake|Mood=fake|Tense=fake|Voice=fake|Person=fake	id\r\n"
            "enim	enim	fake	Case=fake|Numb=fake|Deg=fake|Mood=fake|Tense=fake|Voice=fake|Person=fake	enim\r\n"
            "ait	ait	fake	Case=fake|Numb=fake|Deg=fake|Mood=fake|Tense=fake|Voice=fake|Person=fake	ait\r\n"
            ")	)	PUNC	MORPH=empty	)\r\n"
            "turbabuntur	turbabuntur	fake	Case=fake|Numb=fake|Deg=fake|Mood=fake|Tense=fake|Voice=fake|Person"
            "=fake	turbabuntur\r\n",
            resp,
            "Leading punctuation should not break anything"
        )


