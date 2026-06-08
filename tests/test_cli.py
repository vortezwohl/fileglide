"""Regression tests for the fileglide CLI."""

from __future__ import annotations

import json
import subprocess
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


def test_file_move_supports_cross_root(
    cli, runner, workspace: Path, tmp_path_factory
) -> None:
    destination_root = tmp_path_factory.mktemp("file-move-destination")

    result = runner.invoke(
        cli,
        [
            "file",
            "move",
            "--root",
            str(workspace),
            "--to-root",
            str(destination_root),
            "--confirm",
            "docs/alpha.txt",
            "alpha.txt",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["moved"] is True
    assert payload["result"]["cross_root"] is True
    assert payload["result"]["source"]["exists"] is False
    assert payload["result"]["destination"]["exists"] is True
    assert not (workspace / "docs" / "alpha.txt").exists()
    assert (destination_root / "alpha.txt").read_text(encoding="utf-8") == (
        "alpha\nbeta\ngamma\n"
    )


def test_path_move_moves_descendants_cross_root(
    cli, runner, workspace: Path, tmp_path_factory
) -> None:
    destination_root = tmp_path_factory.mktemp("path-move-destination")

    result = runner.invoke(
        cli,
        [
            "path",
            "move",
            "--root",
            str(workspace),
            "--to-root",
            str(destination_root),
            "--confirm",
            "docs",
            "docs-archive",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["moved"] is True
    assert payload["result"]["cross_root"] is True
    assert not (workspace / "docs").exists()
    assert (destination_root / "docs-archive" / "alpha.txt").exists()
    assert (destination_root / "docs-archive" / "notes.log").exists()


def test_file_move_dry_run_returns_preview(cli, runner, workspace: Path) -> None:
    result = runner.invoke(
        cli,
        [
            "file",
            "move",
            "--root",
            str(workspace),
            "--dry-run",
            "docs/alpha.txt",
            "alpha-moved.txt",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["moved"] is False
    assert payload["result"]["preview"]["dry_run"] is True
    assert (workspace / "docs" / "alpha.txt").exists()
    assert not (workspace / "alpha-moved.txt").exists()


def test_path_move_rejects_destination_inside_source(
    cli, runner, workspace: Path
) -> None:
    result = runner.invoke(
        cli,
        [
            "path",
            "move",
            "--root",
            str(workspace),
            "--confirm",
            "docs",
            "docs/archive",
        ],
    )
    assert result.exit_code == 1, result.output
    payload = parse_json(result.output)
    assert payload["errors"][0]["code"] == "destination_inside_source"


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
    write_payload = parse_json(write_result.output)
    assert write_payload["result"]["data_source"]["source"] == "hex"

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


def test_text_replace_lines_preserves_next_line_without_trailing_newline_lf(
    cli, runner, workspace: Path
) -> None:
    target = workspace / "lf-lines.txt"
    target.write_text("first\nsecond\nthird\n", encoding="utf-8")

    result = runner.invoke(
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
            "updated",
            "lf-lines.txt",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["encoding"]["newline"] == "\n"
    assert target.read_text(encoding="utf-8") == "first\nupdated\nthird\n"


def test_text_replace_lines_preserves_next_line_without_trailing_newline_crlf(
    cli, runner, workspace: Path
) -> None:
    target = workspace / "crlf-lines.txt"
    target.write_bytes(b"first\r\nsecond\r\nthird\r\n")

    result = runner.invoke(
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
            "updated",
            "crlf-lines.txt",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["encoding"]["newline"] == "\r\n"
    assert target.read_bytes() == b"first\r\nupdated\r\nthird\r\n"


def test_text_write_accepts_content_file(cli, runner, workspace: Path) -> None:
    payload_path = workspace / "payload.txt"
    payload_path.write_text(
        "<section>\u4e2d\u6587\u3068\u65e5\u672c\u8a9e</section>\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "text",
            "write",
            "--root",
            str(workspace),
            "--content-file",
            str(payload_path),
            "written.txt",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["content_source"]["source"] == "file"
    assert payload["result"]["verification"]["verified"] is True
    assert (workspace / "written.txt").read_text(encoding="utf-8") == (
        "<section>\u4e2d\u6587\u3068\u65e5\u672c\u8a9e</section>\n"
    )


def test_text_write_accepts_utf8_stdin_payload(cli, runner, workspace: Path) -> None:
    payload_text = "<div title=\"quote\">\u4e2d\u6587\n\u65e5\u672c\u8a9e</div>\n"

    result = runner.invoke(
        cli,
        [
            "text",
            "write",
            "--root",
            str(workspace),
            "--content-stdin",
            "stdin.html",
        ],
        input=payload_text,
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["content_source"]["source"] == "stdin"
    assert payload["result"]["verification"]["verified"] is True
    assert (workspace / "stdin.html").read_text(encoding="utf-8") == payload_text


def test_binary_write_accepts_data_file(cli, runner, workspace: Path) -> None:
    payload_path = workspace / "payload.bin"
    payload_path.write_bytes(bytes.fromhex("00ff10aa"))

    result = runner.invoke(
        cli,
        [
            "text",
            "binary-write",
            "--root",
            str(workspace),
            "--data-file",
            str(payload_path),
            "from-file.bin",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["data_source"]["source"] == "file"
    assert (workspace / "from-file.bin").read_bytes() == bytes.fromhex("00ff10aa")


def test_binary_write_rejects_conflicting_sources(cli, runner, workspace: Path) -> None:
    payload_path = workspace / "payload.bin"
    payload_path.write_bytes(bytes.fromhex("abcd"))

    result = runner.invoke(
        cli,
        [
            "text",
            "binary-write",
            "--root",
            str(workspace),
            "--data-hex",
            "abcd",
            "--data-file",
            str(payload_path),
            "conflict.bin",
        ],
    )
    assert result.exit_code == 1, result.output
    payload = parse_json(result.output)
    assert payload["errors"][0]["code"] == "invalid_content_source_combination"


def test_text_write_rejects_conflicting_content_sources(
    cli, runner, workspace: Path
) -> None:
    payload_path = workspace / "payload.txt"
    payload_path.write_text("content\n", encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "text",
            "write",
            "--root",
            str(workspace),
            "--content",
            "inline",
            "--content-file",
            str(payload_path),
            "conflict.txt",
        ],
    )
    assert result.exit_code == 1, result.output
    payload = parse_json(result.output)
    assert payload["errors"][0]["code"] == "invalid_content_source_combination"


def test_text_replace_lines_preserves_bom_and_reports_verification(
    cli, runner, workspace: Path
) -> None:
    target = workspace / "bom.txt"
    target.write_bytes(b"\xef\xbb\xbfalpha\nbeta\n")

    result = runner.invoke(
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
            "\u4e2d\u6587beta",
            "bom.txt",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["encoding"]["bom"] is True
    assert payload["result"]["verification"]["verified"] is True
    assert target.read_bytes().startswith(b"\xef\xbb\xbf")


def test_encoding_fixtures_are_readable(cli, runner, fixture_root: Path) -> None:
    result = runner.invoke(
        cli,
        ["text", "read", "--root", str(fixture_root / "encodings"), "gbk.txt"],
    )
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["content"] == "\u4e2d\u6587\u6837\u672c"
    assert payload["result"]["encoding"]["name"] in {"gb18030", "gbk"}

    utf16 = runner.invoke(
        cli,
        ["text", "read", "--root", str(fixture_root / "encodings"), "utf-16-le.txt"],
    )
    assert utf16.exit_code == 0, utf16.output
    utf16_payload = parse_json(utf16.output)
    assert utf16_payload["result"]["content"] == "UTF16\u6837\u672c"
    assert utf16_payload["result"]["encoding"]["name"] in {"utf-16", "utf-16-le"}


def test_text_read_rejects_binary_payload(cli, runner, fixture_root: Path) -> None:
    result = runner.invoke(
        cli,
        ["text", "read", "--root", str(fixture_root / "binary"), "sample.bin"],
    )
    assert result.exit_code == 1, result.output
    payload = parse_json(result.output)
    assert payload["errors"][0]["code"] == "binary_detected"


def test_text_stdin_supports_utf8_bytes_via_subprocess(workspace: Path) -> None:
    command = [
        str(Path(__file__).resolve().parents[1] / ".venv" / "Scripts" / "fileglide.exe"),
        "text",
        "write",
        "--root",
        str(workspace),
        "--content-stdin",
        "stdin-bytes.txt",
    ]
    payload_text = "<x>\u4e2d\u6587\u3068\u65e5\u672c\u8a9e</x>\n"
    completed = subprocess.run(
        command,
        input=payload_text.encode("utf-8"),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout.decode("utf-8")
    response = parse_json(completed.stdout.decode("utf-8"))
    assert response["result"]["content_source"]["source"] == "stdin"
    assert (workspace / "stdin-bytes.txt").read_text(encoding="utf-8") == payload_text


def test_batch_run_dry_run(
    cli, runner, sample_plan_path: Path, workspace: Path
) -> None:
    result = runner.invoke(cli, ["batch", "run", "--dry-run", str(sample_plan_path)])
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["dry_run"] is True
    assert payload["result"]["step_count"] == 2
    assert not (workspace / "generated.txt").exists()


def test_batch_run_dry_run_supports_file_move(
    cli, runner, workspace: Path, tmp_path: Path, tmp_path_factory
) -> None:
    destination_root = tmp_path_factory.mktemp("batch-move-destination")
    plan_path = tmp_path / "move-plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "action": "file.move",
                        "arguments": {
                            "root": str(workspace),
                            "source": "docs/alpha.txt",
                            "destination_root": str(destination_root),
                            "destination": "alpha.txt",
                            "confirm": True,
                        },
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(cli, ["batch", "run", "--dry-run", str(plan_path)])
    assert result.exit_code == 0, result.output
    payload = parse_json(result.output)
    assert payload["result"]["results"][0]["ok"] is True

