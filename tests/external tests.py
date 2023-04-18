#!/usr/bin/env python3

"""External tests examine the relationship between a row's data and other
    rows in the db. """

import re

from typing import Dict
from rich import print
from json import loads

from db.get_db_session import get_db_session
from db.models import PaliRoot
from db.models import PaliWord
from db.models import FamilyRoot
from db.models import FamilyCompound
from db.models import DerivedData
from tools.pali_sort_key import pali_sort_key
from tools.timeis import tic, toc
from tools.pali_alphabet import consonants

# generic tests that return tuples of results
# that can be printed or displayed in gui

# run through the db once generting all the necessary sets and lists
# use those lists in individual fucntions
# modularize everything
# describe each test in detail


def run_external_tests():

    print("[bright_yellow]run external db tests")
    db_session = get_db_session("dpd.db")

    print("[green]make searches")
    searches: dict = make_searches(db_session)

    for item in searches:
        print(item, len(searches[item]))
    print()

    # tests
    results_list = []
    results_list.append(family_compound_no_number(searches))
    results_list.append(suffix_does_not_match_pali_1(searches))
    results_list.append(construction_line1_does_not_match_pali_1(searches))
    results_list.append(construction_line2_does_not_match_pali_1(searches))
    results_list.append(pali_1_missing_a_number(searches))
    results_list.append(pali_1_contains_extra_number(searches))
    results_list.append(derived_from_not_in_headwords(searches))
    results_list.append(pali_words_in_english_meaning(searches))
    results_list.append(derived_from_not_in_family_compound(searches))
    results_list.append(pos_does_not_equal_grammar(searches))
    results_list.append(pos_does_not_equal_pattern(searches))
    results_list.append(base_contains_extra_star(searches))
    results_list.append(base_is_missing_star(searches))
    results_list.append(root_x_root_family_mismatch(searches))
    results_list.append(root_x_construction_mismatch(searches))
    results_list.append(family_root_x_construction_mismatch(searches))
    results_list.append(root_key_x_base_mismatch(searches))
    results_list.append(root_sign_x_base_mismatch(searches))
    results_list.append(root_sign_x_base_mismatch(searches))
    results_list.append(root_base_x_construction_mismatch(searches))
    results_list.append(wrong_prefix_in_family_root(searches))

    for name, result, count, solution in results_list:
        print(f"[green]{name.replace('_', ' ')} [{count}]")
        if count > 0:
            print(f"solution: {solution}")
            print(result)
            print()


def make_searches(db_session) -> Dict[str, list]:
    """Make a dict of all searches to be used by functions."""

    searches = {}

    paliword = db_session.query(PaliWord).all()
    searches["paliword"] = paliword

    paliroots = db_session.query(PaliRoot).all()
    searches["paliroots"] = paliroots

    compound_families = db_session.query(FamilyCompound).all()
    searches["compound_families"] = compound_families

    deriveddata = db_session.query(DerivedData).all()
    searches["derived_data"] = deriveddata

    return searches


def regex_results(results: list) -> str:
    """Take a list of results and return a regex search string or None"""

    if results != []:
        results = results[:10]
        regex_string = r"/\b("
        for result in results:
            if result == results[0]:
                regex_string += f"{result}"
            else:
                regex_string += f"|{result}"
        regex_string += r")\b/"
    else:
        regex_string = None

    return regex_string


def family_compound_no_number(searches: dict) -> tuple:
    """Find words in compound_family which should have a number
    because there is more than one meaning."""

    # make a list of all compound_family with numbers
    compound_family_numbered = set()
    results = []

    for i in searches["paliword"]:
        for fc in i.family_compound.split(" "):
            if re.findall(r"\d", fc):
                fc = re.sub(r"\d", "", fc)
                compound_family_numbered.add(fc)

    for i in searches["paliword"]:
        for fc in i.family_compound.split(" "):
            if fc in compound_family_numbered:
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "family_compound_no_number"
    solution = "add a number to family_compound with multiple meanings"
    
    return name, results, length, solution


