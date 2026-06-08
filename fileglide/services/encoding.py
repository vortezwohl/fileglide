"""Encoding detection and lossless write checks for text workflows."""

from __future__ import annotations

import codecs
import hashlib
import os
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

from charset_normalizer import from_bytes, is_binary

from fileglide.exceptions import EncodingRiskError


DEFAULT_TEXT_ENCODING = "utf-8"
DEFAULT_NEWLINE = "\n"
COMMON_ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "gb18030",
    "gbk",
    "shift_jis",
    "utf-16",
    "utf-16-le",
    "utf-16-be",
]
BOM_MAP = {
    codecs.BOM_UTF8: "utf-8-sig",
    codecs.BOM_UTF16_LE: "utf-16-le",
    codecs.BOM_UTF16_BE: "utf-16-be",
}
BOM_BYTES = {
    "utf-8": b"",
    "utf-8-sig": codecs.BOM_UTF8,
    "utf-16": b"",
    "utf-16-le": codecs.BOM_UTF16_LE,
    "utf-16-be": codecs.BOM_UTF16_BE,
    "gb18030": b"",
    "gbk": b"",
    "shift_jis": b"",
}


class EncodingService:
    """Detect encodings, decode bytes, and validate text write safety."""

    def detect(
        self, payload: bytes, explicit_encoding: str | None = None
    ) -> dict[str, Any]:
        """Detect the most suitable text encoding for a payload."""

        if explicit_encoding is not None:
            text = payload.decode(explicit_encoding)
            return {
                "encoding": explicit_encoding,
                "bom": payload.startswith(codecs.BOM_UTF8),
                "confidence": 1.0,
                "source": "explicit",
                "text": text,
                "size_bytes": len(payload),
            }

        if not payload:
            return {
                "encoding": DEFAULT_TEXT_ENCODING,
                "bom": False,
                "confidence": 1.0,
                "source": "default-empty",
                "text": "",
                "size_bytes": 0,
            }

        bom_encoding = self._detect_bom(payload)
        if bom_encoding is not None:
            text = payload.decode(bom_encoding)
            return {
                "encoding": bom_encoding,
                "bom": True,
                "confidence": 1.0,
                "source": "bom",
                "text": text,
                "size_bytes": len(payload),
            }

        utf16_pattern_encoding = self._detect_utf16_without_bom(payload)
        if utf16_pattern_encoding is not None:
            text = payload.decode(utf16_pattern_encoding)
            return {
                "encoding": utf16_pattern_encoding,
                "bom": False,
                "confidence": 0.95,
                "source": "utf16-pattern",
                "text": text,
                "language": self._infer_language(text),
                "size_bytes": len(payload),
            }

        common_candidate = self._detect_common_encoding(payload)
        if common_candidate is not None:
            common_candidate["size_bytes"] = len(payload)
            return common_candidate

        matches = from_bytes(payload)
        match = matches.best() if matches else None
        if match is None:
            text = payload.decode(DEFAULT_TEXT_ENCODING)
            return {
                "encoding": DEFAULT_TEXT_ENCODING,
                "bom": False,
                "confidence": 0.0,
                "source": "fallback",
                "text": text,
                "size_bytes": len(payload),
            }

        return {
            "encoding": match.encoding.replace("_", "-"),
            "bom": match.bom,
            "confidence": max(0.0, 1.0 - match.chaos),
            "source": "charset-normalizer",
            "text": str(match),
            "language": match.language,
            "size_bytes": len(payload),
        }

    def decode_path(
        self, path: Path, explicit_encoding: str | None = None
    ) -> dict[str, Any]:
        """Read a path as text using explicit or detected encoding."""

        payload = path.read_bytes()
        detection = self.detect(payload, explicit_encoding=explicit_encoding)
        detection["size_bytes"] = len(payload)
        return detection

    def is_binary_payload(self, payload: bytes) -> bool:
        """Determine whether a payload should be treated as binary."""

        return bool(payload) and is_binary(payload)

    def is_binary_path(self, path: Path) -> bool:
        """Determine whether a file should be treated as binary."""

        payload = path.read_bytes()
        return self.is_binary_payload(payload)

    def ensure_text(
        self, path: Path, explicit_encoding: str | None = None
    ) -> dict[str, Any]:
        """Load text metadata and fail if the file looks binary."""

        payload = path.read_bytes()
        if self.is_binary_payload(payload):
            raise EncodingRiskError(
                code="binary_detected",
                message="The target appears to be binary, not text.",
                details={"path": str(path)},
                path=str(path),
            )
        return self.detect(payload, explicit_encoding=explicit_encoding)

    def resolve_write_policy(
        self,
        *,
        existing_encoding: str | None = None,
        existing_bom: bool = False,
        existing_newline: str | None = None,
        requested_encoding: str | None = None,
    ) -> dict[str, Any]:
        """Choose charset, BOM policy, and newline policy for text writes."""

        charset = requested_encoding or existing_encoding or DEFAULT_TEXT_ENCODING
        bom = existing_bom if requested_encoding is None else self._default_bom_for_encoding(charset)
        newline = existing_newline or DEFAULT_NEWLINE
        return {
            "charset": charset,
            "bom": bom,
            "newline": newline,
            "charset_source": "requested" if requested_encoding else (
                "existing" if existing_encoding else "default"
            ),
            "bom_source": "existing" if existing_encoding and requested_encoding is None else "default",
            "newline_source": "existing" if existing_newline else "default",
        }

    def serialize_text(self, text: str, *, charset: str, bom: bool) -> bytes:
        """Serialize text to bytes with explicit charset and BOM behavior."""

        try:
            if charset == "utf-8-sig":
                return text.encode("utf-8-sig")
            encoded = text.encode(charset)
        except UnicodeEncodeError as exc:
            raise EncodingRiskError(
                code="encoding_not_lossless",
                message=(
                    "Text cannot be encoded losslessly with the requested encoding."
                ),
                details={"encoding": charset, "reason": str(exc)},
            ) from exc

        prefix = self._bom_prefix(charset, bom)
        if prefix and not encoded.startswith(prefix):
            return prefix + encoded
        if not prefix:
            existing_prefix = self._bom_prefix(charset, True)
            if existing_prefix and encoded.startswith(existing_prefix):
                return encoded[len(existing_prefix) :]
        return encoded

    def verify_serialized_bytes(
        self, text: str, payload: bytes, *, charset: str, bom: bool
    ) -> dict[str, Any]:
        """Verify that serialized bytes decode back to the exact source text."""

        decoded_payload = payload
        prefix = self._bom_prefix(charset, bom)
        if prefix and payload.startswith(prefix):
            decoded_payload = payload[len(prefix) :]
        try:
            decoded_text = decoded_payload.decode(self._decode_charset_for_verify(charset))
        except UnicodeDecodeError as exc:
            raise EncodingRiskError(
                code="write_verification_failed",
                message="Serialized bytes could not be decoded during verification.",
                details={"encoding": charset, "reason": str(exc)},
            ) from exc
        if decoded_text != text:
            raise EncodingRiskError(
                code="write_verification_failed",
                message="Serialized bytes did not round-trip to the expected text.",
                details={"encoding": charset},
            )
        return {
            "verified": True,
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    def atomic_write_bytes(self, path: Path, payload: bytes) -> None:
        """Persist bytes using a same-directory atomic replace."""

        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    @staticmethod
    def detect_newline(text: str) -> str:
        """Infer the dominant newline style from decoded text."""

        if "\r\n" in text:
            return "\r\n"
        if "\r" in text:
            return "\r"
        return DEFAULT_NEWLINE

    @staticmethod
    def _detect_bom(payload: bytes) -> str | None:
        """Detect an explicit BOM-based encoding."""

        for bom, encoding in BOM_MAP.items():
            if payload.startswith(bom):
                return encoding
        return None

    @staticmethod
    def _detect_utf16_without_bom(payload: bytes) -> str | None:
        """Detect likely UTF-16 text when no BOM is present."""

        if len(payload) < 4 or len(payload) % 2 != 0:
            return None
        even_bytes = payload[0::2]
        odd_bytes = payload[1::2]
        even_zero_ratio = even_bytes.count(0) / len(even_bytes)
        odd_zero_ratio = odd_bytes.count(0) / len(odd_bytes)
        if odd_zero_ratio >= 0.3 and even_zero_ratio <= 0.05:
            return "utf-16-le"
        if even_zero_ratio >= 0.3 and odd_zero_ratio <= 0.05:
            return "utf-16-be"
        return None

    def _detect_common_encoding(self, payload: bytes) -> dict[str, Any] | None:
        """Prefer the project-supported common encodings before falling back."""

        candidates = []
        for encoding in COMMON_ENCODINGS:
            if encoding in {"utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"}:
                continue
            try:
                text = payload.decode(encoding)
                if text.encode(encoding) != payload:
                    continue
            except (UnicodeDecodeError, UnicodeEncodeError):
                continue

            profile = self._profile_text(text)
            score = self._score_candidate(encoding, profile)
            candidates.append(
                {
                    "encoding": encoding,
                    "bom": False,
                    "confidence": min(1.0, 0.5 + score / 100.0),
                    "source": "common-encoding",
                    "text": text,
                    "language": self._infer_language(text),
                    "_score": score,
                }
            )

        if not candidates:
            return None

        best = max(
            candidates,
            key=lambda item: (
                item["_score"],
                -COMMON_ENCODINGS.index(item["encoding"]),
            ),
        )
        best.pop("_score", None)
        return best

    @staticmethod
    def _profile_text(text: str) -> dict[str, int]:
        """Collect simple Unicode script and control character counts."""

        profile = {
            "length": len(text),
            "ascii": 0,
            "han": 0,
            "hiragana": 0,
            "katakana": 0,
            "control": 0,
        }
        for char in text:
            codepoint = ord(char)
            if codepoint < 128:
                profile["ascii"] += 1
            if 0x4E00 <= codepoint <= 0x9FFF:
                profile["han"] += 1
            if 0x3040 <= codepoint <= 0x309F:
                profile["hiragana"] += 1
            if 0x30A0 <= codepoint <= 0x30FF:
                profile["katakana"] += 1
            if unicodedata.category(char).startswith("C") and char not in {
                "\n",
                "\r",
                "\t",
            }:
                profile["control"] += 1
        return profile

    @staticmethod
    def _score_candidate(encoding: str, profile: dict[str, int]) -> int:
        """Score a decoded candidate using project-specific heuristics."""

        length = max(profile["length"], 1)
        kana_count = profile["hiragana"] + profile["katakana"]
        score = 0
        if encoding == "utf-8":
            score += 40 if profile["ascii"] == length else 30
        elif encoding == "shift_jis":
            score += 45 if kana_count > 0 else 18
        elif encoding == "gb18030":
            score += 36 if profile["han"] > 0 and kana_count == 0 else 8
        elif encoding == "gbk":
            score += 35 if profile["han"] > 0 and kana_count == 0 else 7
        else:
            score += 5

        if profile["control"]:
            score -= 25 * profile["control"]
        if profile["han"] > 0:
            score += 10
        if kana_count > 0:
            score += 10
        return score

    @staticmethod
    def _infer_language(text: str) -> str:
        """Infer a coarse language label from the decoded text scripts."""

        profile = EncodingService._profile_text(text)
        if profile["hiragana"] + profile["katakana"] > 0:
            return "Japanese"
        if profile["han"] > 0:
            return "Chinese"
        if profile["ascii"] == profile["length"]:
            return "English"
        return "Unknown"

    @staticmethod
    def _default_bom_for_encoding(encoding: str) -> bool:
        """Return the default BOM behavior for a chosen encoding."""

        return encoding == "utf-8-sig"

    @staticmethod
    def _decode_charset_for_verify(encoding: str) -> str:
        """Map serialization charset to a decode charset used for verification."""

        if encoding == "utf-8-sig":
            return "utf-8"
        return encoding

    @staticmethod
    def _bom_prefix(encoding: str, enabled: bool) -> bytes:
        """Resolve a BOM byte prefix for the target encoding and policy."""

        if not enabled:
            return b""
        return BOM_BYTES.get(encoding, b"")
