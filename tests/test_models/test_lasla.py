from pie_extended.models.lasla.classes import get_iterator_and_formatter
from pie_extended.testing_utils import FakeTagger
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
    iterator, formatter = get_iterator_and_formatter()
    return tagger, iterator, formatter


class TestPonctuation(TestCase):
    def test_consecutive_dots(self):
        """Check that consecutive punctation does not break anything

        Found out the hard way it would break things
        """

        tagger, data_iterator, formatter = make_controller([
            "id enim ait turbabuntur a facie eius patris or phanorum et iudicis uiduarum",
            "causam turbationis hanc docuit quod pater"
        ])

        result = tagger.tag_str(
            data="id enim ait turbabuntur a facie eius patris or phanorum et iudicis uiduarum ."
                          "  .  causam turbationis hanc docuit quod pater",
            formatter_class=formatter,
            iterator=data_iterator
        )
        self.assertIn(
            "uiduarum	uiduarum	fake	Case=fake|Numb=fake|Deg=fake|Mood=fake|Tense=fake|Voice=fake|Person=fake"
            "	uiduarum\r\n"
            ".	.	PUNC	MORPH=empty	.\r\n"
            ".	.	PUNC	MORPH=empty	.",
            result,
            "Punctuation should be reinserted and mostly should not break anything"
        )

    def test_leading_punctuation(self):
        """Check that consecutive punctation does not break anything

        Special case of consecutive dots, where sentences starts with it
        """
        tagger, data_iterator, formatter = make_controller([
            "id enim ait", "turbabuntur a facie eius patris or phanorum et iudicis uiduarum"
        ])
        result = tagger.tag_str(
            "( id enim ait ) turbabuntur a facie eius patris or phanorum et iudicis uiduarum .  .",
            formatter_class=formatter,
            iterator=data_iterator
        )
        self.assertIn(
            "form	lemma	POS	morph	treated_token\r\n"
            "(	(	PUNC	MORPH=empty	(\r\n"
            "id	id	fake	Case=fake|Numb=fake|Deg=fake|Mood=fake|Tense=fake|Voice=fake|Person=fake	id\r\n"
            "enim	enim	fake	Case=fake|Numb=fake|Deg=fake|Mood=fake|Tense=fake|Voice=fake|Person=fake	enim\r\n"
            "ait	ait	fake	Case=fake|Numb=fake|Deg=fake|Mood=fake|Tense=fake|Voice=fake|Person=fake	ait\r\n"
            ")	)	PUNC	MORPH=empty	)\r\n"
            "turbabuntur	turbabuntur	fake	Case=fake|Numb=fake|Deg=fake|Mood=fake|Tense=fake|Voice=fake|Person"
            "=fake	turbabuntur\r\n",
            result,
            "Leading punctuation should not break anything"
        )

    def test_punctuation_is_not_seen(self):
        """Check that punctuation is not seen by the tagger

        """
        tagger, data_iterator, formatter = make_controller([
            "id enim ait", "turbabuntur a facie eius patris or phanorum et iudicis uiduarum"
        ])
        tagger.tag_str(
            "( id enim ait ) turbabuntur a facie eius patris or phanorum et iudicis uiduarum .  .",
            formatter_class=formatter,
            iterator=data_iterator
        )
        self.assertNotIn(
            "(",
            [tok for sent in tagger.seen for tok in sent],
            "Punctuation should not be seen by the Tagger"
        )

    def test_j_are_temporarly_replaced(self):
        """Check that characters are replaced for the tagger, thus avoiding out of domain, and reinserted

        """
        tagger, data_iterator, formatter = make_controller([
            "id enim ait", "turbabuntur a facie eius patris or phanorum et iudicis uiduarum"
        ])
        result = tagger.tag_str(
            "( id enim ait ) turbabuntur a facie eius patris or phanorum et judicis uiduarum .  .",
            formatter_class=formatter,
            iterator=data_iterator
        )
        flatten_seen = list([tok for sent in tagger.seen for tok in sent])

        self.assertNotIn("judicis", flatten_seen, "'j' should be removed from tagging")
        self.assertIn("iudicis", flatten_seen, "And 'i' should replace it")
        self.assertIn("\njudicis\t", result, "But, in the end, the original form is given to the user")

    def test_underscores(self):
        string = "una operatio in ecclesiae fundamento.._... _ . laetatur autem pater quia filius perierat"
        tagger, data_iterator, formatter = make_controller([
            "una operatio in ecclesiae fundamento", "laetatur autem pater quia filius perierat"
        ])
        tagger.tag_str(
            string,
            formatter_class=formatter,
            iterator=data_iterator
        )
        flatten_seen = list([tok for sent in tagger.seen for tok in sent])
        self.assertEqual(
            ['una', 'operatio', 'in', 'ecclesiae', 'fundamento', 'laetatur', 'autem', 'pater', 'quia', 'filius',
             'perierat'],
            flatten_seen,
            "Seen element should not count the underscord"
        )