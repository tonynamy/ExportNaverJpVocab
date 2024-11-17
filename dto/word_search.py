from pydantic import BaseModel


class WordSearchResultListMapFieldItemMeansCollectorItemMean(BaseModel):
    order: str
    value: str | None
    languageGroup: str | None
    languageGroupCode: str | None
    exampleOri: str | None
    exampleTrans: str | None
    encode: str


class WordSearchResultListMapFieldItemMeansCollectorItem(BaseModel):
    partOfSpeech: str | None
    partOfSpeech2: str | None
    partOfSpeechCode: str | None
    means: list[WordSearchResultListMapFieldItemMeansCollectorItemMean]


class WordSearchResultListMapFieldItemPhoneticSymbolListItem(BaseModel):
    symbolTypeCode: str | None
    symbolValue: str | None
    symbolFile: str | None


class WordSearchResultListMapFieldItem(BaseModel):
    rank: str
    entryId: str
    meansCollector: list[WordSearchResultListMapFieldItemMeansCollectorItem]
    searchPhoneticSymbolList: list[
        WordSearchResultListMapFieldItemPhoneticSymbolListItem
    ]
    vcode: str
    encode: str
    handleEntry: str


class WordSearchResultListMapField(BaseModel):
    query: str
    queryRevert: str
    items: list[WordSearchResultListMapFieldItem]


class WordSearchResultListMap(BaseModel):
    WORD: WordSearchResultListMapField


class WordSearchResultMap(BaseModel):
    searchResultListMap: WordSearchResultListMap


class WordSearchResult(BaseModel):
    searchResultMap: WordSearchResultMap
