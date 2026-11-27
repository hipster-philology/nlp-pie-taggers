""" Segmentation of the clitics of Classical Armenian, as done in the Universal Dependencies treebank (CAVaL).

In this treebank, 15% of the written words are cut into several words: proclitics (`զ` accusative, `յ`, `ց`),
enclitics (the article `ն`, `ս`, `դ`, `նա`...) are words of their own (`զմեղս` -> `զ`, `մեղս`;
`յանապատին` -> `յ`, `անապատի`, `ն`). The Pie model was trained on these words and its documentation asks for
pre-tokenized input, so the clitics have to be split. No rule can do it (many words legitimately start with `զ`,
`յ` or `ց`, or end with `ն`): the segmenter learns where the treebank cuts.

It is an averaged perceptron that decides, for each position inside a word, whether the treebank cuts there, from
the characters around the position (and the word itself, which makes it a lexicon for the known words).
On the held-out test set of the treebank: cut points F1 = 97.2%, sentences with exactly the words of the treebank:
12.8% without segmentation -> 89%.

The weights are learned from the treebank *on the machine of the user* (`pie-extended install-addons hy_xcl`),
not distributed: CAVaL is licensed CC BY-NC-SA 4.0, which a derived file would inherit.
"""
import collections
import json
import os
import random
import warnings
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

import regex as re

from pie_extended.utils import get_path

# Only words made of Armenian letters can be cut
_WORD = re.compile(r"^[Ա-Ֆՠ-ֈ]+$")
FILENAME = "clitics.json"


def default_path() -> str:
    return get_path("hy_xcl", FILENAME)


def features(word: str, position: int) -> List[str]:
    """ Features of the position between `word[:position]` and `word[position:]` """
    word = word.lower()
    left, right = word[:position], word[position:]
    return [
        "bias",
        "word=%s|%d" % (word, position),  # What was seen for this very word: a lexicon
        "L1=" + left[-1:], "L2=" + left[-2:], "L3=" + left[-3:],
        "R1=" + right[:1], "R2=" + right[:2], "R3=" + right[:3],
        "L1R1=%s|%s" % (left[-1:], right[:1]),
        "start=%d" % min(position, 4), "end=%d" % min(len(word) - position, 4),
        "left=" + (left if len(left) <= 4 else "_"), "right=" + (right if len(right) <= 4 else "_"),
        "len=%d" % min(len(word), 10),
    ]


class CliticSegmenter:
    """ Gives where the clitics of a word have to be cut

    >>> examples = [("զմեղս", {1}), ("զճանապարհ", {1}), ("յանապատին", {1, 8}), ("մեղս", set()), ("ճանապարհ", set())] * 4
    >>> segmenter = train(examples, epochs=6)
    >>> segmenter.cuts("զմեղս"), segmenter.cuts("մեղս")
    ([1], [])
    >>> segmenter.split("յանապատին")
    ['յ', 'անապատի', 'ն']
    """
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights: Dict[str, float] = weights or {}

    def cuts(self, word: str) -> List[int]:
        """ Positions (between characters) where `word` is cut """
        if len(word) < 2 or not _WORD.match(word):
            return []
        weights = self.weights
        return [
            position for position in range(1, len(word))
            if sum(weights.get(feature, 0.0) for feature in features(word, position)) > 0
        ]

    def split(self, word: str) -> List[str]:
        bounds = [0] + self.cuts(word) + [len(word)]
        return [word[start:end] for start, end in zip(bounds, bounds[1:])]

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "weights": {k: round(v, 4) for k, v in self.weights.items() if abs(v) >= 1e-4}},
                      f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "CliticSegmenter":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f)["weights"])


def load_default(warn: bool = True) -> Optional[CliticSegmenter]:
    """ The segmenter trained by `install-addons`, or None (with a warning) if it was not """
    path = default_path()
    if os.path.exists(path):
        return CliticSegmenter.load(path)
    if warn:
        warnings.warn(
            "The clitics of Classical Armenian are not split (the model was trained on words where they are): "
            "run `pie-extended install-addons hy_xcl` to learn how from the Universal Dependencies treebank",
            UserWarning, stacklevel=3
        )
    return None


