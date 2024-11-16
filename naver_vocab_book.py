import enum
import json
from dataclasses import dataclass, field
from typing import cast

from naver_session import NaverSession
from naver_vocab import NaverVocab


class NaverVocabBookResponse:
    id: str
    name: str
    wordCount: int


class NaverVocabBookListDataResponse:
    m_total: int
    m_page: int
    m_pagesize: int
    m_start: int
    m_end: int
    m_totalPage: int
    m_items: list[NaverVocabBookResponse]


class NaverVocabBookListResponse:
    data: NaverVocabBookListDataResponse


@dataclass
class NaverVocabBook:
    class Type(enum.StrEnum):
        JAKO = "jakodict"  # 일한사전
        ZHKO = "zhkodict"  # 중한사전
        ENKO = "enkodict"  # 영한사전

    book_id: str
    book_name: str
    book_type: Type
    vocabs: list[NaverVocab] | None = field(init=False, default=None)

    @staticmethod
    def get_book_list_response(naver_session: NaverSession, book_type: Type):
        # FIXME: 편의상 처음 100개만 확인함
        vocab_lists_text = naver_session.session.get(
            f"https://learn.dict.naver.com/gateway-api/{book_type}/mywordbook/wordbook/list.dict?page={1}&page_size={100}&st=0&domain=naver"
        )

        return cast(NaverVocabBookListResponse, json.loads(vocab_lists_text.text))

    @staticmethod
    def get_book_list(naver_session: NaverSession, book_type: Type):
        return [
            NaverVocabBook(
                book_id=item["id"], book_type=book_type, book_name=item["name"]
            )
            for item in NaverVocabBook.get_book_list_response(naver_session, book_type)[
                "data"
            ]["m_items"]
        ]

    @staticmethod
    def get_book_from_id(naver_session: NaverSession, book_id: str, book_type: Type):
        return next(
            (
                b
                for b in NaverVocabBook.get_book_list(naver_session, book_type)
                if b.book_id == book_id
            )
        )

    def load_vocabs(self, naver_session: NaverSession):
        self.vocabs = NaverVocab.get_vocabs(naver_session, self)
        return self
