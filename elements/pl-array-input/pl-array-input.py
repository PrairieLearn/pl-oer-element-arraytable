import random
import math
import re
from typing import Any
from io import StringIO
import csv
import chevron
import lxml.html
import prairielearn as pl

WEIGHT_DEFAULT = 1
INDEX_DEFAULT = "0"
CORRECT_ANSWER_DEFAULT = None
IS_MATERIAL_DEFAULT = False
PLACEHOLDER_DEFAULT = None
PREFILL_DEFAULT = None
COLUMN_NAMES_DEFAULT = "[Index, Data]"
PARTIAL_CREDIT_DEFAULT = True
SHOW_PARTIAL_SCORE_DEFAULT = True
DATA_BASE_DEFAULT = "dec"
INDEX_BASE_DEFAULT = "dec"
DATA_FIXED_WIDTH_DEFAULT = 0
INDEX_FIXED_WIDTH_DEFAULT = 0
SIGNED_DEFAULT = True
STRICT_GRADING_DEFAULT = False
ALLOW_BLANK_DEFAULT = False
UNKNOWN_VALUE_DEFAULT = ""
SIZE_DEFAULT = 0
HIDE_HELP_TEXT = False
ARRAY_INPUT_MUSTACHE_TEMPLATE_NAME = "pl-array-input.mustache"


def string_to_list(raw_string: str | None) -> list[str]:
    """Convert a comma-separated list of column names into an array"""
    if not raw_string:
        return raw_string

    raw_string = "".join(raw_string.splitlines()).strip()
    if raw_string.startswith("[") and raw_string.endswith("]"):
        raw_string = raw_string[1:-1].strip()

    reader = csv.reader(
        StringIO(raw_string),
        delimiter=",",
        escapechar="\\",
        quoting=csv.QUOTE_NONE,
        skipinitialspace=True,
        strict=True,
    )
    return [item.strip() for item in next(reader)]

def prepare(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)
    required_attribs = ["answers-name"]
    optional_attribs = [
        "weight",
        "index",
        "correct-answer",
        "prefill",
        "placeholder",
        "is-material",
        "column-names",
        "show-partial-score",
        "partial-credit",
        "data-base",
        "index-base",
        "index-prefix",
        "data-prefix",
        "data-fixed-width",
        "index-fixed-width",
        "signed",
        "strict-grading",
        "allow-blank",
        "unknown-value",
        "size",
        "hide-help-text"
    ]
    pl.check_attribs(element, required_attribs, optional_attribs)

    name = pl.get_string_attrib(element, "answers-name")
    pl.check_answers_names(data, name) 

    index_values = pl.get_string_attrib(element, "index", INDEX_DEFAULT) # [0x0, 0x1, 0x2, 0x3, ...]
    index_values = string_to_list(index_values)
    
    # convert each answer to string
    if name in data["correct_answers"]:
        # data["correct_answers"][name] = [str(ans) for ans in data["correct_answers"][name]]
        data["correct_answers"][name] = [
            re.sub(r'(?<!\\),', r'\,', str(ans))
            for ans in data["correct_answers"][name]
        ]
    correct_answer_string = pl.get_string_attrib(element, "correct-answer", CORRECT_ANSWER_DEFAULT) # [159, 11, 4, 148, ...]
    correct_answer_list = string_to_list(correct_answer_string) or data["correct_answers"].get(name, None)
    # if correct-answer was set in html, use that value
    # if not, convert list set in server.py to string
    data["correct_answers"][name] = correct_answer_string or pl.to_json("[" + ", ".join(correct_answer_list) + "]")


    if correct_answer_list is None:
        raise ValueError(f"Missing correct answer for {name}. Ensure that correct answers are set in 'server.py' or 'question.html'.")

    prefill = pl.get_string_attrib(element, "prefill", PREFILL_DEFAULT)
    prefill = string_to_list(prefill)

    placeholder = pl.get_string_attrib(element, "placeholder", PLACEHOLDER_DEFAULT)
    placeholder = string_to_list(placeholder)

    column_names = pl.get_string_attrib(element, "column-names", COLUMN_NAMES_DEFAULT)
    column_names = string_to_list(column_names)

    data_base = pl.get_string_attrib(element, "data-base", DATA_BASE_DEFAULT)
    data_base = data_base.lower()

    data_fixed_width = pl.get_integer_attrib(element, "data-fixed-width", DATA_FIXED_WIDTH_DEFAULT)

    unknown_value = pl.get_string_attrib(element, "unknown-value", UNKNOWN_VALUE_DEFAULT)
    unknown_value = unknown_value.lower()

    allow_blank = pl.get_boolean_attrib(element, "allow-blank", ALLOW_BLANK_DEFAULT)

    num_rows = len(correct_answer_list)

    # check attribute values are either a single string or a list with same length as correct answers
    if len(index_values) != num_rows and len(index_values) != 1:
        raise ValueError(
            f"Length of index ({len(index_values)}) must either match the length of correct-answer ({num_rows}) or be a single start address."
        )
    
    if prefill and len(prefill) != num_rows and len(prefill) != 1:
        raise ValueError(
            f"Length of prefill ({len(prefill)}) must be either 1 or match the length of correct-answer ({num_rows})."
        )
    
    if placeholder is not None and len(placeholder) != num_rows and len(placeholder) != 1:
        raise ValueError(
            f"Length of placeholder ({len(placeholder)}) must be either 1 or match the length of correct-answer ({num_rows})."
        )
    
    # check only 2 column names are given
    if len(column_names) != 2:
        raise ValueError(
            "Length of column-names must be 2."
        )
    
    if data_base not in ["dec", "hex", "bin", "string"]:
        raise ValueError(
            f"data-base attribute must have the value of \"string\", \"dec\", \"hex\", or \"bin\""
        )
    
    check_correct_answer_type(element, correct_answer_list, data_base, unknown_value, allow_blank, name)

    prefix_options = {"dec": "", "bin": "0b", "hex": "0x", "string": ""}
    data_prefix_default = prefix_options[data_base]
    prefix = pl.get_string_attrib(element, "data-prefix", data_prefix_default)
    if data_base == "string" and prefix:
        raise ValueError("data-prefix should not be specified when data-base is 'string'.")
    
    if data_fixed_width < 0:
        raise ValueError("Negative value input for data-fixed-width.")
            
    # check that the input correct-answers meet any width requirement for hex and bin
    valid_unknowns = [unknown_value]
    if allow_blank:
        valid_unknowns.append("")
    if ((data_base == "hex" or data_base == "bin") and data_fixed_width > 0):
        for ans in correct_answer_list:
            if ans.lower() not in valid_unknowns:
                ans = ans.replace(prefix, "", 1)
                if len(ans) != data_fixed_width:
                    raise ValueError(
                        f"Width of one or more correct-answer values after its prefix does not match fixed width of {data_fixed_width} in \"{name}\". This does not include unknown-answer values."
                    ) 