def suffix_does_not_match_pali_1(searches: dict) -> tuple:
    """Suffix last letter does not match the last letter of pali_1."""

    results = []
    exceptions = [
        "adhipa", "bavh", "labbhā", "munī", "gatī", "visesi", "khantī",
        "sāraṇī", "bahulī", "yānī 2"]

    for i in searches["paliword"]:
        if i.suffix != "" and i.pali_1 not in exceptions:
            suffix_lastletter = i.suffix[-1]
            pali_clean_lastletter = i.pali_clean[-1]

            if suffix_lastletter != pali_clean_lastletter:
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "suffix_does_not_match_pali_1"
    solution = "change suffix"

    return name, results, length, solution


def construction_line1_does_not_match_pali_1(searches: dict) -> tuple:
    """The end of construction line 1 does not match the end of pali_1."""

    results = []
    exceptions = [
        "abhijaññā", "acc", "adhipa", "aññā 2", "aññā 3", "anujaññā",
        "anupādā", "attanī", "chettu", "devāna", "dubbalī", "gāmaṇḍala 2.1",
        "gatī", "jaññā 2", "kayirā", "khaṇitti", "koṭṭhāsa 1", "koṭṭhāsa 2",
        "koṭṭhāsa 3", "labbhā", "lokasmi", "munī", "nājjhosa", "nānujaññā",
        "nāsiṃsatī", "nāsīsatī", "natthī", "paralokavajjabhayadassāvine",
        "paresa", "pariññā 2", "paṭivadeyyu", "phuseyyu", "sabbadhammāna",
        "saḷ", "sat 1", "sat 2", "upādā", "vijaññā", "visesi", "govinda",
        "sivathikā", "sīvathikā", "sakad", "bahulī"]

    for i in searches["paliword"]:
        if i.pali_1 not in exceptions:
            if i.construction and i.meaning_1:
                const_lastlettter = re.sub("\n.+", "", i.construction)[-1]
                if i.pali_clean[-1] != const_lastlettter:
                    results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "construction_line1_does_not_match_pali_1"
    solution = "edit construction or add to exceptions"

    return name, results, length, solution


def construction_line2_does_not_match_pali_1(searches: dict) -> tuple:
    """The end of construction line 1 does not match the end of pali_1."""

    results = []

    for i in searches["paliword"]:
        if "\n" in i.construction and i.meaning_1:
            const_lastlettter = i.construction[-1]
            if i.pali_clean[-1] != const_lastlettter:
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "construction_line2_does_not_match_pali_1"
    solution = "edit construction line2"

    return name, results, length, solution


def pali_1_missing_a_number(searches: dict) -> tuple:
    """pali_1 does not contain a number, but should"""

    results = []
    clean_headwords_count: dict = {}

    for i in searches["paliword"]:
        if i.pali_clean not in clean_headwords_count:
            clean_headwords_count[i.pali_clean] = 1
        else:
            clean_headwords_count[i.pali_clean] += 1

    for i in searches["paliword"]:
        if not re.findall(r"\d", i.pali_1):
            if clean_headwords_count[i.pali_clean] > 1:
                results += [i.pali_clean]

    length = len(results)
    results = regex_results(results)
    name = "pali_1_missing_a_number"
    solution = "add a number to pali_1"

    return name, results, length, solution


def pali_1_contains_extra_number(searches: dict) -> tuple:
    """pali_1 contains a number, but shouldn't"""

    results = []
    clean_headwords_count: dict = {}

    for i in searches["paliword"]:
        if i.pali_clean not in clean_headwords_count:
            clean_headwords_count[i.pali_clean] = 1
        else:
            clean_headwords_count[i.pali_clean] += 1

    for i in searches["paliword"]:
        if re.findall(r"\d", i.pali_1):
            if clean_headwords_count[i.pali_clean] == 1:
                results += [i.pali_clean]

    length = len(results)
    results = regex_results(results)
    name = "pali_1_contains_extra_number"
    solution = "delete number from pali_1"
    return name, results, length, solution


