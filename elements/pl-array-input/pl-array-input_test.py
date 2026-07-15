import importlib
import json
import os
import sys
import types
from pathlib import Path

import pytest

ELEMENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ELEMENT_DIR))

sys.modules["chevron"] = types.SimpleNamespace(
    render=lambda _template, params: json.dumps(params)
)

pl_stub = types.SimpleNamespace(
    QuestionData=dict,
    ElementTestData=dict,
    get_string_attrib=lambda element, name, default=None: element.get(name, default),
    get_boolean_attrib=lambda element, name, default=None: (
        element.get(name, str(default)).lower() in {"true", "1", "yes"}
        if element.get(name) is not None
        else default
    ),
    get_integer_attrib=lambda element, name, default=None: (
        int(element.get(name)) if element.get(name) is not None else default
    ),
    check_attribs=lambda _element, _required, _optional: None,
    check_answers_names=lambda _data, *_names: None,
    from_json=lambda value: (
        json.loads(value)
        if isinstance(value, str) and value[:1] in {'"', "[", "{"}
        else value
    ),
    to_json=lambda value: json.dumps(value),
    escape_unicode_string=lambda value: value,
    get_uuid=lambda: "test-uuid",
    determine_score_params=lambda score: ("score", score),
)
sys.modules["prairielearn"] = pl_stub

pl_array_input = importlib.import_module("pl-array-input")


def _base_data() -> dict:
    return {
        "params": {},
        "correct_answers": {},
        "submitted_answers": {},
        "raw_submitted_answers": {},
        "partial_scores": {},
        "format_errors": {},
        "panel": "question",
    }


def _render(element_html: str, data: dict) -> dict:
    old_cwd = os.getcwd()
    try:
        os.chdir(ELEMENT_DIR)
        return json.loads(pl_array_input.render(element_html, data))
    finally:
        os.chdir(old_cwd)


def test_string_to_list_supports_readme_array_syntax_and_escaped_commas() -> None:
    assert pl_array_input.string_to_list("[0x40, 0x2d, NA]") == [
        "0x40",
        "0x2d",
        "NA",
    ]
    assert pl_array_input.string_to_list(r"[Hello\, World!, He]") == [
        "Hello, World!",
        "He",
    ]
    assert pl_array_input.string_to_list("5") == ["5"]
    assert pl_array_input.string_to_list(None) is None


def test_prepare_accepts_hex_correct_answers_from_html() -> None:
    data = _base_data()

    pl_array_input.prepare(
        '<pl-array-input answers-name="regs" index="[0, 1]" '
        'correct-answer="[0x11, 0x0f]" data-base="hex"></pl-array-input>',
        data,
    )

    assert data["correct_answers"]["regs"] == "[0x11, 0x0f]"


def test_prepare_rejects_wrong_length_prefill() -> None:
    data = _base_data()

    with pytest.raises(ValueError, match="Length of prefill"):
        pl_array_input.prepare(
            '<pl-array-input answers-name="regs" index="[0, 1]" '
            'correct-answer="[1, 2]" prefill="[0, 1, 2]"></pl-array-input>',
            data,
        )


def test_prepare_rejects_invalid_value_for_selected_base() -> None:
    data = _base_data()

    with pytest.raises(ValueError, match="invalid hexadecimal"):
        pl_array_input.prepare(
            '<pl-array-input answers-name="regs" index="[0, 1]" '
            'correct-answer="[0x11, nope]" data-base="hex"></pl-array-input>',
            data,
        )


def test_prepare_uses_server_correct_answers_and_escapes_commas() -> None:
    data = _base_data()
    data["correct_answers"]["names"] = ["alpha,beta", "gamma"]

    pl_array_input.prepare(
        '<pl-array-input answers-name="names" data-base="string"></pl-array-input>',
        data,
    )

    assert json.loads(data["correct_answers"]["names"]) == r"[alpha\,beta, gamma]"


def test_prepare_accepts_unknown_and_blank_answers_when_allowed() -> None:
    data = _base_data()

    pl_array_input.prepare(
        '<pl-array-input answers-name="cells" correct-answer="[NA, ]" '
        'unknown-value="NA" allow-blank="true"></pl-array-input>',
        data,
    )

    assert data["correct_answers"]["cells"] == "[NA, ]"


def test_prepare_rejects_fixed_width_answers_with_wrong_width() -> None:
    data = _base_data()

    with pytest.raises(ValueError, match="fixed width of 4"):
        pl_array_input.prepare(
            '<pl-array-input answers-name="regs" correct-answer="[0x1, 0x00ff]" '
            'data-base="hex" data-fixed-width="4"></pl-array-input>',
            data,
        )


def test_render_generates_hex_indices_prefill_placeholders_and_width() -> None:
    data = _base_data()
    element_html = (
        '<pl-array-input answers-name="regs" index="0" index-base="hex" '
        'index-fixed-width="2" correct-answer="[0x0a, 0x0b, 0x0c]" '
        'data-base="hex" prefill="0" placeholder="[1, 2, NA]" '
        'unknown-value="NA" size="6"></pl-array-input>'
    )

    pl_array_input.prepare(element_html, data)
    rendered = _render(element_html, data)

    assert [row["index_col"] for row in rendered["rows"]] == ["0x00", "0x01", "0x02"]
    assert [row["content"]["prefill"] for row in rendered["rows"]] == [
        "0x0",
        "0x0",
        "0x0",
    ]
    assert [row["content"]["placeholder"] for row in rendered["rows"]] == [
        "0x1",
        "0x2",
        "NA",
    ]
    assert {row["content"]["width"] for row in rendered["rows"]} == {64}


