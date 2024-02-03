import json
import os
import re

import tolgee_requests

root_dir = os.path.join(os.path.dirname(__file__), "..")
os.chdir(os.path.join(root_dir, "wingetui"))


__blacklist_strings = [
    "{0} {0} {0} Contributors, please add your names/usernames separated by comas (for credit purposes)",
]


# Function to remove special characters from a string
def remove_special_chars(string):
    # Regular expression for special characters (excluding letters and digits)
    special_chars = r'[^a-zA-Z0-9]'
    # Use regular expression to remove special characters from the string
    return re.sub(special_chars, '', string)


def get_all_strings():
    regex = r'(?<=_\(["\']).+?(?=["\']\))'
    translation_strings: list[str] = []

    for (dirpath, _dirnames, filenames) in os.walk(".", topdown=True):
        for file in filenames:
            _file_name, file_ext = os.path.splitext(file)
            if (file_ext != ".py"):
                continue
            with open(os.path.join(dirpath, file), "r", encoding="utf-8") as f:
                matches: list[str] = re.findall(regex, f.read())
                for match in matches:
                    translation_strings.append(match.encode('raw_unicode_escape').decode('unicode_escape'))

    translation_strings = list(set(translation_strings)) # uniq
    translation_strings.sort(key=lambda x: (remove_special_chars(x.lower()), x))
    return translation_strings


def get_all_translations(lang = "en"):
    with open(f"Core/Languages/lang_{lang}.json", "r", encoding="utf-8") as f:
        lang_strings: dict[str, str] = json.load(f)
    return lang_strings


def get_all_translations_online(lang = "en") -> dict[str, str]:
    response = tolgee_requests.export(zip=False, langs=["en"])
    return json.loads(response.text)


def compare_strings(online = False):
    not_used: list[str] = []
    translation_obj: dict[str, str] = {}
    lang_strings: dict[str, str] = {}
    if (online):
        lang_strings = get_all_translations_online()
    else:
        lang_strings = get_all_translations()
    for key in get_all_strings():
        translation_obj[key] = ""
    for key in lang_strings.keys():
        if (key in __blacklist_strings):
            continue
        if (key in translation_obj):
            del translation_obj[key]
        else:
            not_used.append(key)
    return {
        "not_used": not_used,
        "not_translated": list(translation_obj),
    }
