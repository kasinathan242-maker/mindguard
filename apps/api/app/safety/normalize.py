"""Text normalisation shared by the safety rules and the safety classifier.

The goal is to make one pattern match the many ways people actually type: curly quotes,
dropped apostrophes, chat contractions ("wanna", "im", "u"), stretched letters ("sooo"), and
laughter emoji. Tamil script is left as typed apart from Unicode NFC normalisation.
"""

import re
import unicodedata

# Curly, reversed and acute apostrophes, backtick and the ASCII apostrophe.
_APOSTROPHES = re.compile("[" + "".join(map(chr, (0x2018, 0x2019, 0x201B, 0x60, 0xB4, 0x27))) + "]")
_LAUGH_EMOJI = re.compile(r"[\U0001F602\U0001F923\U0001F480\U0001F606\U0001F639]")
_STRETCHED = re.compile(r"([a-z])\1{2,}")
_SPACES = re.compile("[ " + chr(0x09) + chr(0xA0) + "]+")  # space, tab, no-break space
# Keep letters, digits, Tamil (U+0B80-U+0BFF), whitespace and clause punctuation.
_NOISE = re.compile(r"[^\w" + chr(0x0B80) + "-" + chr(0x0BFF) + r"\s.!?;,\n-]")

# Applied word-by-word after apostrophes are removed ("don't" -> "dont" -> "do not").
_CONTRACTIONS: dict[str, str] = {
    "im": "i am",
    "ive": "i have",
    "id": "i would",
    "dont": "do not",
    "doesnt": "does not",
    "didnt": "did not",
    "cant": "can not",
    "cannot": "can not",
    "wont": "will not",
    "wouldnt": "would not",
    "couldnt": "could not",
    "shouldnt": "should not",
    "isnt": "is not",
    "aint": "am not",
    "whats": "what is",
    "its": "it is",
    "thats": "that is",
    "theyd": "they would",
    "theyll": "they will",
    "wanna": "want to",
    "gonna": "going to",
    "gotta": "got to",
    "u": "you",
    "ur": "your",
    "rn": "right now",
    "pls": "please",
    "plz": "please",
    "kms": "kill myself",
    "kys": "kill yourself",
    "meself": "myself",
    "mysel": "myself",
}
_WORD = re.compile(r"[a-z]+")


def _expand(match: re.Match[str]) -> str:
    word = match.group()
    return _CONTRACTIONS.get(word, word)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    text = _LAUGH_EMOJI.sub(" lol ", text)
    text = _APOSTROPHES.sub("", text)
    text = _NOISE.sub(" ", text)
    text = _STRETCHED.sub(r"\1\1", text)
    text = text.replace("my self", "myself")
    text = _WORD.sub(_expand, text)
    return _SPACES.sub(" ", text).strip()


_CLAUSE_BREAK = re.compile(
    r"[.!?;\n]+|,\s*(?=but\b|though\b|aana\b)|\bbut\b|\bthough\b|\baana\b|ஆனா(?:ல்)?"
)


def clauses(normalised: str) -> list[str]:
    """Split into clauses so a negation in one clause cannot cancel a statement in another."""
    return [part.strip(" ,") for part in _CLAUSE_BREAK.split(normalised) if part.strip(" ,")]