def check_correct_answer_type(element, correct_answer_list, base, unknown_value, allow_blank, name):
    valid_unknowns = [unknown_value]
    if allow_blank:
        valid_unknowns.append("")
    
    prefix_options = {"dec": "", "bin": "0b", "hex": "0x", "string": ""}
    data_prefix_default = prefix_options[base]
    prefix = pl.get_string_attrib(element, "data-prefix", data_prefix_default)

    if base == "dec":
        for i in correct_answer_list:
            i = i.lower()
            i = i.replace(prefix, "", 1)

            if i in valid_unknowns:
                continue
            try:
                cast = int(i)
            except Exception as e: 
                raise ValueError(
                        f"data-base is set to \"dec\" in question {name}, however one or more of the correct-answer values is an invalid decimal number. If you'd like to choose a different base, set data-base to \"hex\", \"bin\", or \"string\"."
                    ) from None
        return
    if base == "hex":
        for i in correct_answer_list:
            i = i.lower()
            i = i.replace(prefix, "", 1)
            if i in valid_unknowns:
                continue
            try:
                cast = int(i, 16)
            except Exception as e: 
                raise ValueError(
                        f"data-base is set to \"hex\" in question {name}, however one or more of the correct-answer values is an invalid hexadecimal number."
                    ) from None
        return
    if base == "bin":
        for i in correct_answer_list:
            i = i.lower()
            i = i.replace(prefix, "", 1)
            if i in valid_unknowns:
                continue
            try:
                cast = int(i, 2)
            except Exception as e: 
                raise ValueError(
                        f"data-base is set to \"bin\" in question {name}, however one or more of the correct-answer values is an invalid binary number."
                    ) from None
        return



