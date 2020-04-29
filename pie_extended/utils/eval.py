from pie_extended.cli.sub import get_tagger, get_imports, get_model
from pie_extended.tagger import ExtensibleTagger
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.models.lasla.imports import get_iterator_and_processor
from typing import List, Dict, Optional, Callable
import re


def read_test_file(
        test_file: str, tasks: List[str],
        use_function: Callable[[Dict[str, str]], Dict[str, str]]
) -> List[Dict[str, str]]:
    """

    :param test_file:
    :param tasks:
    :param use_function:
    :returns:

    """
    out = []
    with open(test_file) as f:
        for line_no, line in enumerate(f):
            data = line.strip().split()
            if not data:
                continue
            if line_no == 0:
                header = data
                continue
            data = use_function(dict(zip(header, data)))
            out.append({task: data[task] for task in ["token"]+tasks})

    return out


def process_parsed_data(
        annotation_lists: List[Dict[str, str]],
        sentence_marker_column: str = "token", sentence_marker_regex: str = r"^[.!?$]+$"
) -> List[List[Dict[str, str]]]:
    """

    :param annotation_lists: List of annotations in the form of a list of dict {task: value}
    :param sentence_marker_column: Column in which to look
    :param sentence_marker_regex: When matched, indicates end of sentence

    Returns
    -------

    """
    # Need to deal with sentences
    new_sentence_cat = sentence_marker_column
    new_sentence_match = re.compile(sentence_marker_regex)

    data_iterator, _ = get_iterator_and_processor()

    # Apply normalization
    if isinstance(data_iterator.tokenizer, MemorizingTokenizer):
        for anno in annotation_lists:
            anno["token"] = data_iterator.tokenizer.replacer(anno["token"])

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

        nb_tokens = [data["token"] for data in sentence]
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


def retroconvert_corrected_file(filename: str, model_name: str, out_file: str) -> int:
    tagger: ExtensibleTagger = get_tagger(model_name)
    tasks = [task for model, tasks in tagger.models for task in tasks]
    imports = get_imports(get_model(model_name))
    annotations = read_test_file(filename, tasks, use_function=imports.reverse_output)
    sentences = process_parsed_data(annotations)
    nb_sentences = write_eval_file(out_file, sentences)
    return nb_sentences
