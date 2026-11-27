""" Builds the lexicons of `pie_extended.pipeline.disambiguators.lexicons` from an annotated corpus.

It analyzes which disambiguation can be learned from a category (the part of speech, usually) only. The result is
the JSON files that feed the lexicons, and the list of the lemmas that cannot be disambiguated this way: these are
the ones where the real work of disambiguation (word sense disambiguation) is.

The corpus is TSV files with a header, that contain at least the columns "lemma", the category (for example "pos")
and "Dis", the disambiguation index (`1` for `qui1`...)::

    token   lemma   pos     Dis
    qui     qui     PROint  2
    est     sum     VER     1
    qui     qui     PROrel  1

Use it with `pie-extended build-lexicons pos corpus/*.tsv --prefix latin-`, or from Python with `build_lexicons`.
(This was the command `autodisambiguator` of the library of the same name, now part of Pie Extended.)
"""
import csv
import json
from collections import Counter, defaultdict, namedtuple
from typing import Callable, Counter as CounterT, Dict, Iterable, List, Union


def default_null_dis(string):
    if string and string != "_":
        return True
    return False


def read_corpus(
        files,
        lemma_key: str = "lemma",
        category_key: str = "pos",
        disambiguation_key: str = "Dis",
        null_dis: Callable[[str], bool] = default_null_dis
) -> Dict[str, Dict[str, CounterT[str]]]:
    stats = defaultdict(lambda: defaultdict(Counter))
    for file in files:
        with open(file, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                disambiguation_index = row[disambiguation_key]
                if null_dis(disambiguation_index):
                    stats[row[lemma_key]][disambiguation_index][row[category_key]] += 1
    return stats


def stats_dict() -> Dict[str, Union[int, List]]:
    """ Function used to generate new dict entry for default dict
    """
    return {
        "total": 0,
        "auto": 0,
        "lemma": []
    }


Dispatched = namedtuple("Dispatched", [
    "stats_per_dis_nb", "partially_categorizable", "uncategorizable",
    "one_disambiguation_only", "autodisambiguation"
])


def dispatch(stats: Dict[str, Dict[str, Dict[str, int]]], limit_counter: int = 1):
    """ Based on a dictionary of counters

    :param stats: Dictionary of lemma to disambiguate with a dictionary of index below, themselves
                    holding each CATEGORY it has been found with and their count
                    eg {"qui": {"1": {"ADV": 1, "PROrel": 50}, "2" {"PROint": 87}}}
    :param limit_counter: Limit at which we assume the presence of a Category is an error
    :return:
    """
    stats_per_dis_nb = defaultdict(stats_dict)
    partialy_categorizable = []
    uncategorizale = []
    one_disambiguation_only = {}
    autodisambiguation = {}

    for lemma, sublemma in stats.items():
        cats = []
        for counter in sublemma.values():
            # Check that we have multiple categories
            if len(counter) > 1:
                # We keep only POS which have at least one presence, to filter out errors
                #   Note that we could filter it based on a ratio to take into account those errors
                count_pos = [POS for POS, count in counter.items() if count > limit_counter]

                # If we have at least one categories that appears more than the arbitrary limit
                if len(count_pos):
                    cats.append(count_pos)
                # If not, each categories happens only below the limit
                else:
                    continue
            else:
                # Some might only have POS with 1 occurences EVERYWHERE
                cats.append(list(counter.keys()))

        stats_per_dis_nb[len(sublemma)]["total"] += 1
        stats_per_dis_nb[len(sublemma)]["lemma"].append(lemma)

        # If we have more than one category
        if len(cats) > 1:
            cats_simplified = [el for li in cats for el in li]
            cats_set = list(set(cats_simplified))

            # Set is unordered... So it can shift things
            cats_simplified = sorted(cats_simplified)
            cats_set = sorted(cats_set)

            # if the list is equal to the set
            #  this means all variations are dispatched based on POS
            #  and are not based on meaning
            if cats_simplified == cats_set:
                stats_per_dis_nb[len(sublemma)]["auto"] += 1
                autodisambiguation[lemma] = {
                    pos: index
                    for index, counter in sublemma.items()
                    for pos, pos_count in counter.items()
                    if pos_count > limit_counter
                }

                if len(autodisambiguation[lemma]) == 0:
                    only_one = True
                    possible = {}
                    for index, counter in sublemma.items():
                        if len(counter) > 1:
                            only_one = False
                            break
                        else:
                            for pos, pos_count in counter.items():
                                possible[pos] = index
                                if not pos_count <= limit_counter:
                                    only_one = False
                                    break

                    if only_one:
                        autodisambiguation[lemma] = possible
                    else:
                        del autodisambiguation[lemma]
                        uncategorizale.append(lemma)

            # We have different categories in at least one sublemma
            elif len(cats_set) != 1:
                partialy_categorizable.append({"lemma": lemma, "sub": sublemma})
                autodisambiguation[lemma] = {
                    pos: index
                    for index, counter in sublemma.items()
                    for pos, pos_count in counter.items()
                    if pos_count > limit_counter and cats_simplified.count(pos) == 1
                }
            else:
                uncategorizale.append(lemma)

            # Check up that a dict has not been left empty
            if lemma in autodisambiguation and len(autodisambiguation[lemma]) == 0:
                print(lemma, sublemma)
        else:
            if len(sublemma.keys()) > 1:
                uncategorizale.append(lemma)
            else:
                one_disambiguation_only[lemma] = list(sublemma.keys())[0]
    return Dispatched(
        stats_per_dis_nb, partialy_categorizable, uncategorizale,
        one_disambiguation_only, autodisambiguation
    )


def summary(dispatched: Dispatched) -> List[str]:
    """ Lines that tell how much of the lemmas can be disambiguated automatically """
    lines = []
    total = 0
    auto = 0
    for nb in sorted(dispatched.stats_per_dis_nb.keys()):
        details = dispatched.stats_per_dis_nb[nb]
        lines.append("Lemma with {} different sublemma".format(nb))

        if nb == 1:
            auto += details["total"]
        else:
            auto += details["auto"]

        total += details["total"]

        lines.append("--- Total: {}".format(details["total"]))
        lines.append("--- Auto.: {}".format(details["auto"]))
        lines.append("--- Auto%: {:.2f}".format(details["auto"] / details["total"] * 100))

    lines.append("Mixed")
    lines.append("--- Total: {}".format(total))
    lines.append("--- Auto.: {}".format(auto))
    lines.append("--- Auto%: {:.2f}".format(auto / total * 100 if total else 0))
    lines.append("{} lemma with partial automatization possible".format(len(dispatched.partially_categorizable)))
    lines.append("{} lemma with no automatization possible".format(len(dispatched.uncategorizable)))
    lines.append("{} lemma with no secondary possible disambiguation".format(len(dispatched.one_disambiguation_only)))
    return lines


def write_lexicons(dispatched: Dispatched, prefix: str, category_key: str) -> List[str]:
    """ Writes the JSON files of the lexicons

    :return: Their paths: `{prefix}{category_key}.json` (for `CategoryAutodisambiguation`), `{prefix}straight.json`
        (for `StraightAutodisambiguation`) and `{prefix}needs.json` (for `NeedsDisambiguation`)
    """
    paths = []
    for name, content in (
            (category_key, dispatched.autodisambiguation),
            ("straight", dispatched.one_disambiguation_only),
            ("needs", list(set(
                dispatched.uncategorizable + list(dispatched.one_disambiguation_only.keys()) +
                list(dispatched.autodisambiguation.keys())
            ))),
    ):
        path = prefix + name + ".json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f)
        paths.append(path)
    return paths


def build_lexicons(prefix: str, category_key: str, lemma_key: str, files: Iterable[str],
                   disambiguation_key: str) -> Dispatched:
    """ Reads the corpus, prints a summary, and writes the JSON files of the lexicons (see `write_lexicons`) """
    files = list(files)
    if not files:
        raise ValueError("No files found")

    stats = read_corpus(
        files, lemma_key=lemma_key, category_key=category_key, disambiguation_key=disambiguation_key,
        null_dis=default_null_dis
    )
    dispatched = dispatch(stats)

    print()
    print()
    print("--- Summary ---")
    print()
    for line in summary(dispatched):
        print(line)

    write_lexicons(dispatched, prefix, category_key)
    return dispatched