def render(element_html: str, data: pl.QuestionData) -> str:
    element = lxml.html.fragment_fromstring(element_html)
    name = pl.get_string_attrib(element, "answers-name")

    correct_answer_string = data["correct_answers"][name] # [159, 11, 4, 148, ...]
    correct_answer_list = string_to_list(correct_answer_string) or data["correct_answers"].get(name, None)
    
    if correct_answer_list is None:
        raise ValueError(f"Missing correct answer for {name}. Ensure that correct answers are set in 'server.py' or 'question.html'.")

    correct_answer_list = [val.strip() for val in correct_answer_list]
    num_rows = len(correct_answer_list)

    index_values = pl.get_string_attrib(element, "index", INDEX_DEFAULT) # [0x0, 0x1, 0x2, 0x3, ...]
    index_values = string_to_list(index_values)

    hide_help_text = pl.get_boolean_attrib(element, "hide-help-text", HIDE_HELP_TEXT)
    prefix_options = {"dec": "", "bin": "0b", "hex": "0x"}
    base_options = {"dec": 10, "bin": 2, "hex": 16}
    index_base = pl.get_string_attrib(element, "index-base", INDEX_BASE_DEFAULT).lower()
    if index_base not in prefix_options:
        raise ValueError(f"Invalid base '{index_base}' for index-base. Must be one of {list(prefix_options.keys())}.")
    prefix_default = prefix_options[index_base]
    index_prefix = pl.get_string_attrib(element, "index-prefix", prefix_default)
    index_fixed_width = pl.get_integer_attrib(element, "index-fixed-width", INDEX_FIXED_WIDTH_DEFAULT)

    if len(index_values) != num_rows:
        initial_value = index_values[0]
        try:
            initial_int = int(initial_value, base_options[index_base])
        except ValueError:
            # if initial value doesnt make sense for base (eg. index="5", index-base="bin")
            raise ValueError(
                f"Invalid index '{initial_value}' for base '{index_base}'. Ensure the value matches the chosen base."
            )
        if index_base == "hex":
            # hexadecimal format (e.g., "0x0")
            index_values = [f"{index_prefix}{(initial_int + i):X}" for i in range(num_rows)]
            if index_fixed_width != 0:
                max_index = f"{initial_int + (num_rows - 1):X}"
                # check width is not smaller than largest index value
                if index_fixed_width < len(max_index):
                    raise ValueError(
                        f"Width of one or more index values is greater than fixed width of {index_fixed_width} in \"{name}\". For instance, {max_index}."
                    )
                else:
                    index_values = [f"{index_prefix}{(initial_int + i):0{index_fixed_width}X}" for i in range(num_rows)]
    
        elif index_base == "bin":
            # binary format
            index_values = [f"{index_prefix}{(initial_int + i):b}" for i in range(num_rows)]
            if index_fixed_width != 0:
                max_index = f"{initial_int + (num_rows - 1):b}"
                # check width is not smaller than largest index value
                if index_fixed_width < len(max_index):
                    raise ValueError(
                        f"Width of one or more index values is greater than fixed width of {index_fixed_width} in \"{name}\". For instance, {max_index}."
                    )
                else:
                    index_values = [f"{index_prefix}{(initial_int + i):0{index_fixed_width}b}" for i in range(num_rows)]
        else:
            # decimal format
            index_values = [f"{index_prefix}{initial_int + i}" for i in range(num_rows)]
    
    # check if index-base/index-prefix/index-fixed-width are given with list of indices
    elif any(
        pl.get_string_attrib(element, attr, None) is not None 
        for attr in ["index-base", "index-prefix", "index-fixed-width"]
    ):
        raise ValueError("Index base/prefix/fixed width should not be specified when a complete list of indices is provided.")


    prefill = pl.get_string_attrib(element, "prefill", PREFILL_DEFAULT)
    if prefill:
        prefill = string_to_list(prefill)
        if len(prefill) == 1:
            prefill = prefill * num_rows

    placeholder = pl.get_string_attrib(element, "placeholder", PLACEHOLDER_DEFAULT)
    if placeholder is not None:
        placeholder = string_to_list(placeholder)
        if len(placeholder) == 1:
            placeholder = placeholder * num_rows
    
    prefix_options = {"dec": "", "bin": "0b", "hex": "0x", "string": ""}
    data_base = pl.get_string_attrib(element, "data-base", DATA_BASE_DEFAULT).lower()
    if data_base not in prefix_options:
        raise ValueError(f"Invalid base '{data_base}'. Must be one of {list(prefix_options.keys())}.")
    data_prefix_default = prefix_options[data_base]
    prefix = pl.get_string_attrib(element, "data-prefix", data_prefix_default)
    
    unknown_value = pl.get_string_attrib(element, "unknown-value", UNKNOWN_VALUE_DEFAULT)
    unknown_value = unknown_value.lower()
    allow_blank = pl.get_boolean_attrib(element, "allow-blank", ALLOW_BLANK_DEFAULT)
    
    width = 0
    for i in range(num_rows):
        width = max(width, len(correct_answer_list[i]) * 1.2)
        if placeholder:
            if placeholder[i] and not placeholder[i].startswith(prefix) and placeholder[i].lower() != unknown_value:
                placeholder[i] = prefix + placeholder[i]
            width = max(width, len(placeholder[i]) * 1.2)
        if prefill:
            if prefill[i] and not prefill[i].startswith(prefix) and prefill[i].lower() != unknown_value:
                prefill[i] = prefix + prefill[i]
            width = max(width, len(prefill[i]) * 1.2)

    size = pl.get_integer_attrib(element, "size", SIZE_DEFAULT)
    if size < 0:
        raise ValueError(
            f"The size attribute must be 0 or greater."
        )
    width = size or math.ceil(width) 

    column_names = pl.get_string_attrib(element, "column-names", COLUMN_NAMES_DEFAULT)
    column_names = string_to_list(column_names)

    is_material = pl.get_boolean_attrib(element, "is-material", IS_MATERIAL_DEFAULT)

    score = data["partial_scores"].get(name, {"score": None}).get("score", None)
    if score is not None:
        score = round(float(score) * 100)
    ac = score == 100
    aw = score == 0

    correct_answer_dict = {f"{name}_{i}": answer for i, answer in enumerate(correct_answer_list)}

    rows = []
    for i in range(num_rows):
        row = {
            "index_col": index_values[i],
            "row_index": i,
            "name" : name,
            "is_first_row": i == 0,
            "content": {
                "cell_name": f"{name}_{i}",
                "sub": data["raw_submitted_answers"].get(f"{name}_{i}", prefill[i] if prefill else ""),
                "prefill": prefill[i] if prefill else "",
                "correct": False,
                "incorrect": False,
                "format_error": data["format_errors"].get(f"{name}_{i}", None),
                "correct_answer": correct_answer_dict.get(f"{name}_{i}", None),
                "placeholder": placeholder[i] if placeholder else None,
                "width": 16 + 8 * width
            }
        }
        partial_score = (
            data["partial_scores"]
            .get(f"{name}_{i}", {"score": None})
            .get("score", None)
        )
        if partial_score is not None:
            try:
                partial_score = float(partial_score)
                if partial_score >= 1:
                    row["content"]["correct"] = True
                else:
                    row["content"]["incorrect"] = True
            except Exception as e:
                raise ValueError("invalid score" + str(partial_score)) from e
        rows.append(row)
    
    with open(ARRAY_INPUT_MUSTACHE_TEMPLATE_NAME, "r", encoding="utf-8") as f:
        template = f.read()

    # add format instructions based on expected answer format
    signed = pl.get_boolean_attrib(element, "signed", SIGNED_DEFAULT)
    data_fixed_width = pl.get_integer_attrib(element, "data-fixed-width", DATA_FIXED_WIDTH_DEFAULT)


    allow_blank_instruction = "(You may leave this completely blank. If you choose not to, follow the next formatting instructions for your inputs.)" if allow_blank else ""
    signed_instruction = "" if data_base != "hex" and data_base != "bin" else "a signed" if signed else "an unsigned"
    base_instruction = "a decimal" if data_base == "dec" else "binary" if data_base == "bin" else "hexadecimal" if data_base == "hex" else "a string"
    fixed_width_instruction = "" if data_fixed_width <= 0 else "with " +  str(data_fixed_width) + " digits (excluding any prefix)" 
    unknown_value_instruction = "blank" if unknown_value == "" else "\"" + unknown_value + "\""

    # combine the instructions
    format_instructions = ""
    format_instructions += allow_blank_instruction + " Your answer must be " +  signed_instruction + " "+ base_instruction + " value " + fixed_width_instruction + " or " +unknown_value_instruction + ". "

    
    partial_credit = pl.get_boolean_attrib(element, "partial-credit", PARTIAL_CREDIT_DEFAULT)
    show_partial_score = pl.get_boolean_attrib(element, "show-partial-score", SHOW_PARTIAL_SCORE_DEFAULT)
    if data["panel"] == "question":
        grading_text = ""
        if show_partial_score:
            if partial_credit:
                grading_text = format_instructions + "You will receive credit per correct cell, and feedback on which cells are filled out correctly."
            else:
                grading_text = format_instructions + "You will receive feedback on which cells are correct, but no partial credit unless the entire table is filled correctly."
        else:
            if partial_credit:
                grading_text = format_instructions + "You will receive credit per correct cell, but no detailed feedback on which cells are correct."  
            else:
                grading_text = format_instructions + "You will not receive partial credit unless the entire table is filled correctly."

        info_params = {
            "format": True,
            "grading_text": grading_text
        }
        info = chevron.render(template, info_params).strip()
        html_params = {
            "question": True,
            "name": name,
            "column_names": column_names,
            "info": info,
            "uuid": pl.get_uuid(),
            "rows": rows,
            "is_material": is_material,
            "show_partial_score": show_partial_score,
            "score": score,
            "all_correct": ac,
            "all_incorrect": aw,
            "hide_help_text": hide_help_text
        }
        return chevron.render(template, html_params).strip()
    
    elif data["panel"] == "submission":
        html_params = {
            "submission": True,
            "name": name,
            "column_names": column_names,
            "uuid": pl.get_uuid(),
            "rows": rows,
            "is_material": is_material,
            "show_partial_score": show_partial_score,
            "score": score,
            "all_correct": ac,
            "all_incorrect": aw,
        }
        for i in range(num_rows):
            answer_name = f"{name}_{i}"
            parse_error = data["format_errors"].get(answer_name, None)
            if parse_error is None and answer_name in data["submitted_answers"]:
                a_sub = data["submitted_answers"].get(answer_name, None)
                a_sub = pl.from_json(a_sub)
                a_sub = pl.escape_unicode_string(a_sub)
                html_params["a_sub"] = a_sub
            elif answer_name not in data["submitted_answers"]:
                data["format_errors"][answer_name] = "No submitted answer."
                html_params["parse_error"] = None
        
        if show_partial_score and score is not None:
            score_type, score_value = pl.determine_score_params(score)
            html_params[score_type] = score_value
        return chevron.render(template, html_params).strip()
    
    elif data["panel"] == "answer":
        html_params = {
            "answer": True,
            "name": name,
            "column_names": column_names,
            "rows": rows,
        }
        return chevron.render(template, html_params).strip()

