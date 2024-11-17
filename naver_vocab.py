import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict, cast
from urllib.parse import unquote_plus

import requests

from dto.word_search import WordSearchResult
from naver_session import NaverSession
from naver_vocab_entry import get_entry_dict

if TYPE_CHECKING:
    from naver_vocab_book import NaverVocabBook


class NaverVocabResponse(TypedDict):
    id: str
    entryId: str
    wordbookId: str
    name: str
    content: str


class NaverVocabListDataResponse(TypedDict):
    m_total: int
    over_last_page: bool
    next_cursor: str
    m_items: list[NaverVocabResponse]


class NaverVocabListResponse(TypedDict):
    data: NaverVocabListDataResponse


SEARCH_SIZE = 100


def get_words_response(
    naver_session: NaverSession,
    *,
    book: "NaverVocabBook",
    cursor: str | None = None,
):
    book_id = book.book_id

    if cursor is None:
        link = f"https://learn.dict.naver.com/gateway-api/{book.book_type}/mywordbook/word/list/search?wbId={book_id}&qt=0&st=0&page_size={SEARCH_SIZE}&domain=naver"
    else:
        link = f"https://learn.dict.naver.com/gateway-api/{book.book_type}/mywordbook/word/list/search?wbId={book_id}&qt=0&st=0&cursor={cursor}&page_size={SEARCH_SIZE}&domain=naver"

    vocabs_text = naver_session.session.get(link).text

    if not vocabs_text:
        return None

    return cast(NaverVocabListResponse, json.loads(vocabs_text))


def get_vocabs(naver_session: NaverSession, book: "NaverVocabBook"):
    cursor = None
    words: list[NaverVocab] = []

    while (
        (response := get_words_response(naver_session, book=book, cursor=cursor))
        and response["data"]
        and response["data"]["over_last_page"] is False
    ):
        words += [
            NaverVocab(
                id=item["id"],
                **get_entry_dict(book.book_type, json.loads(item["content"])),
            )
            for item in response["data"]["m_items"]
            if item["content"]
        ]

        cursor = response["data"]["next_cursor"]

    return words


# FIXME:
def get_dictionary_type(vocab_book_type: "NaverVocabBook.Type"):
    return vocab_book_type.value.rstrip("dict")


def get_vocab_from_word(
    naver_session: NaverSession, dict_type: str, word: str
) -> "NaverVocab | None":
    res = requests.get(
        f"https://dict.naver.com/api3/{dict_type}/search?query={word}",
        headers={
            "Referer": "https://dict.naver.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        },
    )

    json_result = res.json()

    with open(f"files/{word}.json", "w", encoding="utf-8") as f:
        json.dump(json_result, f)

    # with open(f"files/{word}.json", "r", encoding="utf-8") as f:
    #     json_result = json.load(f)

    result = WordSearchResult.model_validate(json_result)
    word_items = result.searchResultMap.searchResultListMap.WORD.items

    if not word_items:
        return None

    def _pron_rank(type_code: str):
        if type_code == "US∙GB":
            return 1

        if type_code == "US":
            return 2

        return 3

    word_item = word_items[0]
    mean = (
        (
            means[0]
            if (means := [item for item in collector[0].means if item.value])
            else None
        )
        if (collector := word_item.meansCollector)
        else None
    )
    symbol = (
        symbol_list[0]
        if (
            symbol_list := sorted(
                [
                    symbol
                    for symbol in word_item.searchPhoneticSymbolList
                    if symbol.symbolValue
                ],
                key=lambda x: _pron_rank(x.symbolTypeCode),
            )
        )
        else None
    )

    return NaverVocab(
        id=word_item.entryId,
        word=unquote_plus(word_item.encode),
        meaning=mean.value,
        pron=symbol.symbolValue if symbol else None,
        pron_file=symbol.symbolFile if symbol else None,
        examples=[unquote_plus(mean.encode)] if mean.encode else [],
    )


@dataclass
class NaverVocab:
    id: str
    word: str
    meaning: str
    pron: str
    pron_file: str | None
    remarks: str | None = None
    examples: list[str] | None = None

    def get_pron_file_name(self):
        return self.pron_file.split("/")[-1] if self.pron_file else None

    def get_pron_file_link(self, naver_session: NaverSession):
        if self.pron_file is None:
            return None
        res = naver_session.session.post(
            "https://learn.dict.naver.com/api/pronunLink.dict",
            data={"filePath": self.pron_file, "dmain": "naver"},
        )
        res_json = json.loads(res.text)
        return res_json["data"]["pronunLinkList"][0]