def derived_from_not_in_headwords(searches: dict) -> tuple:
    """Test if derived from is not found in pali_1."""

    results = []
    clean_headwords: set = set()
    root_families: set = set()

    for i in searches["paliword"]:
        clean_headwords.add(i.pali_clean)
        if i.family_root != "":
            root_families.add(i.family_root)

    for i in searches["paliword"]:
        test1 = i.meaning_1 != ""
        test2 = i.derived_from != ""
        test3 = i.derived_from not in clean_headwords
        test4 = i.derived_from not in root_families
        test5 = not re.findall("irreg form of", i.grammar)
        test6 = not re.findall(fr"\bcomp\b", i.grammar)
        test7 = not re.findall("√", i.derived_from)

        if test1 & test2 & test3 & test4 & test5 & test6 & test7:
            results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "derived_from_not_in_headwords"
    solution = "add derived from to dictionary, or edit derived_from"

    return name, results, length, solution


def pali_words_in_english_meaning(searches: dict) -> tuple:
    """Test if there are Pāḷi words in the meaning"""
    results = []
    pali_words = set()
    english_words = set()
    exceptions: set = {
        "a", "abhidhamma", "ajātasattu", "ala", "an", "ana", "anuruddha",
        "anāthapiṇḍika", "apadāna", "arahant", "are", "assapura", "avanti",
        "aya", "aṅga", "aṅguttara", "aṭṭhakathā", "aṭṭhakavagga", "bhagga",
        "bhoja", "bhāradvāja", "bhātaragāma", "bhū", "bimbisāra", "bodhi",
        "bodhisatta", "brahma"}

    for i in searches["paliword"]:
        pali_words.add(i.pali_clean)
        meaning = i.meaning_1.lower()
        meaning = re.sub("[^A-Za-zāīūṭḍḷñṅṇṃ1234567890\-'’ ]", "", meaning)
        english_words.update(meaning.split())

    english_words = english_words - exceptions
    results = sorted(pali_words & english_words)

    length = len(results)
    results = regex_results(results)
    name = "pali_words_in_english_meaning"
    solution = "add pali_1 to exceptions"

    return name, results, length, solution


def derived_from_not_in_family_compound(searches: dict) -> tuple:
    """Test if derived from is in family compound"""
    results = []
    exceptions = [
        "ana 1", "ana 2", "assā 2", "ato", "atta 2", "abhiṅkharitvā",
        "dhammani", "daddabhāyati", "pakudhaka", "vakkali", "vammika",
        "vammīka", "koliyā", "bhaggava", "bhāradvāja 1", "cicciṭa",
        "cicciṭāyati", "kambojā", "sahali", "vāsiṭṭha", "yāmuna", "bhesajja",
        "ciṅgulaka", "soṇḍi", "sudinna 2",
    ]

    for i in searches["paliword"]:

        test1 = i.pali_1 not in exceptions
        test2 = i.root_key == ""
        test3 = i.pos != "pron"
        test4 = i.meaning_1 != ""
        test5 = i.derived_from != ""
        test6 = not re.findall(r"\bcomp\b", i.grammar)
        test7 = i.family_compound == ""
        test8 = i.family_word == ""

        if test1 & test2 & test3 & test4 & test5 & test6 & test7 & test8:
            results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "derived_from_not_in_family_compound"
    solution = "add pali_1 to exceptions, or add derived_from to family compound"

    return name, results, length, solution


def pos_does_not_equal_grammar(searches):
    """Test of pos equals pos in grammar."""

    results = []
    exceptions: list = ["dve 2"]

    for i in searches["paliword"]:
        if i.pali_1 not in exceptions:
            grammar_pos = re.sub("( |,).+$", "", i.grammar)
            if i.pos != grammar_pos:
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "pos_does_not_equal_grammar"
    solution = "edit pos or grammar"

    return name, results, length, solution