def parse(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)

    # check if the question is marked as material (informational)
    is_material = pl.get_boolean_attrib(element, "is-material", False)
    # if it's material, skip grading
    if is_material:
        return
    
    name = pl.get_string_attrib(element, "answers-name")

    # get number of rows
    correct_answer = data["correct_answers"][name]
    correct_answer = string_to_list(correct_answer)
    if correct_answer is None:
        raise ValueError(f"Missing correct answer for {name}. Ensure that correct answers are set in 'server.py' or 'question.html'.")

    num_rows = len(correct_answer)    
    submitted_answers_list = string_to_list(data['submitted_answers'].get(name, None))

    allow_blank = pl.get_boolean_attrib(element, "allow-blank", ALLOW_BLANK_DEFAULT)
     # check if all are blank, and if so, return.
    if allow_blank:
        blank_count = 0
        for row_index in range(num_rows):
            answer_name = f"{name}_{row_index}"
            a_sub = submitted_answers_list[row_index] if submitted_answers_list != None else data["submitted_answers"].get(answer_name, None)
            if not a_sub or a_sub is None:
                blank_count += 1
                data["submitted_answers"][answer_name] = a_sub
        if blank_count == num_rows:
            return


    for row_index in range(num_rows):
        answer_name = f"{name}_{row_index}"
        a_sub = submitted_answers_list[row_index] if submitted_answers_list != None else data["submitted_answers"].get(answer_name, None)
        validate_input(a_sub, answer_name, element, data)

    return

