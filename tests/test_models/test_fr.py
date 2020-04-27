from pie_extended.models.fr.imports import get_iterator_and_processor
from pie_extended.testing_utils import FakeTagger
from typing import List, Tuple

from unittest import TestCase
from .test_lasla import make_fake_data


def make_controller(sentences: List[str]):
    # Add the lemmatizer routes
    tagger = FakeTagger(
        make_fake_data(sentences),
        tasks="lemma,MODE,TEMPS,PERS,NOMB,GENRE,CAS,DEGRE,POS".split(",")
    )
    iterator, processor = get_iterator_and_processor()
    return tagger, iterator, processor


class TestFr(TestCase):
    """
    def test_elision_apostrophe(self):
        string = "q'il meurt"
        treated = ["q' il meurt"]
        tagger, it, pro = make_controller(treated)
        out = tagger.tag_str(string, it, pro)
        self.assertEqual(out[0]["form"], "q'")
        self.assertEqual(out[0]["treated"], "q")

    def test_elision_apostrophe_and_quote(self):
        string = "'q'il meurt 'dit il'"
        treated = ["' q' il meurt  ' dit il '"]
        tagger, it, pro = make_controller(treated)
        out = tagger.tag_str(string, it, pro)
        self.assertEqual(out[0]["form"], "'")
        self.assertEqual(out[0]["treated"], "'")
        self.assertEqual(out[1]["form"], "q'")
        self.assertEqual(out[1]["treated"], "q")
        self.assertEqual(out[-1]["form"], "'", "Last apostrophe is kept")
        # Ending and starting apostrophe are not reinserted for some reason.
    """

    def test_tokenization_clitics(self):
        iterator, _ = get_iterator_and_processor()
        iterator.tokenizer.replacer = lambda x: x  # Until model is fixed
        self.assertEqual(
            list(
                iterator.tokenizer.sentence_tokenizer(
                    "L'a-t-il mangé celui-là-même ou l'a-t-on rangé celui-ci ? -très mauvaise tokenization"
                )
            ),
            [
                ["L'", 'a', '-t-il', 'mangé', 'celui', '-là', '-même',
                 'ou', "l'", 'a', '-t-on', 'rangé', 'celui', '-ci', '?'],
                ["-", "très", "mauvaise", "tokenization"]
            ],
            "Dots around roman number are not sentences markers"
        )

    def test_tokenization_peut_etre(self):
        iterator, _ = get_iterator_and_processor()
        iterator.tokenizer.replacer = lambda x: x  # Until model is fixed
        self.assertEqual(
            list(
                iterator.tokenizer.sentence_tokenizer(
                    "Peut-être a-t-il raison ?"
                )
            ),
            [['Peut', '-', 'être', 'a', '-t-il', 'raison', '?']],
            "Dots around roman number are not sentences markers"
        )

    def test_tokenization_aujourdhui(self):
        iterator, _ = get_iterator_and_processor()
        iterator.tokenizer.replacer = lambda x: x  # Until model is fixed
        self.assertEqual(
            list(
                iterator.tokenizer.sentence_tokenizer(
                    "Aujourd'hui a-t-il raison ?"
                )
            ),
            [['Aujourd\'hui', 'a', '-t-il', 'raison', '?']],
            "Dots around roman number are not sentences markers"
        )

    def test_tokenization_elise_t_euphonique(self):
        """ Check that -t' are correctly tokenized """
        iterator, _ = get_iterator_and_processor()
        self.assertEqual(
            list(
                iterator.tokenizer.sentence_tokenizer("Va-t'en va-nu-pieds !")
            ),
            [
                ["Va", "-t'", "en", "va", "-", "nu", "-", "pieds", "!"]
            ]
        )

    def test_tokenization_abbreviations(self):
        """ Check that abbreviation are recognized """
        iterator, _ = get_iterator_and_processor()
        self.assertEqual(
            list(
                iterator.tokenizer.sentence_tokenizer("La Zoo. montre des limites. cf. un truc. Et V. n.  est un neutre"
                                                      ". Mais j'aime ma Lit. et mon lit.!")
            ),
            [
                ['La', 'Zoo.', 'montre', 'des', 'limites', '.'],
                ['cf.', 'un', 'truc', '.'],
                ['Et', 'V.', 'n.', 'est', 'un', 'neutre', '.'],
                ['Mais', "j'", 'aime', 'ma', 'Lit.', 'et', 'mon', 'lit', '.', '!']
            ]
        )
