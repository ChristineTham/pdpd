"""Compile HTML data for Russian to Pāḷi dictionary."""

import re

from css_html_js_minify import css_minify
from mako.template import Template
from minify_html import minify
from rich import print
from sqlalchemy.orm import Session
from typing import List, Tuple
from dps.tools.paths_dps import DPSPaths

from export_dpd_ru import render_header_templ

from db.models import DpdHeadwords
# from db.models import DpdRoots
from tools.tic_toc import bip, bop
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
# from tools.configger import config_test
from tools.utils import RenderResult, RenderedSizes, default_rendered_sizes
from sqlalchemy.orm import joinedload


def generate_epd_html(db_session: Session, pth: ProjectPaths, dpspth: DPSPaths) -> Tuple[List[RenderResult], RenderedSizes]:
    """generate html for english to pali dictionary"""

    size_dict = default_rendered_sizes()

    print("[green]generating epd html")

    dpd_db: list = db_session.query(DpdHeadwords).options(joinedload(DpdHeadwords.ru)).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
    dpd_db_length = len(dpd_db)

    # roots_db: list = db_session.query(DpdRoots).all()
    # roots_db_length = len(roots_db)

    epd: dict = {}
    pos_exclude_list = ["abbrev", "cs", "letter", "root", "suffix", "ve"]

    with open(pth.epd_css_path) as f:
        epd_css: str = f.read()

    epd_css = css_minify(epd_css)

    header_templ = Template(filename=str(dpspth.header_templ_path))
    header = render_header_templ(
        pth, css=epd_css, js="", header_templ=header_templ)

    bip()
    for counter, i in enumerate(dpd_db):
        ru_meanings_list = []

        # Generate ru-pali
        if (
            i.ru and
            i.ru.ru_meaning and 
            i.pos not in pos_exclude_list
        ):
            
            i.ru.ru_meaning = re.sub(r"\?\?", "", i.ru.ru_meaning)

            # remove all space brackets
            ru_meanings_clean = re.sub(r" \(.+?\)", "", i.ru.ru_meaning)
            # remove all brackets space
            ru_meanings_clean = re.sub(r"\(.+?\) ", "", ru_meanings_clean)
            # remove space at start and fin
            ru_meanings_clean = re.sub(r"(^ | $)", "", ru_meanings_clean)
            # remove double spaces
            ru_meanings_clean = re.sub(r"  ", " ", ru_meanings_clean)
            # remove space around ;
            ru_meanings_clean = re.sub(r" ;|; ", ";", ru_meanings_clean)
            # remove т.д.
            ru_meanings_clean = re.sub(r"т\.д\. ", "", ru_meanings_clean)
            # remove !
            ru_meanings_clean = re.sub(r"!", "", ru_meanings_clean)
            # remove ?
            ru_meanings_clean = re.sub(r"\\?", "", ru_meanings_clean)
            ru_meanings_list = ru_meanings_clean.split(";")

            for ru_meaning in ru_meanings_list:
                if ru_meaning in epd.keys():
                    epd_string = f"{epd[ru_meaning]}<br><b class = 'epd'>{i.lemma_clean}</b> {i.pos}. {i.ru.ru_meaning}"
                    epd[ru_meaning] = epd_string

                if ru_meaning not in epd.keys():
                    epd_string = f"<b class = 'epd'>{i.lemma_clean}</b> {i.pos}. {i.ru.ru_meaning}"
                    epd.update(
                        {ru_meaning: epd_string})

        # Extract sutta number from i.meaning_2 and use it as key in epd
        def extract_sutta_numbers(meaning_2):
            unified_pattern = r"\(([A-Z]+)\s?([\d\.]+)(-\d+)?\)|([A-Z]+)[\s]?([\d\.]+)(-\d+)?"
            match = re.finditer(unified_pattern, meaning_2)
            combined_numbers = []

            for m in match:
                prefix = m.group(1) if m.group(1) else m.group(3)
                number = m.group(2) if m.group(2) else m.group(4)
                combined_number_without_space = f"{prefix}{number}" if prefix and number else None
                combined_number_with_space = f"{prefix} {number}" if prefix and number else None

                if '.' in number:
                    combined_number_with_colon_with_space = f"{prefix} {number.replace('.', ':')}" if prefix and number else None
                    combined_number_with_colon_without_space = f"{prefix}{number.replace('.', ':')}" if prefix and number else None
                else:
                    combined_number_with_colon_with_space = None
                    combined_number_with_colon_without_space = None

                combined_numbers.extend([combined_number_without_space, combined_number_with_space, combined_number_with_colon_with_space, combined_number_with_colon_without_space])

            return combined_numbers

        def update_epd(epd, combined_numbers, i):
            for combined_number in combined_numbers:
                if combined_number:
                    number_link = i.source_link_sutta
                    if number_link:
                        anchor_link = f'<a href="{number_link}">link</a>'
                        epd_string = f"<b class='epd'>{i.lemma_clean}</b>. {i.meaning_2} {anchor_link}"
                    else:
                        epd_string = f"<b class='epd'>{i.lemma_clean}</b>. {i.meaning_2}"

                    if combined_number in epd.keys():
                        epd[combined_number] += f"<br>{epd_string}"
                    else:
                        epd.update({combined_number: epd_string})

        if (
            i.meaning_2 and 
            (i.family_set.startswith("suttas of") or 
            i.family_set == "bhikkhupātimokkha rules" or 
            i.family_set == "chapters of the Saṃyutta Nikāya")
        ):
            combined_numbers = extract_sutta_numbers(i.meaning_2)
            update_epd(epd, combined_numbers, i) 

        if counter % 10000 == 0:
            print(f"{counter:>10,} / {dpd_db_length:<10,} {i.lemma_1[:20]:<20} {bop():>10}")
            bip()

    # TODO after adding ru meaning for roots incluad them here

    # print("[green]adding roots to epd")

    # for counter, i in enumerate(roots_db):

    #     root_meanings_list: list = i.root_meaning.split(", ")

    #     for root_meaning in root_meanings_list:
    #         if root_meaning in epd.keys():
    #             epd_string = f"{epd[root_meaning]}<br><b class = 'epd'>{i.root}</b> root. {i.root_meaning}"
    #             epd[root_meaning] = epd_string

    #         if root_meaning not in epd.keys():
    #             epd_string = f"<b class = 'epd'>{i.root}</b> root. {i.root_meaning}"
    #             epd.update(
    #                 {root_meaning: epd_string})

    #     if counter % 250 == 0:
    #         print(f"{counter:>10,} / {roots_db_length:<10,} {i.root:<20} {bop():>10}")
    #         bip()

    print("[green]compiling epd html")

    epd_data_list: List[RenderResult] = []

    for counter, (word, html_string) in enumerate(epd.items()):
        html = header
        size_dict["epd_header"] += len(header)

        html += "<body>"
        html += f"<div class ='epd'><p>{html_string}</p></div>"
        html += "</body></html>"
        size_dict["epd"] += len(html) - len(header)

        html = minify(html)

        res = RenderResult(
            word = word,
            definition_html = html,
            definition_plain = "",
            synonyms = [],
        )

        epd_data_list.append(res)

    return epd_data_list, size_dict