def validate_input(a_sub, answer_name, element, data: pl.QuestionData):
        
        # check if a_sub does not exist
        if a_sub is None:
            data["format_errors"][answer_name] = "No submitted answer."
            data["submitted_answers"][answer_name] = None
            return   
    
        unknown_value = pl.get_string_attrib(element, "unknown-value", UNKNOWN_VALUE_DEFAULT)
        unknown_value = unknown_value.lower()

        if not a_sub and unknown_value != "":
            data["format_errors"][
                answer_name
            ] = "Invalid format. The submitted answer was left blank."
            data["submitted_answers"][answer_name] = None  
            return

        # clean a_sub
        a_sub_clean = a_sub.lstrip().rstrip()
        a_sub_clean = a_sub_clean.lower() 

        base = pl.get_string_attrib(element, "data-base", DATA_BASE_DEFAULT)
        base = base.lower()

        prefix_options = {"dec": "", "bin": "0b", "hex": "0x", "string": ""}
        if base not in prefix_options:
            raise ValueError(f"Invalid base '{base}'. Must be one of {list(prefix_options.keys())}.")
        data_prefix_default = prefix_options[base]
        prefix = pl.get_string_attrib(element, "data-prefix", data_prefix_default)

        a_sub_clean = a_sub_clean.replace(prefix, "", 1)

        # string base should allow all
        if base == "string":
            data["submitted_answers"][answer_name] = pl.to_json(a_sub)
            return
        
        # check if a_sub is equal to unknown-value or blank.
        if (a_sub_clean == unknown_value):
            data["submitted_answers"][answer_name] = pl.to_json(a_sub)
            return

        # alternative blank value instead of ""
        uv = "\'" + unknown_value + "\'" if (unknown_value != "") else "blank"

        if base == "dec":
            try:
                cast = int(a_sub_clean)
            except Exception as e:
                data["format_errors"][
                    answer_name
                ] = f"Invalid format. The submitted answer must be a valid decimal or {uv}."
                data["submitted_answers"][answer_name] = pl.to_json(a_sub)
                return
        elif base == "hex":
            a_sub_clean = a_sub_clean.replace(" ", "")
            try:
                cast = int(a_sub_clean, 16)
            except Exception as e:
                data["format_errors"][
                    answer_name
                ] = f"Invalid format. The submitted answer must be a valid hexadecimal number or {uv}."
                data["submitted_answers"][answer_name] = pl.to_json(a_sub)
                return
        else:
            a_sub_clean = a_sub_clean.replace(" ", "")
            try:
                cast = int(a_sub_clean, 2)
            except Exception as e:
                data["format_errors"][
                    answer_name
                ] = f"Invalid format. The submitted answer must be a valid binary number or {uv}."
                data["submitted_answers"][answer_name] = pl.to_json(a_sub)
                return
        
        strict = pl.get_boolean_attrib(element, "strict-grading", STRICT_GRADING_DEFAULT)
        data_fixed_width = pl.get_integer_attrib(element, "data-fixed-width", DATA_FIXED_WIDTH_DEFAULT)

        # if data-fixed-width > 0 and strict is false, check width
        if (data_fixed_width > 0) and not strict:
            if (len(a_sub_clean) != data_fixed_width):
                data["format_errors"][
                    answer_name
                ] = "Invalid format. The submitted answer is not the right length."
                data["submitted_answers"][answer_name] = pl.to_json(a_sub)
                return
            
        data["submitted_answers"][answer_name] = pl.to_json(a_sub)

