#!/usr/bin/env python3
"""Validate the files and documentation contract for the Clear Voice repo."""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

REQUIRED_ROOT_FILES = ("README.md", "LICENSE", "LICENSE-CODE", "NOTICE.md", "SKILL.md")
MACHINE_PATH_RE = re.compile(r"(?:/Users/[^\s)\]>'\"]+|/home/[^\s)\]>'\"]+|/var/folders/[^\s)\]>'\"]+|[A-Za-z]:\\Users\\[^\s)\]>'\"]+|~/\.)")
CREDENTIAL_RE = re.compile(
    r"(?i)(?:api[_ -]?key|access[_ -]?token|secret[_ -]?key|password|private[_ -]?key)\s*[:=]\s*['\"][^'\"]+['\"]"
)
LINK_RE = re.compile(r"!?(?:\[[^]]*\])\(([^)]+)\)")
REQUIRED_DURATION_CHOICES = ("This reply", "This conversation", "Moving forward")


def add(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str, list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, "", ["SKILL.md frontmatter is missing"]
    end = text.find("\n---", 4)
    if end < 0:
        return {}, "", ["SKILL.md frontmatter is not closed"]
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"SKILL.md frontmatter line is malformed: {line}")
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = value.strip().strip("'\"")
    return fields, text[end + 4 :], errors


