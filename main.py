import csv
from pathlib import Path
from typing import NamedTuple

import inquirer
from tqdm import tqdm

from naver_session import NaverSession
from naver_vocab import NaverVocab
from naver_vocab_book import NaverVocabBook


def inquire_bool(message: str) -> bool:
    questions = [inquirer.Confirm("temp", message=message)]
    answers = inquirer.prompt(questions)
    return answers["temp"]


def inquire_is_session_load():
    return inquire_bool("세션을 불러오시겠습니까?")


def inquire_is_session_save():
    return inquire_bool("세션을 저장하시겠습니까?")


def inquire_quit():
    return inquire_bool("종료하시겠습니까?")


def inquire_is_download_pron_files():
    return inquire_bool(
        "발음 파일을 다운로드하시겠습니까? (CSV에 저장된 파일의 경로가 추가됩니다(ANKI에서 사용))"
    )


def inquire_examples():
    return inquire_bool("예문을 추가 하시겠습니까? (CSV에 예문이 추가됩니다)")


def inquire_path(message: str, is_directory: bool = False) -> Path:
    questions = [inquirer.Path("path", message=message)]
    answers = inquirer.prompt(questions)
    path = Path(answers["path"])

    if is_directory:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

    return path


def inquire_sesion_file_path():
    return inquire_path("세션 파일 경로를 입력하세요")


def inquire_csv_file_path():
    return inquire_path("CSV 파일 경로를 입력하세요")


def inquire_pron_folder_path():
    return inquire_path("발음 파일 폴더 경로를 입력하세요", is_directory=True)


def inquire_username_and_password() -> tuple[str, str]:
    questions = [
        inquirer.Text("username", message="네이버 아이디를 입력하세요"),
        inquirer.Password("password", message="네이버 비밀번호를 입력하세요"),
    ]
    answers = inquirer.prompt(questions)
    return answers["username"], answers["password"]


def inquire_book_type() -> NaverVocabBook.Type:
    questions = [
        inquirer.List(
            "book_type",
            message="사전을 선택하세요",
            choices=[
                ("영한사전", NaverVocabBook.Type.ENKO),
                ("일한사전", NaverVocabBook.Type.JAKO),
                ("중한사전", NaverVocabBook.Type.ZHKO),
            ],
        ),
    ]
    answers = inquirer.prompt(questions)
    return NaverVocabBook.Type(answers["book_type"])


def inquire_book_id(books: list[NaverVocabBook]) -> str:
    questions = [
        inquirer.List(
            "book_id",
            message="단어장을 선택하세요",
            choices=[(book.book_name, book.book_id) for book in books],
        ),
    ]
    answers = inquirer.prompt(questions)
    return answers["book_id"]


def get_session():
    try:
        if inquire_is_session_load():
            session_file_path = inquire_sesion_file_path()
            return NaverSession.from_file(session_file_path)

    except FileNotFoundError:
        print("세션 파일을 찾지 못했습니다. 로그인을 진행합니다.")

    if inquire_is_session_save():
        session_file = inquire_sesion_file_path()

    username, password = inquire_username_and_password()
    session = NaverSession.login(username, password)
    session.save(session_file)

    return session


class PronFileTuple(NamedTuple):
    vocab_id: str
    path: Path
    link: str


def _download_pron_files(session: NaverSession, file_tuples: list[PronFileTuple]):
    download_tqdm = tqdm(file_tuples)
    download_tqdm.set_description("발음 파일을 다운로드하는 중")
    for file_tuple in download_tqdm:
        with open(file_tuple.path, "wb") as f:
            f.write(session.session.get(file_tuple.link).content)


def _get_front_and_back(
    book_type: NaverVocabBook.Type, vocab: NaverVocab
) -> tuple[str, str]:
    match book_type:
        case NaverVocabBook.Type.JAKO | NaverVocabBook.Type.ENKO:
            return (vocab.word, f"{vocab.meaning}")

        case NaverVocabBook.Type.ZHKO:
            return (vocab.word, f"{vocab.pron}<br/>{vocab.meaning}")

        case _:
            raise NotImplementedError


def main():
    session = get_session()

    while True:
        book_type = inquire_book_type()

        books = NaverVocabBook.get_book_list(session, book_type)

        book_id = inquire_book_id(books)

        selected_book = NaverVocabBook.get_book_from_id(session, book_id, book_type)
        selected_book.load_vocabs(session)

        vocabs = selected_book.vocabs
        assert vocabs

        csv_file_path = inquire_csv_file_path()
        extra_columns: dict[str, tuple[str, ...]] = {
            vocab.id: tuple() for vocab in vocabs
        }

        if inquire_is_download_pron_files():

            def _add_file_prefix(path: str):
                return f"{csv_file_path.stem}-{path}"

            folder_path = inquire_pron_folder_path()

            file_tuple_tqdm = tqdm(vocabs)
            file_tuple_tqdm.set_description("발음 파일 링크를 가져오는 중")
            file_tuples = [
                PronFileTuple(
                    vocab_id=vocab.id,
                    path=folder_path.joinpath(Path(_add_file_prefix(file_name))),
                    link=link,
                )
                for vocab in file_tuple_tqdm
                if (link := vocab.get_pron_file_link(session))
                and (file_name := vocab.get_pron_file_name())
            ]

            _download_pron_files(session, file_tuples)

            for file_tuple in file_tuples:
                extra_columns[file_tuple.vocab_id] += (
                    f"[sound:{file_tuple.path.name}]",
                )

        if inquire_examples():
            for vocab in vocabs:
                extra_columns[vocab.id] += (
                    vocab.examples[0] if vocab.examples else "",
                )

        with open(csv_file_path, "w", encoding="utf8") as f:
            wr = csv.writer(f)

            for vocab in vocabs:
                wr.writerow(
                    _get_front_and_back(book_type, vocab) + extra_columns[vocab.id]
                )

        print(f"{len(vocabs)}개 단어를 {csv_file_path}에 저장했습니다.")

        if inquire_quit():
            break


if __name__ == "__main__":
    main()