def grade(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)
    # check if the question is marked as material (informational)
    is_material = pl.get_boolean_attrib(element, "is-material", False)
    # if it's material, skip grading
    if is_material:
        return
    
    weight = pl.get_integer_attrib(element, "weight", WEIGHT_DEFAULT)
    name = pl.get_string_attrib(element, "answers-name")
    
    # get number of rows
    correct_answer = data["correct_answers"][name]
    correct_answer = string_to_list(correct_answer)
    if correct_answer is None:
        raise ValueError(f"Missing correct answer for {name}. Ensure that correct answers are set in 'server.py' or 'question.html'.")

    num_rows = len(correct_answer)
    correct_answer_dict = {f"{name}_{i}": answer.strip() for i, answer in enumerate(correct_answer)}

    partial_credit = pl.get_boolean_attrib(
        element, "partial-credit", PARTIAL_CREDIT_DEFAULT
    )

    is_incorrect = False
    score_sum = 0
    for index in range(num_rows):
        answer_name = f"{name}_{index}"
        # get the correct answer for each row
        a_tru = pl.from_json(correct_answer_dict.get(answer_name, None))
        if a_tru is None:
            break
        if answer_name in data["submitted_answers"]:
            a_sub = data["submitted_answers"][answer_name]
            if check_answer(a_sub, a_tru, element):
                data["partial_scores"][answer_name] = {
                    "score": 1,
                    "feedback": "Correct.",
                    "weight": 0
                }
                score_sum += 1
            else:
                data["partial_scores"][answer_name] = {
                    "score": 0,
                    "feedback": "Incorrect.",
                    "weight": 0
                }
                if not partial_credit:
                    is_incorrect = True
        else:
            data["partial_scores"][answer_name] = {
                "score": 0,
                "feedback": "Missing input.",
                "weight": 0
            }
            if not partial_credit:
                is_incorrect = True

    if not partial_credit and is_incorrect:
        score_sum = 0
    data["partial_scores"][name] = {"score": score_sum / (num_rows), "weight": weight}

    return


