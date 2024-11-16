import enum
import re

# as per recommendation from @freylis, compile once only
RE_HTML = re.compile(r"<.*?>")
RE_PARENTHESIS = re.compile(r"\((?:[^)(]|\([^)(]*\))*\)")
RE_BRACKET = re.compile(r"\[(?:[^\]\[]|\[[^\]\[]*\])*\]")
RE_PARENTHESIS_HANGUL = re.compile(r"\(([ㄱ-ㅎ가-힣ㅏ-ㅣ\s]+)\)")
RE_HANGUL = re.compile(r"[가-힣]+")
RE_KANJI = re.compile("[\u4e00-\u9fff\s]+")
RE_HIRA = re.compile("[\u3040-\u309fー\s]+")
RE_KATA = re.compile("[\u30a0-\u30ff\s]+")
RE_JAPANESE = re.compile("[\u3040-\u30ff\u30a0-\u30ffー\s]+")
RE_HIRA_KATA = re.compile("[\u3040-\u30ffー\s]+")


class RegexPattern(enum.Enum):
    HTML = RE_HTML
    PARENTHESIS = RE_PARENTHESIS
    BRACKET = RE_BRACKET
    PARENTHESIS_HANGUL = RE_PARENTHESIS_HANGUL
    HANGUL = RE_HANGUL
    KANJI = RE_KANJI
    HIRA = RE_HIRA
    KATA = RE_KATA
    JAPANESE = RE_JAPANESE
    HIRA_KATA = RE_HIRA_KATA


def get(raw: str, *, pattern: RegexPattern):
    return "".join(re.findall(pattern.value, raw))


def clean(raw: str, *, pattern: RegexPattern):
    while True:
        output = re.sub(pattern.value, "", raw)

        if output == raw:
            return output

        raw = output


def get_first_item(raw):
    return raw.split(";")[0].split(",")[0].split(".")[0].split("·")[0].strip()
