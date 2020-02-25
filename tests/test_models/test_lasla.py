from pie_extended.models.lasla.get import get_iterator_and_processor
from pie_extended.models import lasla
from pie_extended.testing_utils import FakeTagger, create_auto_tagger
from typing import List, Tuple
import csv

from unittest import TestCase


def write_crazy_file() -> str:
    filename = "crazy_text_file.txt"
    with open(filename, "w") as f:
        f.write("""\\\\\\<1>[$@$](V)\\\\\\§
\\\\<1>[$@$]\\\\§
§
\\[I]\\§
En honor et en bien et en gran remembrançe §
Et offerant mercé, honor et celebrançe §""")
    return filename


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
            {"form": "uiduarum", "lemma": "uiduarum", "pos": "fake", "morph": "Case=fake|Numb=fake|Deg=fake|Mood=fake|"
                                                                            "Tense=fake|Voice=fake|Person=fake",
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

        self.assertEqual(
                content,
            [{'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '<', 'lemma': '<', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '1', 'lemma': 'lemma0', 'pos': 'pos0',
              'morph': 'Case=Case0|Numb=Numb0|Deg=Deg0|Mood=Mood0|Tense=Tense0|Voice=Voice0|Person=Person0',
              'treated': '1'},
             {'token': '>', 'lemma': '>', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '[', 'lemma': '[', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '$', 'lemma': '$', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '@', 'lemma': '@', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '$', 'lemma': '$', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': ']', 'lemma': ']', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '(', 'lemma': '(', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': 'v', 'lemma': 'lemma1', 'pos': 'pos1',
              'morph': 'Case=Case1|Numb=Numb1|Deg=Deg1|Mood=Mood1|Tense=Tense1|Voice=Voice1|Person=Person1',
              'treated': 'u'},
             {'token': ')', 'lemma': ')', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '§', 'lemma': '§', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '<', 'lemma': '<', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '1', 'lemma': 'lemma2', 'pos': 'pos2',
              'morph': 'Case=Case2|Numb=Numb2|Deg=Deg2|Mood=Mood2|Tense=Tense2|Voice=Voice2|Person=Person2',
              'treated': '1'},
             {'token': '>', 'lemma': '>', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '[', 'lemma': '[', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '$', 'lemma': '$', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '@', 'lemma': '@', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '$', 'lemma': '$', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': ']', 'lemma': ']', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '§', 'lemma': '§', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '§', 'lemma': '§', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '[', 'lemma': '[', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': 'i', 'lemma': 'lemma3', 'pos': 'pos3',
              'morph': 'Case=Case3|Numb=Numb3|Deg=Deg3|Mood=Mood3|Tense=Tense3|Voice=Voice3|Person=Person3',
              'treated': 'i'},
             {'token': ']', 'lemma': ']', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '\\', 'lemma': '\\', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': '§', 'lemma': '§', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': 'en', 'lemma': 'lemma4', 'pos': 'pos4',
              'morph': 'Case=Case4|Numb=Numb4|Deg=Deg4|Mood=Mood4|Tense=Tense4|Voice=Voice4|Person=Person4',
              'treated': 'en'},
             {'token': 'honor', 'lemma': 'lemma5', 'pos': 'pos5',
              'morph': 'Case=Case5|Numb=Numb5|Deg=Deg5|Mood=Mood5|Tense=Tense5|Voice=Voice5|Person=Person5',
              'treated': 'honor'},
             {'token': 'et', 'lemma': 'lemma6', 'pos': 'pos6',
              'morph': 'Case=Case6|Numb=Numb6|Deg=Deg6|Mood=Mood6|Tense=Tense6|Voice=Voice6|Person=Person6',
              'treated': 'et'},
             {'token': 'en', 'lemma': 'lemma7', 'pos': 'pos7',
              'morph': 'Case=Case7|Numb=Numb7|Deg=Deg7|Mood=Mood7|Tense=Tense7|Voice=Voice7|Person=Person7',
              'treated': 'en'},
             {'token': 'bie', 'lemma': 'lemma8', 'pos': 'pos8',
              'morph': 'Case=Case8|Numb=Numb8|Deg=Deg8|Mood=Mood8|Tense=Tense8|Voice=Voice8|Person=Person8',
              'treated': 'bie'},
             {'token': '-ne', 'lemma': 'ne2', 'pos': 'pos9',
              'morph': 'Case=Case9|Numb=Numb9|Deg=Deg9|Mood=Mood9|Tense=Tense9|Voice=Voice9|Person=Person9',
              'treated': '-ne'},
             {'token': 'et', 'lemma': 'lemma10', 'pos': 'pos10',
              'morph': 'Case=Case10|Numb=Numb10|Deg=Deg10|Mood=Mood10|Tense=Tense10|Voice=Voice10|Person=Person10',
              'treated': 'et'},
             {'token': 'en', 'lemma': 'lemma11', 'pos': 'pos11',
              'morph': 'Case=Case11|Numb=Numb11|Deg=Deg11|Mood=Mood11|Tense=Tense11|Voice=Voice11|Person=Person11',
              'treated': 'en'},
             {'token': 'gra', 'lemma': 'lemma12', 'pos': 'pos12',
              'morph': 'Case=Case12|Numb=Numb12|Deg=Deg12|Mood=Mood12|Tense=Tense12|Voice=Voice12|Person=Person12',
              'treated': 'gra'},
             {'token': '-ne', 'lemma': 'ne2', 'pos': 'pos13',
              'morph': 'Case=Case13|Numb=Numb13|Deg=Deg13|Mood=Mood13|Tense=Tense13|Voice=Voice13|Person=Person13',
              'treated': '-ne'},
             {'token': 'remembrançe', 'lemma': 'lemma14', 'pos': 'pos14',
              'morph': 'Case=Case14|Numb=Numb14|Deg=Deg14|Mood=Mood14|Tense=Tense14|Voice=Voice14|Person=Person14',
              'treated': 'remembrançe'},
             {'token': '§', 'lemma': '§', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': 'et', 'lemma': 'lemma15', 'pos': 'pos15',
              'morph': 'Case=Case15|Numb=Numb15|Deg=Deg15|Mood=Mood15|Tense=Tense15|Voice=Voice15|Person=Person15',
              'treated': 'et'},
             {'token': 'offerant', 'lemma': 'lemma16', 'pos': 'pos16',
              'morph': 'Case=Case16|Numb=Numb16|Deg=Deg16|Mood=Mood16|Tense=Tense16|Voice=Voice16|Person=Person16',
              'treated': 'offerant'},
             {'token': 'mercé', 'lemma': 'lemma17', 'pos': 'pos17',
              'morph': 'Case=Case17|Numb=Numb17|Deg=Deg17|Mood=Mood17|Tense=Tense17|Voice=Voice17|Person=Person17',
              'treated': 'mercé'},
             {'token': ',', 'lemma': ',', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'},
             {'token': 'honor', 'lemma': 'lemma18', 'pos': 'pos18',
              'morph': 'Case=Case18|Numb=Numb18|Deg=Deg18|Mood=Mood18|Tense=Tense18|Voice=Voice18|Person=Person18',
              'treated': 'honor'},
             {'token': 'et', 'lemma': 'lemma19', 'pos': 'pos19',
              'morph': 'Case=Case19|Numb=Numb19|Deg=Deg19|Mood=Mood19|Tense=Tense19|Voice=Voice19|Person=Person19',
              'treated': 'et'},
             {'token': 'celebrançe', 'lemma': 'lemma20', 'pos': 'pos20',
              'morph': 'Case=Case20|Numb=Numb20|Deg=Deg20|Mood=Mood20|Tense=Tense20|Voice=Voice20|Person=Person20',
              'treated': 'celebrançe'},
             {'token': '§', 'lemma': '§', 'pos': 'PUNC', 'morph': 'MORPH=empty', 'treated': '--IGN.--'}]
        )