def pos_does_not_equal_pattern(searches: dict) -> tuple:
    """Test pos does not equal pos in pattern."""

    results = []
    pos_exceptions: list = [
        'abbrev', 'abs', 'cs', 'fut', 'ger', 'idiom', 'imp', 'ind', 'inf',
        'letter', 'root', 'opt', 'prefix', 'sandhi', 'suffix', 've', 'var']
    headword_exceptions = ["paṭṭhitago", "dve 2"]

    for i in searches["paliword"]:
        if (i.pos not in pos_exceptions and
                i.pali_1 not in headword_exceptions):

            # how many spaces in the pattern?
            if len(re.findall(" ", i.pattern)) == 1:
                pattern_pos = re.sub(".* ", "", i.pattern)
            elif len(re.findall(" ", i.pattern)) == 2:
                pattern_pos = re.sub(".* (.+) .*", "\\1", i.pattern)
            else:
                pattern_pos = i.pattern

            if i.pos != pattern_pos:
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "pos_does_not_equal_pattern"
    solution = "edit pos or pattern"

    return name, results, length, solution


def vuddhi(root):
    root_vuddhi = []

    if root[-1] in consonants:
        root = root[:-1]
    if root[-1] in consonants:
        root = root[:-1]

    if "a" in root:
        root_vuddhi += [re.sub("a", "ā", root)]
    if "i" in root:
        root_vuddhi += [re.sub("i", "ī", root)]
        root_vuddhi += [re.sub("i", "e", root)]
    if "u" in root:
        root_vuddhi += [re.sub("u", "ū", root)]
        root_vuddhi += [re.sub("u", "av", root)]
        root_vuddhi += [re.sub("u", "āv", root)]
        root_vuddhi += [re.sub("u", "o", root)]
    if root == "plu":
        root_vuddhi += ["pilāv", "pilāp"]
    if root == "kili":
        root_vuddhi += ["kiles"]
    

    root_regex = f"({'|'.join(root_vuddhi)})"
    return root_regex


def base_contains_extra_star(searches: dict) -> tuple:
    """Test if base contains a star but no vuddhi"""

    results = []

    for i in searches["paliword"]:
        if (i.root_base != "" and
            "*" in i.root_base and
                i.pos != "perf"):
            root_no_sign = re.sub("√", "", i.root_clean)

            if not re.findall(f" > {vuddhi(root_no_sign)}", i.root_base):
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "base_contains_extra_star"
    solution = "delete extra star from base"

    return name, results, length, solution


def base_is_missing_star(searches: dict) -> tuple:
    """Test if base is missing a star and contains vuddi"""

    results = []

    for i in searches["paliword"]:

        test1 = i.root_base != ""
        test2 = "*" not in i.root_base
        test3 = "*" in i.root_sign
        test4 = bool(re.findall("a|u|i", i.root_clean))
        test5 = not re.findall("> .+ >", i.root_base)
        test6 = not re.findall("√hi|√ḍi", i.root_key)

        if test1 & test2 & test3 & test4 & test5 & test6:
            root_no_sign = re.sub("√", "", i.root_clean)
            if re.findall(f" > {vuddhi(root_no_sign)}", i.root_base):
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "base_is_missing_star"
    solution = "add vuddhi star to base"

    return name, results, length, solution


def root_x_root_family_mismatch(searches: dict) -> tuple:
    """Test if root matches root family without prefixes."""

    results = []

    for i in searches["paliword"]:
        root_clean = i.root_clean.replace("√", "")
        root_family_clean = re.sub(".*√", "", i.family_root)

        if root_clean != root_family_clean:
            results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "root_x_root_family_mismatch"
    solution = "edit root or family_root"

    return name, results, length, solution


def root_x_construction_mismatch(searches: dict) -> tuple:
    """Test if root matches root in construction."""

    results = []

    for i in searches["paliword"]:
        root_clean = i.root_clean.replace("√", "")
        if "√" in i.construction and i.root_key != "":
            constr_clean = re.sub("\n.+", "", i.construction)
            constr_clean = re.sub("(.*√)(.[^ ]*)(.*)", "\\2", constr_clean)
            if root_clean != constr_clean:
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "root_x_construction_mismatch"
    solution = "edit root_key or root in construction"

    return name, results, length, solution


