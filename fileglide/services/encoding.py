"""Encoding detection and lossless write checks for text workflows."""

from __future__ import annotations

import codecs
import unicodedata
from pathlib import Path
from typing import Any

from charset_normalizer import from_bytes, is_binary

from fileglide.exceptions import EncodingRiskError


DEFAULT_TEXT_ENCODING = "utf-8"
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
            }

        if not payload:
            return {
                "encoding": DEFAULT_TEXT_ENCODING,
                "bom": False,
                "confidence": 1.0,
                "source": "default-empty",
                "text": "",
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
            }

        common_candidate = self._detect_common_encoding(payload)
        if common_candidate is not None:
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
            }

        return {
            "encoding": match.encoding.replace("_", "-"),
            "bom": match.bom,
            "confidence": max(0.0, 1.0 - match.chaos),
            "source": "charset-normalizer",
            "text": str(match),
            "language": match.language,
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

    def validate_round_trip(self, text: str, encoding: str) -> dict[str, Any]:
        """Ensure the provided text can be losslessly written with the encoding."""

        try:
            encoded = text.encode(encoding)
        except UnicodeEncodeError as exc:
            raise EncodingRiskError(
                code="encoding_not_lossless",
                message=(
                    "Text cannot be encoded losslessly with the requested "
                    "encoding."
                ),
                details={"encoding": encoding, "reason": str(exc)},
            ) from exc

        decoded = encoded.decode(encoding)
        if decoded != text:
            raise EncodingRiskError(
                code="encoding_round_trip_mismatch",
                message="Text changed during encoding round-trip validation.",
                details={"encoding": encoding},
            )
        return {"encoding": encoding, "size_bytes": len(encoded), "lossless": True}

    def encoding_for_write(
        self,
        *,
        existing_encoding: str | None = None,
        requested_encoding: str | None = None,
    ) -> str:
        """Choose the target encoding for text writes."""

        if requested_encoding:
            return requested_encoding
        if existing_encoding:
            return existing_encoding
        return DEFAULT_TEXT_ENCODING

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
