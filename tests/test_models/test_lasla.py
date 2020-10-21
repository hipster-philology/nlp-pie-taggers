from pie_extended.models.lasla.imports import get_iterator_and_processor
from pie_extended.models import lasla
from pie_extended.testing_utils import FakeTagger, create_auto_tagger
from typing import List, Tuple

from unittest import TestCase


def write_crazy_file() -> str:
    filename = "crazy_text_file.txt"
    with open(filename, "w") as f:
        f.write("""\\\\\\<1>[$@$](V)\\\\\\§
\\\\<1>[$@$]\\\\§
§
\\[I]\\§
At o sceleste penis, o meum malum,
graui piaque lege noxiam lues.
Licet querare, nec tibi tener puer""")
    return filename


class FakeAnnotationMaker:
    def __init__(self):
        self.cnt = 0

    def make_response(self, token, is_ignored=False, treated=None):
        if is_ignored:
            return {
                'token': token, 'lemma': token, 'pos': 'PUNC', 'morph': 'MORPH=empty', 'Dis': '_',
                'treated': '--IGN.--'
            }
        else:
            resp = {
                'token': token, 'lemma': f'lemma{self.cnt}', 'pos': f'pos{self.cnt}',
                'morph': 'Case=Case{0}|Numb=Numb{0}|Gend=Gend{0}|Deg=Deg{0}|Mood=Mood{0}|Tense=Tense{0}|'
                         'Voice=Voice{0}|Person=Person{0}'.format(self.cnt),
                'Dis': f'Dis{self.cnt}', 'treated': treated if treated else token
            }
            self.cnt += 1
            return resp

    def make_multiple_response(self, tokens, is_ignored=False):
        for token in tokens:
            yield self.make_response(token, is_ignored=is_ignored)

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
    tasks = "lemma,Voice,Mood,Deg,Numb,Person,Tense,Case,Gend,Dis,pos".split(",")
    tagger = FakeTagger(
        make_fake_data(sentences, nb_tasks=len(tasks)),
        tasks=tasks
    )
    iterator, processor = get_iterator_and_processor()
    return tagger, iterator, processor


