#!/usr/bin/env python3
"""Translate IG pagecontent Markdown files from French to English using Albert API."""

import os
import sys
import argparse
import httpx
from pathlib import Path

ALBERT_API_URL = "https://albert.api.etalab.gouv.fr/v1/chat/completions"
DEFAULT_MODEL = "mistralai/Mistral-Small-3.2-24B-Instruct-2506"

SYSTEM_PROMPT = """You are a medical/technical translator specializing in French healthcare interoperability documentation (FHIR Implementation Guides).

Translate the following Markdown/HTML content from French to English.

Strict rules:
- Preserve ALL technical elements exactly as-is without any modification:
  * Liquid/Jekyll tags: {% sql ... %}, {% include ... %}, {% lang-fragment ... %}
  * HTML tags and their attributes (style, class, src, alt, title, etc.)
  * FHIR resource names, profile identifiers, search parameter names
  * French code identifiers: TRE_xxx, JDV_xxx, ASS_xxx, flux names (e.g. Flux1, CreationCercleSoins)
  * URLs, canonical links, anchor links
  * Image src paths (e.g. sf_image1.png)
  * Markdown structure: heading levels (###, ####, etc.), tables, lists, bold/italic
  * Code blocks (``` ... ```) — do not translate their content
- Translate ONLY the human-readable French prose and labels
- Do NOT add any explanations, preamble, or trailing comment
- Return ONLY the translated content"""


def translate_content(content: str, token: str, model: str) -> str:
    response = httpx.post(
        ALBERT_API_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            "max_tokens": 8192,
            "temperature": 0.1,
        },
        timeout=120.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def main():
    parser = argparse.ArgumentParser(
        description="Translate IG pagecontent from French to English with Albert API"
    )
    parser.add_argument(
        "--source-dir",
        default="input/pagecontent",
        help="Directory containing the French .md source files (default: input/pagecontent)",
    )
    parser.add_argument(
        "--target-dir",
        default="input/translations/en/pagecontent",
        help="Directory where English translations will be written (default: input/translations/en/pagecontent)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Albert model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Retranslate files even if a translation already exists",
    )
    args = parser.parse_args()

    token = os.environ.get("ALBERT_API_KEY")
    if not token:
        print("Error: ALBERT_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)

    source_dir = Path(args.source_dir)
    target_dir = Path(args.target_dir)

    if not source_dir.is_dir():
        print(f"Error: source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    target_dir.mkdir(parents=True, exist_ok=True)

    md_files = sorted(source_dir.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {source_dir}")
        return

    translated_count = 0
    skipped_count = 0

    for source_file in md_files:
        target_file = target_dir / source_file.name
        content = source_file.read_text(encoding="utf-8")

        if not content.strip():
            print(f"Skipping {source_file.name} (empty file)")
            skipped_count += 1
            continue

        if target_file.exists() and not args.force:
            print(f"Skipping {source_file.name} (translation exists — use --force to retranslate)")
            skipped_count += 1
            continue

        print(f"Translating {source_file.name}...", end=" ", flush=True)
        try:
            translated = translate_content(content, token, args.model)
            target_file.write_text(translated, encoding="utf-8")
            print("OK")
            translated_count += 1
        except httpx.HTTPStatusError as e:
            print(f"FAILED (HTTP {e.response.status_code})", file=sys.stderr)
            print(e.response.text, file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"FAILED: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"\nDone: {translated_count} translated, {skipped_count} skipped.")


if __name__ == "__main__":
    main()