def check_answer(a_sub, a_tru, element,):


    base = pl.get_string_attrib(element, "data-base", DATA_BASE_DEFAULT).lower()
    strict = pl.get_boolean_attrib(element, "strict-grading", STRICT_GRADING_DEFAULT)
    data_fixed_width = pl.get_integer_attrib(element, "data-fixed-width", DATA_FIXED_WIDTH_DEFAULT)
    unknown_value = pl.get_string_attrib(element, "unknown-value", UNKNOWN_VALUE_DEFAULT).lower()
    allow_blank = pl.get_boolean_attrib(element, "allow-blank", ALLOW_BLANK_DEFAULT)

    #remove spaces on the sides
    a_sub = a_sub.lstrip().rstrip()
    a_tru = a_tru.lstrip().rstrip()

    #string comparison
    if (base == "string"):
        return a_sub.lstrip().rstrip() == a_tru.lstrip().rstrip()
    
    # initial cleaning: make everything lowercase
    a_sub = a_sub.lower()
    a_tru = a_tru.lower()


    # handle unknown and blank cases first
    if (a_tru == unknown_value):
        return (a_sub == a_tru)

    # since a_tru is not unknown value, a_sub = unknown value or blank is incorrect
    if a_sub == unknown_value:
        return False
    
    # direct comparison for allow blank values
    if allow_blank and a_sub == "" and unknown_value != "":
        return a_sub == a_tru

    # check a_tru is empty string before converting base
    if allow_blank and a_tru == "" and a_sub != "":
        return False

    # handle decimal case
    if base == "dec":
        a_sub_int = int(a_sub)
        a_tru_int = int(a_tru)
        return (a_sub_int == a_tru_int)
    
    # handle hex and bin cases

    prefix_options = {"dec": "", "bin": "0b", "hex": "0x", "string": ""}
    data_prefix_default = prefix_options[base]
    prefix = pl.get_string_attrib(element, "data-prefix", data_prefix_default)

    a_sub = a_sub.replace(prefix, "", 1)
    a_tru = a_tru.replace(prefix, "", 1)

    # enforce width if data_fixed_width > 0 and strict is true.
    if (data_fixed_width > 0) and strict:
        if (len(a_sub) != data_fixed_width):
            return False
        return (a_sub == a_tru)
    
    signed = pl.get_boolean_attrib(element, "signed", SIGNED_DEFAULT)

    if not signed:
        a_sub_clean = a_sub_clean.replace(" ", "")
        if base == "hex":
            return (int(a_sub, 16) == int(a_tru,16))
        else:
            return (int(a_sub, 2) == int(a_tru, 2))

    # for signed values
    if base == "hex":
        a_sub_clean = a_sub_clean.replace(" ", "")
        neg_values = ["8", "9", "a", "b", "c", "d", "e", "f"]
        a_sub_int = None
        # calculate integer value of submitted answer 
        if (a_sub[0] in neg_values):
            a_sub_int_unsigned = int(a_sub, 16)
            mask = int(("f" * len(a_sub)), 16)
            a_sub_int = -1 * ((a_sub_int_unsigned ^ mask) + 1) 
        else:
            a_sub_int = int(a_sub, 16)

        # calculate integer value of correct answer 
        a_tru_int = None
        if (a_tru[0] in neg_values):
            a_tru_int_unsigned = int(a_tru, 16)
            mask = int(("f" * len(a_sub)), 16)
            a_tru_int = -1 * ((a_tru_int_unsigned ^ mask) + 1) 
        else:
            a_tru_int = int(a_tru, 16)

        return (a_sub_int == a_tru_int)
    
    if base == "bin":
        a_sub_clean = a_sub_clean.replace(" ", "")
        a_sub_int = None
        # calculate integer value of submitted answer 
        if (a_sub[0] == '1'):
            a_sub_int_unsigned = int(a_sub,2)
            mask = int(("1" * len(a_sub)), 2)
            a_sub_int = -1 * ((a_sub_int_unsigned ^ mask) + 1)
        else:
             a_sub_int = int(a_sub, 2)
            
        # calculate integer value of correct answer 
        a_tru_int = None
        if (a_tru[0] == '1'):
            a_tru_int_unsigned = int(a_sub,2)
            mask = int(("1" * len(a_sub)), 2)
            a_tru_int = -1 * ((a_tru_int_unsigned ^ mask) + 1)
        else:
             a_tru_int = int(a_tru, 2)
        return (a_sub_int == a_tru_int)


