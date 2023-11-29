#! /usr/bin/env python
"""
Scrapes the MEGA digital library for the letters we are interested in,
and converts them into an acceptable `.csv` format.
"""

import requests as req
import json
import sys
from bs4 import BeautifulSoup
from typing import Dict, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

index_url = "https://megadigital.bbaw.de/briefe/index.xql?&offset="
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}


def dprint(s: str):
    "Debug print helper function"
    print(f"[DEBUG] {s}", file=sys.stderr)


def get_url(n: int) -> str:
    "Get the url of the `MEGA` index page given some integer."
    return index_url + str(n)


class LetterRetrievalError(Exception):
    """
    Exception for letter-retrieval exceptions specifically, to be
    thrown up the stack.
    """

    def __init__(self, msg: str):
        self.msg = msg


@dataclass
class LetterMeta:
    """
    Record type, the fields representing important later data to be used
    """
    date: str
    href: str


def get_metas(page: BeautifulSoup) -> List[LetterMeta]:
    """
    Retreive the metadata from each letter in the index, ignoring
    postulated letters
    """
    content = page.find(id="content")
    if not content:
        return []

    listing = content.find(class_="grid_11")
    if not listing:
        return []

    letters = listing.find(class_="letters")
    if not letters:
        return []

    metas = []

    for row in letters.find_all(class_="clickable-row"):
        href = "https://megadigital.bbaw.de/" + row.get("data-href")[6:] + "&view=l"
        date = row.find(class_="date").text
        metas.append(LetterMeta(date, href))

    return metas


@dataclass
class LetterContent:
    """
    Record containgin the contents of a given letter
    """
    date: str
    href: str
    title: str
    author: str
    text: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "meta-date": self.date,
            "meta-href": self.href,
            "meta-title": self.title,
            "meta-author": self.author,
            "meta-text": self.text
        }


def get_content(letter_meta: LetterMeta) -> LetterContent | None:
    response = req.get(letter_meta.href, headers=HEADERS)

    if response.status_code != 200:
        dprint(f"[get_content] Unable to retrieve data from {letter_meta.href}")
        return None
    else:
        page = BeautifulSoup(response.content, "html.parser")

        inner_summary = page.find(class_="boxInner erschlossen summary")
        if inner_summary:
            dprint(f"[get_content] {letter_meta.href} is posited, ignoring")
            return None
        
        inner_transkription = page.find(class_="grid_11 box whitebox")
        if inner_transkription is None:
            dprint(f"[get_content] {letter_meta.href} unknown format!")
            return None
        
        inner_contents = page.find(class_="boxInner transkription")
        if inner_contents is None:
            dprintf(f"[get_content] {href} no inner content!")
            return None
        
        header = page.find(class_="subnavbar").text
        text = inner_contents.text

        author = header.split("an")[0].strip()
        return LetterContent(letter_meta.date, letter_meta.href, header, author, text)


def get_letters(index_begin: int, index_end: int) -> List[LetterContent]:
    """
    Given `index_begin` and `index_end`, retrieves the letter content
    from the MEGA letter index.
    """
    # the maximum displayable amount of letters per index
    INDEX_STEP = 39

    letters = []

    for i in range(index_begin - 1, index_end, INDEX_STEP):
        url = get_url(i)
        dprint(f"[get_letters] Getting {url}")

        # Get the HTML of the index
        response = req.get(url, headers=HEADERS)

        # Handle the response
        if response.status_code != 200:
            raise LetterRetrievalError(
                f"Unable to get {url}, bad status code: {response.status_code}"
            )
        else:
            dprint(f"[get_letters] Successfly retrieved {url}")

            # Parse the html content
            page = BeautifulSoup(response.content, "html.parser")

            # Retrieve the date, author, and href
            letter_metas = get_metas(page)

            # For each href, create a make a new Letter object, with the data from the meta
            for meta in letter_metas:
                dprint(f"[get_letters] href: {meta.href}, date: {meta.date}, retrieving text content!")
                letter_content = get_content(meta)

                if letter_content is None:
                    continue
                else:
                    letters.append(letter_content)

    return letters

def csv_format(letters: List[LetterContent]):
    letter_dict = [letter.to_dict() for letter in letters]
    json.dump(letter_dict, sys.stdout)


INDEX_MIN = 0
INDEX_MAX = 1519 + 40


def check_index(idx: int):
    """
    Checks if the index provides is within the acceptable range.
    """
    assert (
        INDEX_MAX > idx
    ), f"[ERROR] index of {idx} expected to be less than maximum index {INDEX_MAX}"
    assert (
        INDEX_MIN <= idx
    ), f"[ERROR] index of {idx} expected to be greater than, or equal to, minimum index of {INDEX_MIN}"


def main() -> None:
    # Throw an error if there is nothing within the arguments provided
    if len(sys.argv) < 2:
        print("[USAGE] $ scraper.py <index_range>", file=sys.stderr)
        print(
            "     <index_range> := a number of the form 'x-y', where 'x' is the begining offset, and 'y' is the ending offset.",
            file=sys.stderr,
        )
        exit(-1)

    # Get the range of indices of letters
    index_range = sys.argv[1]
    index_begin, index_end = tuple(map(lambda x: int(x), index_range.split("-")))

    # Check if the indices are within the acceptable range, see `INDEX_MIN`, `INDEX_MAX`, and `check_index`
    check_index(index_begin)
    check_index(index_end)

    dprint(f"Using index_range of {index_begin}-{index_end}")

    letters = get_letters(index_begin, index_end)
    csv_format(letters)


if __name__ == "__main__":
    main()