def train(examples: Sequence[Tuple[str, Set[int]]], epochs: int = 8, seed: int = 0) -> CliticSegmenter:
    """ Averaged perceptron

    :param examples: A word, and the positions where it has to be cut
    """
    data = [(word, set(cuts)) for word, cuts in examples if len(word) > 1 and _WORD.match(word)]
    weights: Dict[str, float] = collections.defaultdict(float)
    totals: Dict[str, float] = collections.defaultdict(float)
    stamps: Dict[str, int] = collections.defaultdict(int)
    step = 0
    shuffler = random.Random(seed)
    for _ in range(epochs):
        shuffler.shuffle(data)
        for word, gold in data:
            for position in range(1, len(word)):
                step += 1  # Every instance counts for the average, not only the mistakes
                feats = features(word, position)
                expected = position in gold
                if (sum(weights.get(f, 0.0) for f in feats) > 0) != expected:
                    update = 1.0 if expected else -1.0
                    for f in feats:
                        totals[f] += (step - stamps[f]) * weights[f]
                        stamps[f] = step
                        weights[f] += update
    averaged = {f: (totals[f] + (step - stamps[f]) * w) / max(1, step) for f, w in weights.items()}
    return CliticSegmenter(averaged)


def read_conllu(path: str) -> Iterator[Tuple[str, List[str]]]:
    """ Sentences of a CoNLL-U file: the text, and the words (multiword token ranges and empty nodes are skipped) """
    text, words = None, []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("# text ="):
                text = line[len("# text ="):].strip()
            elif not line.strip():
                if text is not None:
                    yield text, words
                text, words = None, []
            elif not line.startswith("#"):
                columns = line.split("\t")
                if columns[0].isdigit():
                    words.append(columns[1])
        if text is not None:
            yield text, words


def training_examples(sentences: Iterable[Tuple[str, List[str]]]) -> List[Tuple[str, Set[int]]]:
    """ Where the treebank cuts the words, for the tokens of our tokenizer (without any segmentation)

    A sentence is skipped if our tokens cannot be rebuilt from its words (different spelling, for example).
    """
    from pie_extended.models.hy_hye.tokenizer import ArmenianTokenizer

    tokenizer = ArmenianTokenizer()
    examples: List[Tuple[str, Set[int]]] = []
    for text, words in sentences:
        tokenizer.reset()
        tokens = tokenizer.word_tokenizer(text)
        found: List[Tuple[str, Set[int]]] = []
        index = 0
        for token in tokens:
            written, cuts = "", set()
            while written != token and index < len(words) and len(written) < len(token):
                if written:
                    cuts.add(len(written))
                written += words[index]
                index += 1
            if written != token:
                found = []
                break
            found.append((token, cuts))
        examples.extend(found)
    return examples


def evaluate(segmenter: CliticSegmenter, sentences: Sequence[Tuple[str, List[str]]]) -> Dict[str, float]:
    """ Scores on sentences of a treebank

    :return: Precision, recall and F1 of the cut points, share of words cut as in the treebank, and share of sentences
        whose words are exactly the ones of the treebank
    """
    from pie_extended.models.hy_hye.tokenizer import ArmenianTokenizer

    true = false = missed = words_ok = words = 0
    for word, gold in training_examples(sentences):
        predicted = set(segmenter.cuts(word))
        true += len(predicted & gold)
        false += len(predicted - gold)
        missed += len(gold - predicted)
        words_ok += predicted == gold
        words += 1
    tokenizer = ArmenianTokenizer(segmenter=segmenter)
    exact = 0
    for text, gold_words in sentences:
        tokenizer.reset()
        exact += tokenizer.word_tokenizer(text) == gold_words
    precision = true / max(1, true + false)
    recall = true / max(1, true + missed)
    return {
        "precision": precision, "recall": recall, "f1": 2 * precision * recall / max(1e-9, precision + recall),
        "words_exact": words_ok / max(1, words), "sentences_exact": exact / max(1, len(sentences)),
    }
