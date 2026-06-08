"""Regression tests for the fileglide CLI."""

from __future__ import annotations

import json
from pathlib import Path


def parse_json(output: str) -> dict:
    """Parse a CLI JSON response."""

    return json.loads(output)


def test_file_create_and_exists(cli, runner, workspace: Path) -> None:
    result = runner.invoke(
        cli, ["file", "create", "--root", str(workspace), "sample.txt"]
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["ok"] is True
    assert payload["result"]["entry"]["name"] == "sample.txt"

    exists = runner.invoke(
        cli, ["file", "exists", "--root", str(workspace), "sample.txt"]
    )
    assert exists.exit_code == 0, exists.output
    exists_payload = parse_json(exists.output)
    assert exists_payload["result"]["entry"]["exists"] is True


def test_path_delete_dry_run_returns_preview(cli, runner, workspace: Path) -> None:
    target = workspace / "to-delete"
    target.mkdir()
    (target / "nested.txt").write_text("content", encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "path",
            "delete",
            "--root",
            str(workspace),
            "--recursive",
            "--dry-run",
            "to-delete",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["ok"] is True
    assert payload["result"]["preview"]["dry_run"] is True
    assert target.exists()


def test_tree_list_respects_depth(cli, runner, workspace: Path) -> None:
    (workspace / "docs" / "nested").mkdir()
    (workspace / "docs" / "nested" / "deep.txt").write_text("deep", encoding="utf-8")

    result = runner.invoke(
        cli,
        ["tree", "list", "--root", str(workspace), "--max-depth", "1", "docs"],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    relative_paths = {entry["relative_path"] for entry in payload["result"]["entries"]}
    assert "docs/nested/deep.txt" not in relative_paths


def test_text_read_write_and_replace_lines(cli, runner, workspace: Path) -> None:
    write_result = runner.invoke(
        cli,
        [
            "text",
            "write",
            "--root",
            str(workspace),
            "--mode",
            "overwrite",
            "--content",
            "first\nsecond\nthird\n",
            "editable.txt",
        ],
    )
    assert write_result.exit_code == 0, write_result.output

    read_result = runner.invoke(
        cli,
        [
            "text",
            "read",
            "--root",
            str(workspace),
            "--start-line",
            "2",
            "--end-line",
            "3",
            "editable.txt",
        ],
    )
    assert read_result.exit_code == 0, read_result.output
    read_payload = parse_json(read_result.output)
    assert [line["text"] for line in read_payload["result"]["lines"]] == [
        "second",
        "third",
    ]

    replace_result = runner.invoke(
        cli,
        [
            "text",
            "replace-lines",
            "--root",
            str(workspace),
            "--start-line",
            "2",
            "--end-line",
            "2",
            "--content",
            "updated\n",
            "editable.txt",
        ],
    )
    assert replace_result.exit_code == 0, replace_result.output
    assert (workspace / "editable.txt").read_text(
        encoding="utf-8"
    ) == "first\nupdated\nthird\n"


def test_regex_search_and_fuzzy_search(cli, runner, workspace: Path) -> None:
    grep_result = runner.invoke(
        cli, ["text", "grep", "--root", str(workspace), "match", "docs"]
    )
    assert grep_result.exit_code == 0, grep_result.output
    grep_payload = parse_json(grep_result.output)
    assert grep_payload["result"]["count"] == 1
    assert grep_payload["result"]["matches"][0]["line_number"] == 2

    fuzzy_result = runner.invoke(
        cli,
        [
            "file",
            "search",
            "--root",
            str(workspace),
            "--mode",
            "fuzzy",
            "alpah",
            "docs",
        ],
    )
    assert fuzzy_result.exit_code == 0, fuzzy_result.output
    fuzzy_payload = parse_json(fuzzy_result.output)
    assert fuzzy_payload["result"]["matches"][0]["name"] == "alpha.txt"


def test_binary_read_write_and_copy(cli, runner, workspace: Path) -> None:
    write_result = runner.invoke(
        cli,
        [
            "text",
            "binary-write",
            "--root",
            str(workspace),
            "--data-hex",
            "a1b2c3",
            "copy.bin",
        ],
    )
    assert write_result.exit_code == 0, write_result.output

    read_result = runner.invoke(
        cli,
        [
            "inspect",
            "bytes",
            "--root",
            str(workspace),
            "--offset",
            "1",
            "--length",
            "2",
            "copy.bin",
        ],
    )
    assert read_result.exit_code == 0, read_result.output
    read_payload = parse_json(read_result.output)
    assert read_payload["result"]["content_hex"] == "b2c3"

    copy_result = runner.invoke(
        cli,
        ["text", "binary-copy", "--root", str(workspace), "copy.bin", "copy-2.bin"],
    )
    assert copy_result.exit_code == 0, copy_result.output
    assert (workspace / "copy-2.bin").read_bytes() == bytes.fromhex("a1b2c3")


def test_batch_run_dry_run(
    cli, runner, sample_plan_path: Path, workspace: Path
) -> None:
    result = runner.invoke(cli, ["batch", "run", "--dry-run", str(sample_plan_path)])
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["dry_run"] is True
    assert payload["result"]["step_count"] == 2
    assert not (workspace / "generated.txt").exists()


def test_encoding_fixtures_are_readable(cli, runner, fixture_root: Path) -> None:
    result = runner.invoke(
        cli,
        ["text", "read", "--root", str(fixture_root / "encodings"), "gbk.txt"],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["content"] == "中文样本"
    assert payload["result"]["encoding"]["name"] in {"gb18030", "gbk"}

    utf16 = runner.invoke(
        cli,
        ["text", "read", "--root", str(fixture_root / "encodings"), "utf-16-le.txt"],
    )
    assert utf16.exit_code == 0, utf16.output
    utf16_payload = parse_json(utf16.output)
    assert utf16_payload["result"]["content"] == "UTF16样本"
    assert utf16_payload["result"]["encoding"]["name"] in {"utf-16", "utf-16-le"}


def test_text_read_rejects_binary_payload(cli, runner, fixture_root: Path) -> None:
    result = runner.invoke(
        cli,
        ["text", "read", "--root", str(fixture_root / "binary"), "sample.bin"],
    )
    assert result.exit_code == 1, result.output
    payload = parse_json(result.output)
    assert payload["errors"][0]["code"] == "binary_detected"