def test_render_rejects_index_format_options_when_full_index_list_is_given() -> None:
    data = _base_data()
    element_html = (
        '<pl-array-input answers-name="regs" index="[0, 1]" index-base="hex" '
        'correct-answer="[1, 2]"></pl-array-input>'
    )

    pl_array_input.prepare(element_html, data)

    with pytest.raises(ValueError, match="complete list of indices"):
        pl_array_input.render(element_html, data)


def test_parse_accepts_single_submitted_array_and_normalizes_values() -> None:
    data = _base_data()
    element_html = (
        '<pl-array-input answers-name="regs" correct-answer="[0x0A, 0x0B]" '
        'data-base="hex"></pl-array-input>'
    )
    data["submitted_answers"]["regs"] = "[0xa, 0X0B]"

    pl_array_input.prepare(element_html, data)
    pl_array_input.parse(element_html, data)

    assert data["format_errors"] == {}
    assert data["submitted_answers"]["regs_0"] == '"0xa"'
    assert data["submitted_answers"]["regs_1"] == '"0x0b"'


def test_parse_reports_missing_blank_prefix_and_width_errors() -> None:
    data = _base_data()
    element_html = (
        '<pl-array-input answers-name="regs" correct-answer="[0x01, 0x02, 0x03, 0x04]" '
        'data-base="hex" data-fixed-width="2" unknown-value="NA"></pl-array-input>'
    )
    data["submitted_answers"].update(
        {
            "regs_1": "",
            "regs_2": "0x",
            "regs_3": "0x4",
        }
    )

    pl_array_input.prepare(element_html, data)
    pl_array_input.parse(element_html, data)

    assert data["format_errors"] == {
        "regs_0": "No submitted answer.",
        "regs_1": "Invalid format. The submitted answer was left blank.",
        "regs_2": "Invalid format. The submitted answer is only a prefix.",
        "regs_3": "Invalid format. The submitted answer is not the right length.",
    }


def test_grade_scores_numeric_equivalence_and_unknown_values() -> None:
    data = _base_data()
    element_html = (
        '<pl-array-input answers-name="regs" correct-answer="[0x0f, NA, 0x10]" '
        'data-base="hex" unknown-value="NA" signed="false"></pl-array-input>'
    )
    data["submitted_answers"].update(
        {
            "regs_0": "f",
            "regs_1": "na",
            "regs_2": "0x11",
        }
    )

    pl_array_input.prepare(element_html, data)
    pl_array_input.parse(element_html, data)
    pl_array_input.grade(element_html, data)

    assert data["partial_scores"]["regs_0"]["score"] == 1
    assert data["partial_scores"]["regs_1"]["score"] == 1
    assert data["partial_scores"]["regs_2"]["score"] == 0
    assert data["partial_scores"]["regs"]["score"] == pytest.approx(2 / 3)


def test_grade_all_or_nothing_zeroes_score_after_one_wrong_cell() -> None:
    data = _base_data()
    element_html = (
        '<pl-array-input answers-name="regs" correct-answer="[1, 2, 3]" '
        'partial-credit="false"></pl-array-input>'
    )
    data["submitted_answers"].update({"regs_0": "1", "regs_1": "2", "regs_2": "4"})

    pl_array_input.prepare(element_html, data)
    pl_array_input.parse(element_html, data)
    pl_array_input.grade(element_html, data)

    assert data["partial_scores"]["regs_0"]["score"] == 1
    assert data["partial_scores"]["regs_2"]["score"] == 0
    assert data["partial_scores"]["regs"]["score"] == 0


def test_signed_hex_grading_treats_twos_complement_values_as_equal() -> None:
    element = importlib.import_module("lxml.html").fragment_fromstring(
        '<pl-array-input data-base="hex"></pl-array-input>'
    )

    assert pl_array_input.check_answer("0xff", "-1", element) is True


def test_signed_bin_grading_treats_twos_complement_values_as_equal() -> None:
    element = importlib.import_module("lxml.html").fragment_fromstring(
        '<pl-array-input data-base="bin"></pl-array-input>'
    )

    # 1110 is -2 in two's complement, so it should match a correct answer of -2.
    assert pl_array_input.check_answer("1110", "1110", element) is True
    assert pl_array_input.check_answer("0010", "1110", element) is False


def test_strict_fixed_width_grading_marks_short_values_wrong() -> None:
    element = importlib.import_module("lxml.html").fragment_fromstring(
        '<pl-array-input data-base="bin" data-fixed-width="4" '
        'strict-grading="true"></pl-array-input>'
    )

    assert pl_array_input.check_answer("11", "0011", element) is False
    assert pl_array_input.check_answer("0011", "0011", element) is True


def test_render_read_only_displays_material_and_accepts_legacy_alias() -> None:
    data = _base_data()
    element_html = (
        '<pl-array-input answers-name="regs" correct-answer="[1, 2]" '
        'read-only="true"></pl-array-input>'
    )

    pl_array_input.prepare(element_html, data)
    rendered = _render(element_html, data)

    assert rendered["is_material"] is True

    legacy_data = _base_data()
    legacy_html = (
        '<pl-array-input answers-name="regs" correct-answer="[1, 2]" '
        'is-material="true"></pl-array-input>'
    )
    pl_array_input.prepare(legacy_html, legacy_data)
    legacy_rendered = _render(legacy_html, legacy_data)

    assert legacy_rendered["is_material"] is True
