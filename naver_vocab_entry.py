import functools
from typing import TYPE_CHECKING, TypedDict

import utils
from utils import RegexPattern

if TYPE_CHECKING:
    from naver_vocab_book import NaverVocabBook


class NaverVocabEntryResponseMemberPron(TypedDict):
    pron_id: str
    pron_symbol: str
    pron_alias: str
    pron_type: str
    korean_pron_symbol: str
    order_seq: int
    male_pron_file: str
    female_pron_file: str


class NaverVocabEntryResponseMember(TypedDict):
    member_id: str
    entry_name: str
    super_script: str
    entry_importance: str
    origin_language: str
    kanji: str
    prons: list[NaverVocabEntryResponseMemberPron]


class NaverVocabEntryResponseEntryMeanExampleItem(TypedDict):
    origin_example: str
    show_example: str


class NaverVocabEntryResponseEntryMean(TypedDict):
    mean_id: str
    part_id: str
    part_code: str
    part_name: str
    mean_type: str
    show_mean: str
    examples: list[NaverVocabEntryResponseEntryMeanExampleItem]


class NaverVocabEntryResponseEntry:
    entry_id: str
    members: list[NaverVocabEntryResponseMember]
    means: list[NaverVocabEntryResponseEntryMean]


class NaverVocabEntryResponse:
    entry: NaverVocabEntryResponseEntry


def get_word(book_type: "NaverVocabBook.Type", member: NaverVocabEntryResponseMember):
    from naver_vocab_book import NaverVocabBook

    match book_type:
        case NaverVocabBook.Type.JAKO:
            cleaned = functools.reduce(
                lambda acc, cur: utils.clean(acc, pattern=cur),
                [
                    RegexPattern.PARENTHESIS,
                    RegexPattern.HTML,
                ],
                member["kanji"],
            )

            word = utils.get_first_item(cleaned)

            return word

        case NaverVocabBook.Type.ZHKO | NaverVocabBook.Type.ENKO:
            return member["entry_name"]

        case _:
            raise NotImplementedError


def get_meaning(
    book_type: "NaverVocabBook.Type", mean: NaverVocabEntryResponseEntryMean
):
    from naver_vocab_book import NaverVocabBook

    match book_type:
        case NaverVocabBook.Type.JAKO:
            cleaned = functools.reduce(
                lambda acc, cur: utils.clean(acc, pattern=cur),
                [
                    RegexPattern.HTML,
                ],
                mean["show_mean"],
            )

            return utils.get_first_item(cleaned)

        case NaverVocabBook.Type.ZHKO | NaverVocabBook.Type.ENKO:
            return mean["show_mean"]

        case _:
            raise NotImplementedError


def get_pron(book_type: "NaverVocabBook.Type", member: NaverVocabEntryResponseMember):
    from naver_vocab_book import NaverVocabBook

    match book_type:
        case NaverVocabBook.Type.JAKO:
            cleaned = functools.reduce(
                lambda acc, cur: utils.clean(acc, pattern=cur),
                [
                    RegexPattern.PARENTHESIS,
                    RegexPattern.PARENTHESIS_HANGUL,
                    RegexPattern.HTML,
                ],
                member["entry_name"],
            )

            word = utils.get_first_item(cleaned)

            return word

        case NaverVocabBook.Type.ZHKO:
            pron = member["prons"][0]
            return pron["pron_symbol"]

        case NaverVocabBook.Type.ENKO:
            return ""


def get_pron_file(
    book_type: "NaverVocabBook.Type", member: NaverVocabEntryResponseMember
):
    from naver_vocab_book import NaverVocabBook

    pron = member["prons"][0]

    match book_type:
        case NaverVocabBook.Type.JAKO | NaverVocabBook.Type.ENKO:
            return None

        case NaverVocabBook.Type.ZHKO:
            return pron["male_pron_file"] or pron["female_pron_file"] or None

        case _:
            raise NotImplementedError


def get_valid_mean(means: list[NaverVocabEntryResponseEntryMean]):
    return next(mean for mean in means if mean["show_mean"] != "")


def get_valid_examples_for_mean(mean: NaverVocabEntryResponseEntryMean):
    examples = [
        example.get("origin_example", example.get("show_example"))
        for example in mean["examples"]
    ]
    examples = [item for item in examples if item]
    return examples


class NaverVocabEntryDict(TypedDict):
    word: str
    meaning: str
    pron: str
    pron_file: str | None
    remarks: str | None
    examples: list[str]


def get_entry_dict(
    book_type: "NaverVocabBook.Type", entry_dict: NaverVocabEntryResponse
):
    member = entry_dict["entry"]["members"][0]
    mean = get_valid_mean(entry_dict["entry"]["means"])
    examples = get_valid_examples_for_mean(mean)

    return NaverVocabEntryDict(
        word=get_word(book_type, member),
        meaning=get_meaning(book_type, mean),
        pron=get_pron(book_type, member),
        pron_file=get_pron_file(book_type, member),
        remarks=None,
        examples=examples,
    )