def validate(root: Path) -> dict[str, object]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    root = root.resolve()

    for name in REQUIRED_ROOT_FILES:
        present = (root / name).is_file()
        checks[f"required:{name}"] = present
        add(errors, present, f"missing required root file: {name}")

    references = root / "references"
    reference_files = sorted(p for p in references.rglob("*") if p.is_file()) if references.is_dir() else []
    checks["exactly_three_references"] = len(reference_files) == 3
    add(errors, len(reference_files) == 3, f"references must contain exactly three files (found {len(reference_files)})")

    skill_path = root / "SKILL.md"
    if skill_path.is_file():
        skill_text = skill_path.read_text(encoding="utf-8", errors="replace")
        fields, body, fm_errors = parse_frontmatter(skill_text)
        errors.extend(fm_errors)
        add(errors, fields.get("name") == "clear-voice", "SKILL.md frontmatter name must be clear-voice")
        trigger = fields.get("description", "")
        add(errors, (trigger.lower().startswith("use on") or trigger.lower().startswith("use when"))
            and 20 <= len(trigger) <= 350,
            "SKILL.md frontmatter description must be a concise explicit trigger starting with 'Use on' or 'Use when'")
        add(errors, fields.get("license", "").upper().startswith("CC-BY"),
            "SKILL.md frontmatter must have a CC-BY license field")
        add(errors, bool(body.strip()), "SKILL.md body must be non-empty")
        add(errors, not MACHINE_PATH_RE.search(skill_text), "SKILL.md contains an absolute machine-local path")
        add(errors, not CREDENTIAL_RE.search(skill_text), "SKILL.md contains a credential-like string")
        for target in LINK_RE.findall(skill_text):
            target = target.split("#", 1)[0].split("?", 1)[0].strip().strip("<>")
            if not target or "://" in target or target.startswith("#"):
                continue
            link_path = (skill_path.parent / target).resolve()
            try:
                link_path.relative_to(root)
                inside = True
            except ValueError:
                inside = False
            add(errors, inside and link_path.is_file(), f"SKILL.md relative reference does not resolve: {target}")

    readme_path = root / "README.md"
    if readme_path.is_file():
        readme = readme_path.read_text(encoding="utf-8", errors="replace")
        has_duration_choices = all(re.search(re.escape(choice), readme, re.I) for choice in REQUIRED_DURATION_CHOICES)
        add(errors, has_duration_choices, "README.md must include the three duration choices: "
            + ", ".join(REQUIRED_DURATION_CHOICES))
        add(errors, bool(re.search(r"current[- ]client", readme, re.I) and re.search(r"profile", readme, re.I)
                           and re.search(r"persist|boundary", readme, re.I)),
            "README.md must state the current-client/profile persistence boundary")
        add(errors, bool(re.search(r"related writing styles", readme, re.I)),
            "README.md must include a 'Related writing styles' section")
        add(errors, bool(re.search(r"author", readme, re.I) and re.search(r"repo|repository", readme, re.I)
                           and re.search(r"license", readme, re.I)),
            "README.md must include external author/repository/license notes")
        add(errors, bool(re.search(r"caveman", readme, re.I) and re.search(r"untested", readme, re.I)
                           and re.search(r"persistent", readme, re.I) and re.search(r"auto[- ]trigger", readme, re.I)),
            "README.md must include the Caveman untested/persistent/auto-trigger caveat")
        add(errors, bool(re.search(r"claude", readme, re.I) and re.search(r"limitation|cannot verify|unable to verify", readme, re.I)),
            "README.md must state the Claude verification limitation")
        negative_disclosures = re.compile(
            r"(?i)\bnot\s+(?:officially\s+)?(?:affiliated\s+with|compatible\s+with|endorsed\s+by)(?:\s+or\s+(?:not\s+)?endorsed\s+by)?"
        )
        claim_text = negative_disclosures.sub("", readme)
        claims = re.compile(r"(?i)(?:officially\s+affiliat|affiliated\s+with|compatible\s+with|endorsed\s+by|official\s+endorsement|we\s+endorse)")
        add(errors, not claims.search(claim_text), "README.md contains a compatibility, affiliation, or endorsement claim")

    for name in ("LICENSE", "NOTICE.md"):
        path = root / name
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            good = bool(re.search(r"copyright", text, re.I) and re.search(r"attribution|clear voice", text, re.I))
            checks[f"attribution:{name}"] = good
            add(errors, good, f"{name} must contain copyright and attribution markers")

    code_license = root / "LICENSE-CODE"
    if code_license.is_file():
        text = code_license.read_text(encoding="utf-8", errors="replace")
        good = bool(re.search(r"MIT License", text, re.I) and re.search(r"permission is hereby granted", text, re.I))
        checks["license_code_mit"] = good
        add(errors, good, "LICENSE-CODE must be the MIT license")

    dist_package = root / "dist" / "clear-voice.skill"
    if dist_package.is_file():
        expected = {f"clear-voice/{name}": root / name
                    for name in ("SKILL.md", "NOTICE.md", "LICENSE", "README.md")}
        for ref in reference_files:
            expected[f"clear-voice/references/{ref.name}"] = ref
        fresh = True
        try:
            with zipfile.ZipFile(dist_package) as zf:
                names = set(zf.namelist())
                for arcname, source in expected.items():
                    if not source.is_file():
                        continue
                    if arcname not in names or zf.read(arcname) != source.read_bytes():
                        fresh = False
                        add(errors, False,
                            f"dist/clear-voice.skill is stale: {arcname} does not match the "
                            "repository file; regenerate the package from the current files")
        except zipfile.BadZipFile:
            fresh = False
            add(errors, False, "dist/clear-voice.skill is not a valid zip archive")
        checks["dist_package_fresh"] = fresh

    forbidden_vendor = []
    forbidden_automation = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_relative_to(root / "tests"):
            continue
        relative = path.relative_to(root)
        parts = [part.lower() for part in relative.parts]
        joined = "/".join(parts)
        if "attention-span" in joined or "attention_span" in joined or "caveman" in joined:
            forbidden_vendor.append(str(relative))
        if (parts[0] in {".github", ".gitlab", ".circleci", "ci"}
                or path.name.lower() in {".travis.yml", "jenkinsfile", "makefile", "setup.py"}
                or re.match(r"(?:install|setup)(?:[-_].*)?\.(?:sh|bash|zsh)$", path.name, re.I)):
            forbidden_automation.append(str(relative))
    add(errors, not forbidden_vendor, "vendored attention-span or Caveman files are forbidden: " + ", ".join(forbidden_vendor))
    add(errors, not forbidden_automation, "CI/install automation files are forbidden: " + ", ".join(forbidden_automation))

    return {"ok": not errors, "root": str(root), "errors": errors, "checks": checks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    result = validate(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
