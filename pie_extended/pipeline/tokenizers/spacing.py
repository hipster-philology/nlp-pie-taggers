from typing import List, Tuple

# How far (in characters) we accept to look ahead for a token when the text between the previous token and
# this one is not only whitespace (a token was rewritten by a normalizer, for example)
RESYNC_WINDOW = 40


def space_after(text: str, tokens: List[str], lower: bool = False) -> Tuple[List[bool], int]:
    """ Finds out, for each token, if it is followed by a space in the original text.

    Tokenizers throw away whitespace (`str.split`, inserted spaces around punctuation, sentence splitting...),
    so the tokens are aligned back, in order, on the original text.

    A token is followed by a space when the next character in the text is whitespace.
    At the very end of the text, we consider there is a space after (nothing is glued to the next token).

    :param text: Original text
    :param tokens: Tokens in the order they were found in the text, *before* any replacement. An empty string is
        a token that is not written in the text but moved from somewhere else (see below).
    :param lower: Whether the tokens were lowercased by the tokenizer
    :return: One boolean per token (True if a space follows), and the number of tokens that could not be located
        in the text (those are given True)

    >>> space_after("Arma uirumque: cano", ["Arma", "uirumque", ":", "cano"])
    ([True, False, True, True], 0)
    >>> space_after("Arma  uirumque\\n:cano.", ["Arma", "uirumque", ":", "cano", "."])
    ([True, True, False, False, True], 0)

    Case is ignored if the tokenizer lowered the input:

    >>> space_after("Arma uirumque", ["arma", "uirumque"], lower=True)
    ([True, True], 0)

    A token that is not written in the text (an empty string) is glued to the previous token. This is for tokenizers
    that detach a character from its word and output it after it (Armenian `Մի՞թե` -> `Միթե`, `՞`): the word is
    given with the whole written form (mark included), and the moved token with an empty string.

    >>> space_after("Մի՞թե այդ", ["Մի՞թե", "", "այդ"])
    ([False, True, True], 0)
    >>> space_after("Ո՞րն էր", ["Ո՞րն", "", "էր"])
    ([False, True, True], 0)

    A token we cannot find does not prevent the next ones from being aligned:

    >>> space_after("Arma (uirumque) cano", ["Arma", "(", "ZZZ", ")", "cano"])
    ([True, False, True, True, True], 1)
    """
    haystack = text
    if lower and len(text.lower()) == len(text):
        haystack = text.lower()
        tokens = [token.lower() for token in tokens]

    out: List[bool] = []
    missed = 0
    position = 0
    length = len(haystack)

    for token in tokens:
        if token == "":
            # Not written in the text: it ends where the previous token ends
            if out:
                out[-1] = False
            out.append(position >= length or haystack[position].isspace())
            continue

        index = haystack.find(token, position)
        # We only trust a match that is directly after the previous token (modulo whitespace),
        #  or that is close enough to be a rewritten token.
        if index != -1 and haystack[position:index].strip() and index - position > RESYNC_WINDOW:
            index = -1

        if index == -1:
            missed += 1
            out.append(True)
            continue

        position = index + len(token)
        out.append(position >= length or haystack[position].isspace())

    return out, missed