class TestLasla(TestCase):
    def test_consecutive_dots(self):
        """Check that consecutive punctation does not break anything

        Found out the hard way it would break things
        """

        tagger, data_iterator, processor = make_controller([
            "id enim ait turbabuntur a facie eius patris or phanorum et iudicis uiduarum",
            "causam turbationis hanc docuit quod pater"
        ])

        result = tagger.tag_str(
            data="id enim ait turbabuntur a facie eius patris or phanorum et iudicis uiduarum ."
                          "  .  causam turbationis hanc docuit quod pater",
            processor=processor,
            iterator=data_iterator
        )
        self.assertEqual(
            result[12],
            {"form": "uiduarum", "lemma": "uiduarum", "pos": "fake", "morph": "Case=fake|Numb=fake|Gend=fake"
                                                                              "|Deg=fake|Mood=fake|"
                                                                              "Tense=fake|Voice=fake|Person=fake",
                                                                              'Dis': 'fake',
             "treated": "uiduarum"},
            "Punctuation should be reinserted and mostly should not break anything"
        )

    def test_leading_punctuation(self):
        """Check that consecutive punctation does not break anything

        Special case of consecutive dots, where sentences starts with it
        """
        tagger, data_iterator, processor = make_controller([
            # Need an empty sentence because ( was treated as such
            "id enim ait", "turbabuntur a facie eius patris or phanorum et iudicis uiduarum"
        ])
        result = tagger.tag_str(
            "( id enim ait) turbabuntur a facie eius patris or phanorum et iudicis uiduarum ..",
            processor=processor,
            iterator=data_iterator
        )
        tokens = [t["form"] for t in result]
        self.assertEqual(
            ["(", "id", "enim", "ait", ")", "turbabuntur", "a", "facie", "eius", "patris", "or", "phanorum",
             "et", "iudicis", "uiduarum", ".", "."],
            tokens,
            "Leading punctuation should not break anything"
        )

    def test_punctuation_is_not_seen(self):
        """Check that punctuation is not seen by the tagger

        """
        tagger, data_iterator, processor = make_controller([
            "id enim ait", "turbabuntur a facie eius patris or phanorum et iudicis uiduarum"
        ])
        tagger.tag_str(
            "( id enim ait ) turbabuntur a facie eius patris or phanorum et iudicis uiduarum .  .",
            processor=processor,
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
        tagger, data_iterator, processor = make_controller([
            "iudicis uiduarum"
        ])
        result = tagger.tag_str(
            "judicis uiduarum",
            processor=processor,
            iterator=data_iterator
        )
        flatten_seen = list([tok for sent in tagger.seen for tok in sent])

        self.assertEqual(result[0]["form"], "judicis", "'j' should be removed from tagging")
        self.assertEqual(result[0]["treated"], "iudicis", "And 'i' should replace it")

    def test_underscores(self):
        string = "una operatio in ecclesiae fundamento.._... _ . laetatur autem pater quia filius perierat"
        tagger, data_iterator, processor = make_controller([
            "una operatio in ecclesiae fundamento", "laetatur autem pater quia filius perierat"
        ])
        tagger.tag_str(
            string,
            processor=processor,
            iterator=data_iterator
        )
        flatten_seen = list([tok for sent in tagger.seen for tok in sent])
        self.assertEqual(
            ['una', 'operatio', 'in', 'ecclesiae', 'fundamento', 'laetatur', 'autem', 'pater', 'quia', 'filius',
             'perierat'],
            flatten_seen,
            "Seen element should not count the underscord"
        )

    def test_with_fake_advanced_tagger(self):
        target = write_crazy_file()
        tagger, it, pr = create_auto_tagger(lasla, lower=True)
        out_file = tagger.tag_file(target, it, pr)
        content = []
        with open(out_file) as f:
            header = []
            for line in f:
                splitted = line.strip().split()
                if not header:
                    header = splitted
                    continue
                content.append(dict(list(zip(header, splitted))))
        self.maxDiff = None

        fam = FakeAnnotationMaker()
        """\\\<1>[$@$](V)\\\§
\\<1>[$@$]\\§
§
\[I]\§
At o sceleste penis, o meum malum,
graui piaque lege noxiam lues.
Licet querare, nec tibi tener puer"""
        self.assertEqual(
                content,
            [
                *fam.make_multiple_response(["\\", "\\", "\\", "<"], is_ignored=True),
                fam.make_response("1"),
                *fam.make_multiple_response([">", "[", "$", "@", "$", "]", "("], is_ignored=True),
                fam.make_response("V", is_ignored=False, treated="3"),  # Roman Numeral
                *fam.make_multiple_response(
                    [")", "\\", "\\", "\\", "§", "\\", "\\", "<"], is_ignored=True),
                fam.make_response("1"),
                *fam.make_multiple_response([
                    ">", "[", "$", "@", "$", "]",
                    "\\", "\\", "§",
                    "§",
                    "\\", "["], is_ignored=True),
                fam.make_response("I", is_ignored=False, treated="1"),  # Roman Numeral
                *fam.make_multiple_response(["]", "\\", "§"], is_ignored=True),
                *fam.make_multiple_response(["At", "o", "sceleste", "penis"]),
                fam.make_response(",", is_ignored=True),
                *fam.make_multiple_response(["o", "meum", "malum"]),
                fam.make_response(",", is_ignored=True),
                *fam.make_multiple_response(["graui", "piaque", "lege", "noxiam", "lues"]),
                fam.make_response(".", is_ignored=True),
                *fam.make_multiple_response(["Licet", "querare"]),
                fam.make_response(",", is_ignored=True),
                *fam.make_multiple_response(["nec", "tibi", "tener", "puer", ])
            ]
        )

    def test_normalizers(self):
        "Check that references and abbreviations are correctly ignored"
        iterator, _ = get_iterator_and_processor()

        self.assertEqual(
            list(iterator("[REF:1.a.b]Quis est M. Cicero ? [REF:1.a.c] Ego sum !")),
            [
                (['Quis', 'est', 'M', 'Cicero'], 4, {0: '[REF:1.a.b]', 5: '?'}),
                (['Ego', 'sum'], 2, {0: '[REF:1.a.c]', 3: '!'})
            ],
            "References and abbreviations are kept as tokens. Abbreviations are sent in without DOT,"
            "References are untouched"
        )

        self.assertEqual(
            iterator.tokenizer.tokens,
            [(0, '[REF:1.a.b]', '[REF:1.a.b]'), (1, 'Quis', 'Quis'), (2, 'est', 'est'), (3, 'M.', 'M'),
             (4, 'Cicero', 'Cicero'), (5, '?', '?'), (6, '[REF:1.a.c]', '[REF:1.a.c]'), (7, 'Ego', 'Ego'),
             (8, 'sum', 'sum'), (9, '!', '!')],
            "Memory should be kept for abbreviations"
        )

