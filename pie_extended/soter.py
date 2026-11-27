""" Lemmatization of Ancient Greek with Sôtêr (https://huggingface.co/Zual/soter-mini).

Sôtêr mini is a very small (1.9 M parameters) T5 model that works on the bytes of the text, and gives the lemma of
one token at a time, from the token and its context. It is a *lemmatizer*: it gives the task `lemma` and nothing
else, and is meant to be combined with another engine for the other tasks (see `CompositeTagger`).

It needs `transformers` (`pip install "pie-extended[soter]"`), imported only when the model is loaded.
"""
import json
import unicodedata
from typing import Dict, List, Optional, Sequence, Tuple

import re

DEFAULT_REPO = "Zual/soter-mini"
# The apostrophe of an elision: Sôtêr was trained on the texts of the treebanks, where it is U+2019. GreCy needs U+02BC,
# and our tokenizer gives it to the model, hence the conversion here: with U+02BC, the elided words that Sôtêr gets right
# go from 100% to 46% (PROIEL, dev set)
ELISION = "\u2019"
_APOSTROPHES = re.compile("['\u2019\u02bc\u1fbd\u1fbf\u02b9\u0384]")
# What the model gives is the convention of Perseus (the one of the entries of the LSJ). The other conventions are
# restored from a table that is in the repository of the model
CONVENTIONS = ("perseus", "proiel", "ptnk")


def build_input(forms: Sequence[str], index: int, context: int = 8) -> str:
    """ What the model is given for the token `index` of a sentence: the token spelled letter by letter, then its
    context (`context` words on each side) in which the token is marked

    >>> build_input("Ἀλέξανδρος ἐγένετο βασιλεύς".split(), 1)
    'ἐ γ έ ν ε τ ο <sep> Ἀλέξανδρος <tgt> ἐγένετο </tgt> βασιλεύς'
    >>> build_input("a b c d e".split(), 0, context=1)
    'a <sep>  <tgt> a </tgt> b'
    """
    low, high = max(0, index - context), min(len(forms), index + 1 + context)
    return "{} <sep> {} <tgt> {} </tgt> {}".format(
        " ".join(forms[index]), " ".join(forms[low:index]), forms[index], " ".join(forms[index + 1:high])
    ).strip()


class SoterLemmatizer:
    """ Gives the lemma of each token of sentences, with Sôtêr

    The contract is the one of a tagger (`tag`), so that it can be an engine of the `CompositeTagger`.

    :param repo: Repository of the model on Hugging Face (`Zual/soter-mini`), or a folder
    :param convention: `perseus` (what the model gives), `proiel` or `ptnk` (restored from the tables of the model)
    :param context: Words on each side of the token that the model sees (8: what it was trained with)
    :param batch_size: Tokens lemmatized together
    :param device: `cpu` or `cuda`
    :param max_length: Longest lemma, in bytes
    """
    TASKS: Tuple[str, ...] = ("lemma",)

    def __init__(self, repo: str = DEFAULT_REPO, convention: str = "perseus", context: int = 8, batch_size: int = 64,
                 device: str = "cpu", max_length: int = 48):
        if convention not in CONVENTIONS:
            raise ValueError("Unknown convention {!r}. Available: {}".format(convention, ", ".join(CONVENTIONS)))
        self.repo = repo
        self.convention = convention
        self.context = context
        self.batch_size = batch_size
        self.device = device
        self.max_length = max_length
        self.tokenizer = None
        self.model = None
        self.table: Dict[Tuple[str, str], str] = {}

    def load(self) -> "SoterLemmatizer":
        """ Loads the model (and the table of the convention): it is downloaded the first time """
        try:
            import torch  # noqa: F401
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as error:
            raise ImportError(
                "transformers is needed for Sôtêr: pip install \"pie-extended[soter]\""
            ) from error
        self.tokenizer = AutoTokenizer.from_pretrained(self.repo)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.repo).eval().to(self.device)
        if self.convention != "perseus":
            self.table = self._load_table(self.repo, self.convention)
        return self

    @staticmethod
    def _load_table(repo: str, convention: str) -> Dict[Tuple[str, str], str]:
        """ `{(form, lemma of Perseus): lemma of the convention}` """
        import os
        path = os.path.join(repo, "tables", convention + ".json")
        if not os.path.exists(path):
            from huggingface_hub import hf_hub_download
            path = hf_hub_download(repo, "tables/{}.json".format(convention))
        with open(path, encoding="utf-8") as f:
            return {tuple(key.split("\t")): value for key, value in json.load(f).items()}

    def _generate(self, inputs: List[str]) -> List[str]:
        """ The lemmas of a batch of inputs (this is what the model does) """
        import torch
        encoded = self.tokenizer(inputs, return_tensors="pt", padding=True, truncation=True, max_length=384)
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        with torch.inference_mode():
            generated = self.model.generate(**encoded, max_length=self.max_length, num_beams=1)
        return self.tokenizer.batch_decode(generated, skip_special_tokens=True)

    @staticmethod
    def normalize(form: str) -> str:
        """ What the model reads: NFC, and the apostrophe of an elision as in the treebanks """
        return _APOSTROPHES.sub(ELISION, unicodedata.normalize("NFC", form))

    def lemmas(self, sentences: Sequence[Sequence[str]]) -> List[List[str]]:
        """ The lemma of every token of every sentence

        The model works on NFC text, and on the apostrophe of the treebanks: the forms are normalized for it. The tokens
        are lemmatized by batches of similar length (less padding), and given back in their order.

        >>> SoterLemmatizer.normalize("δι\u02bc")
        'δι’'
        """
        forms = [[self.normalize(form) for form in sentence] for sentence in sentences]
        inputs = [build_input(sentence, index, self.context) for sentence in forms for index in range(len(sentence))]
        order = sorted(range(len(inputs)), key=lambda position: len(inputs[position]))
        results = [""] * len(inputs)
        for start in range(0, len(order), self.batch_size):
            chunk = order[start:start + self.batch_size]
            for position, lemma in zip(chunk, self._generate([inputs[position] for position in chunk])):
                results[position] = lemma

        out, position = [], 0
        for sentence in forms:
            lemmas = []
            for form in sentence:
                lemma = results[position]
                lemmas.append(self.table.get((form, lemma), lemma))
                position += 1
            out.append(lemmas)
        return out

    def tag(self, sents: Sequence[Sequence[str]], lengths: Optional[Sequence[int]] = None, **kwargs
            ) -> Tuple[List[List[Tuple[str, Tuple[str, ...]]]], List[str]]:
        """ Same contract as the taggers: tagged sentences ([(token, (lemma,))]) and the tasks (`["lemma"]`) """
        if self.model is None:
            self.load()
        lemmas = self.lemmas(sents)
        return [
            [(token, (lemma,)) for token, lemma in zip(sentence, sentence_lemmas)]
            for sentence, sentence_lemmas in zip(sents, lemmas)
        ], list(self.TASKS)