def family_root_x_construction_mismatch(searches: dict) -> tuple:
    """Test if family_root matches root in construction."""

    results = []

    for i in searches["paliword"]:
        family_root_clean = re.sub(".*√", "", i.family_root)
        if "√" in i.construction and i.root_key != "":
            constr_clean = re.sub("\n.+", "", i.construction)
            constr_clean = re.sub("(.*√)(.[^ ]*)(.*)", "\\2", constr_clean)
            if family_root_clean != constr_clean:
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "family_root_x_construction_mismatch"
    solution = "edit family_root or root in construction"

    return name, results, length, solution


def root_key_x_base_mismatch(searches: dict) -> tuple:
    """Test if root_key matches root in base."""

    results = []

    for i in searches["paliword"]:
        if i.root_key != "" and i.root_base != "":
            base_clean = re.sub("(√.[^ ]*)(.*)", "\\1", i.root_base)
            if i.root_clean != base_clean:
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "root_key_x_base_mismatch"
    solution = "edit root_key or root in base"

    return name, results, length, solution


def root_sign_x_base_mismatch(searches: dict) -> tuple:
    """Test if root_sign matches root in base."""

    results = []

    for i in searches["paliword"]:
        if i.root_key != "" and i.root_base != "":
            root_sign_clean = re.sub(r"\*|\+", "", i.root_sign)
            base_clean = re.sub(r"\*|\+", "", i.root_base)

            if f" {root_sign_clean} " not in base_clean:
                if not re.findall("intens|desid|perf|fut", i.root_base):
                    results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "root_sign_x_base_mismatch"
    solution = "edit root_sign or root in base"

    return name, results, length, solution


def root_base_x_construction_mismatch(searches: dict) -> tuple:
    """Test if root_base matches base in construction."""

    results = []

    for i in searches["paliword"]:
        test1 = i.root_base != ""
        test2 = i.construction != ""
        test3 = i.meaning_1 != ""

        if test1 & test2 & test3:
            base_clean = re.sub("^.+> ", "", i.root_base)
            base_clean = re.sub(r" \(.+$", "", base_clean)

            if re.findall(f"(^| ){base_clean} ", i.construction) == []:
                results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "root_base_x_construction_mismatch"
    solution = "edit root_base or base in construction"

    return name, results, length, solution


def wrong_prefix_in_family_root(searches: dict) -> tuple:
    """Test prefixes in family_root."""

    results = []
    allowable_prefixes = [
        'abhi', 'adhi', 'anu', 'apa', 'api', 'ati', 'ava', 'ni', 'nī', 'pa',
        'pari', 'parā', 'pati', 'prati', 'sad', 'saṃ', 'ud', 'upa', 'vi', 'ā',
        "√"]

    for i in searches["paliword"]:
        if i.family_root:
            fr_splits = i.family_root.split()
            for fr_split in fr_splits:
                test1 = "√" not in fr_split
                test2 = fr_split not in allowable_prefixes
                if test1 & test2:
                    results += [i.pali_1]

    length = len(results)
    results = regex_results(results)
    name = "wrong_prefix_in_family_root"
    solution = "edit prefix in family_root"

    return name, results, length, solution

# next 
# find_fem_abstr_comps

# not included from old tests
# test_words_construction_are_headwords
# test_headword_in_inflections
# run_test_formulas
# derivatives_in_compounds
# complete_root_matrix
# random_words
# identical_meanings
# add_family2
# test_family2
# family2_is_empty
# family2_no_meaning
# words_in_family2_not_in_dpd

# db improvements in old tests
# add_commentary_definitions
# find_variants_and_synonyms
# find_word_families
# find_word_families2
# find_word_families3
# find_word_family_loners



def main():
    tic()
    run_external_tests()
    toc()


if __name__ == "__main__":
    main()