"""Extract MW from Simsapa.
Export to GoldenDict, MDict and JSON."""

import json
import sqlite3

from rich import print

from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import sanskrit_sort_key
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc


def extract_mw_from_simsapa():
    """Query Simsapa DB for MW data."""
    print("[green]querying simspa db")

    simsapa_db_path = "../../.local/share/simsapa/assets/appdata.sqlite3"
    conn = sqlite3.connect(simsapa_db_path)
    c = conn.cursor()
    c.execute("""SELECT word, definition_html, synonyms FROM dict_words WHERE source_uid is 'mw'""")
    mw_data = c.fetchall()

    return mw_data

def main():
    tic()
    print("[bright_yellow]exporting mw to GoldenDict, MDict and JSON")

    pth = ProjectPaths()
    mw_data = extract_mw_from_simsapa()

    print("[green]making data list")
    mw_data_list = []
    for i in mw_data:
        headword, html, synonyms = i
        headword = headword.replace("ṁ", "ṃ")
        html = html.replace("ṁ", "ṃ")

        if "ṃ" in headword:
            synonyms = add_niggahitas([headword])
        else:
            synonyms = []

        mw_data_list.append({
            "word": headword, 
            "definition_html": html,
            "definition_plain": "",
            "synonyms": synonyms           
            })

    # sort into sanskrit alphabetical order
    mw_data_list = sorted(mw_data_list, key=lambda x: sanskrit_sort_key(x["word"]))

    # save as json
    print("[green]saving json")
    with open(pth.mw_json_path, "w") as file:
        json.dump(mw_data_list, file, indent=4, ensure_ascii=False)

    # save as goldendict
    print("[green]saving goldendict")

    # TODO find out more details, website etc

    bookname = "Monier Williams Sanskrit English Dicitonary 1899"
    description = "Monier Williams Sanskrit English Dicitonary 1899"
    author = "Sir Monier Monier Williams"
    website = ""

    ifo = ifo_from_opts({
            "bookname": bookname,
            "author": author,
            "description": description,
            "website": website
            })

    export_words_as_stardict_zip(mw_data_list, ifo, pth.mw_gd_path)

    # save as mdict
    print("[green]saving mdict")
    output_file = str(pth.mw_mdict_path)
    
    export_to_mdict(
        mw_data_list,
        output_file,
        bookname,
        f"{description}. {website}")

    toc()


if __name__ == "__main__":
    main()

