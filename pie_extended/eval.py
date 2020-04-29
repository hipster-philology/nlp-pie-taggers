from pie_extended.cli.sub import get_tagger
from pie_extended.tagger import ExtensibleTagger
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.models.lasla.imports import get_iterator_and_processor
from typing import List, Dict, Optional
import re


def read_test_file(
        test_file: str, tasks: List[str],
        glue_char: str = "|", regexp: str = "({task}=)", glued_task: Optional[str] = "morph",
        default_value="_", treated: Optional[str] = "treated",
        ignore: str = "--IGN.--", remove_disambiguation=True,
        task_map = {"pos": "POS"}
) -> List[Dict[str, str]]:
    """

    :param test_file:
    :param tasks:
    :param glue_char:
    :param regexp:
    :param glued_task:
    :param default_value:
    :param treated:
    :param ignore:
    :param remove_disambiguation:
    :param task_map:
    :returns:

    """
    res = {
        task: re.compile(regexp.format(task=task))
        for task in tasks
    }
    form_key = "form"
    if treated:
        form_key = treated
    out = []
    remover_dis = re.compile(r"(\d+)$")
    with open(test_file) as f:
        for line_no, line in enumerate(f):
            data = line.strip().split()
            if not data:
                continue
            if line_no == 0:
                header = data
                filtered_task = [task for task in tasks if task not in header]
                continue
            data = dict(zip(header, data))
            if ignore and data[form_key] == ignore:
                continue
            if glued_task:
                glued = data[glued_task].split(glue_char)
                data.update({
                    task: res[task].sub("", glue_value)
                    for glue_value in glued
                    for task in filtered_task
                    if res[task].match(glue_value)
                })
            if remove_disambiguation:
                data["lemma"] = remover_dis.sub("", data["lemma"])

            out.append({task: data.get(task_map.get(task, task), default_value) for task in [form_key]+tasks})

    return out


def process_test_file(
        model_name: str, annotation_lists: List[Dict[str, str]],
        sentence_marker_column: str = "form", sentence_marker_regex: str = r"^[.!?$]+$"
) -> List[List[Dict[str, str]]]:
    """

    Parameters
    ----------
    model_name
    annotation_lists
    sentence_marker_column
    sentence_marker_regex

    Returns
    -------

    """

    tagger: ExtensibleTagger = get_tagger(model_name)
    tasks = [task for model, tasks in tagger.models for task in tasks]

    # Need to deal with sentences
    new_sentence_cat = sentence_marker_column
    new_sentence_match = re.compile(sentence_marker_regex)

    data_iterator, _ = get_iterator_and_processor()

    # Apply normalization
    if isinstance(data_iterator.tokenizer, MemorizingTokenizer):
        for anno in annotation_lists:
            anno["form"] = data_iterator.tokenizer.replacer(anno["form"])

    # Transform sequence into group of sentences
    sentences = [[]]
    for tok in annotation_lists:
        if new_sentence_match.match(tok[new_sentence_cat]):
            sentences[-1].append(tok)
            sentences.append([])
        else:
            sentences[-1].append(tok)

    # Excluding tokens
    new_sentences = []
    for sentence in sentences:
        if not sentence:
            continue

        nb_tokens = [data["form"] for data in sentence]
        toks, excluded_ids = data_iterator.exclude_tokens(nb_tokens)
        new_sentences.append([
            anno
            for anno_id, anno in enumerate(sentence)
            if anno_id not in excluded_ids
        ])

    return new_sentences


def write_eval_file(filename, sentences: List[List[Dict[str, str]]]):
    with open(filename, "w") as f:
        headers = list(sentences[0][0].keys())
        f.write("\t".join(headers)+"\n")
        for sentence in sentences:
            for token in sentence:
                f.write("\t".join([token[head] for head in headers])+"\n")
            f.write("\n")

    return len(sentences)