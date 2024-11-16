import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict, cast

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


@dataclass
class NaverVocab:
    id: str
    word: str
    meaning: str
    pron: str
    pron_file: str | None
    remarks: str | None = None

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

    @staticmethod
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

    @staticmethod
    def get_vocabs(naver_session: NaverSession, book: "NaverVocabBook"):
        cursor = None
        words: list[NaverVocab] = []

        while (
            (
                response := NaverVocab.get_words_response(
                    naver_session, book=book, cursor=cursor
                )
            )
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