def test(element_html: str, data: pl.ElementTestData) -> None:
    element = lxml.html.fragment_fromstring(element_html)
    name = pl.get_string_attrib(element, "answers-name")

    is_material = pl.get_boolean_attrib(element, "is-material", IS_MATERIAL_DEFAULT)
    if (is_material):
        data["raw_submitted_answers"][name] = data["correct_answers"]
        return

    weight = pl.get_integer_attrib(element, "weight", WEIGHT_DEFAULT)
    partial_credit = pl.get_boolean_attrib(
        element, "partial-credit", PARTIAL_CREDIT_DEFAULT
    )
    correct_answer_string = data["correct_answers"].get(name, [])
    correct_answer_list = string_to_list(correct_answer_string) or data["correct_answers"].get(name, None)
    number_answers = len(correct_answer_list)
    all_keys = [i for i in range(number_answers)] 

    # determine valid incorrect values
    unknown_value = pl.get_string_attrib(element, "unknown-value", UNKNOWN_VALUE_DEFAULT) 
    data_fixed_width = pl.get_integer_attrib(element, "data-fixed-width", DATA_FIXED_WIDTH_DEFAULT)

    incorrect_hex = "0x0"
    incorrect_bin = "0b0"
    incorrect_dec = "0"
    incorrect_string = unknown_value + "1"

    # This avoids errors that will be caused by the strict-grading attribute. Can add related test cases.
    if (data_fixed_width > 0):
        extension = "0" * (data_fixed_width - 1)
        incorrect_hex += extension
        incorrect_bin += extension


    result = data["test_type"]

    if result == "correct":
        data["raw_submitted_answers"][name] = data["correct_answers"][name] 
        feedback = {
             name: "null"
        }
        data["partial_scores"][name] = {
            "score": 1,
            "weight" : weight
        }
        for key in all_keys:
            data["partial_scores"][name + "_" + str(key)] = {
                "score": 1,
                "weight": 0, 
                "feedback": "Correct."
            }
    elif result == "incorrect":
        while True:
            # select answer keys at random to be correct
            correct_keys = [k for k in all_keys if random.choice([True, False])]
            # break and use this choice if some are incorrect
            if (
                len(correct_keys) < len(correct_answer_list)
            ):
                break
        if partial_credit:
            points = len(set(correct_keys))
            score = points / len(set(all_keys))
        else:
            score = 0

        data_base = pl.get_string_attrib(element, "data-base", DATA_BASE_DEFAULT).lower()

        # generate random submitted answers(incorrect/correct depending on correct_keys) and corresponding partial scores
        submitted_answers = "["
        correct_answer_list_as_strings = [str(x) for x in correct_answer_list]
        incorrect_val = ""
        match data_base:
            case "bin":
                incorrect_val = incorrect_bin
            case "hex":
                incorrect_val = incorrect_hex
            case "dec":
                incorrect_val = incorrect_dec
            case "string":
                incorrect_val = incorrect_string
        if incorrect_val == "":
            raise ValueError("Incorrect value inputted for data-base. Options are \"dec\", \"bin\", \"hex\", and \"string\"")
        for key in all_keys: 
            feedback = "Correct."
            partial_score = 1
            if key in correct_keys:
                submitted_answers += correct_answer_list_as_strings[key]
            else:
                feedback = "Incorrect."
                partial_score = 0
                if correct_answer_list[key] != unknown_value:
                    submitted_answers += unknown_value
                else:
                    submitted_answers += incorrect_val
            submitted_answers += ","
            data["partial_scores"][name + "_" + str(key)] = {"score": partial_score, "weight": 0, "feedback": feedback}
        submitted_answers = submitted_answers[:-1]
        submitted_answers += "]"

        data["raw_submitted_answers"][name] = submitted_answers

        data["partial_scores"][name] = {
            "score": score,
            "weight": weight,
        }

    elif result == "invalid":
        # FIXME: add more examples of invalid inputs
        data["raw_submitted_answers"][name] = None
        for key in all_keys:
            data["format_errors"][name + "_" + str(key)] = "No submitted answer."
    else:
        raise Exception("invalid result: %s" % result)

        
# def string_to_list(value: str):
#     if value is None:
#         return None
#     value = value.strip()
#     if value.startswith("[") and value.endswith("]"):
#         value = value[1:-1]
#     value = value.split(",")
#     value = [v.strip() for v in value]
#     return value