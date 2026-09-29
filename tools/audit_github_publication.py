from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "GITHUB_PUBLICATION_AUDIT.md"
GITHUB_LIMIT = 100 * 1024 * 1024
WARNING_LIMIT = 50 * 1024 * 1024
TEXT_SCAN_LIMIT = 4 * 1024 * 1024


@dataclass(frozen=True)
class Finding:
    level: str
    message: str


def git_bytes(*args: str) -> bytes:
    proc = subprocess.run(
        ["git", *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace").strip())
    return proc.stdout


def repository_files() -> list[Path]:
    raw = git_bytes("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    names = [item for item in raw.decode("utf-8", errors="surrogateescape").split("\0") if item]
    return [ROOT / name for name in names if (ROOT / name).is_file()]


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def readable_text(path: Path) -> str | None:
    if path.stat().st_size > TEXT_SCAN_LIMIT:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace")


def main() -> int:
    findings: list[Finding] = []
    files = repository_files()
    scanned_text = 0
    absolute_windows_paths: list[str] = []

    required = {
        "LICENSE": "PolyForm Noncommercial License 1.0.0",
        "LICENSE-DOCUMENTATION.md": "CC BY-NC 4.0",
        "COMMERCIAL-LICENSE.md": "Commercial use",
        "CITATION.cff": "PolyForm-Noncommercial-1.0.0",
        "README.md": "PolyForm Noncommercial 1.0.0",
        "README_EN.md": "PolyForm Noncommercial License 1.0.0",
    }
    for name, marker in required.items():
        path = ROOT / name
        if not path.is_file():
            findings.append(Finding("ERROR", f"Brak wymaganego pliku `{name}`."))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        normalized_text = " ".join(text.split())
        normalized_marker = " ".join(marker.split())
        if normalized_marker not in normalized_text:
            findings.append(
                Finding("ERROR", f"Plik `{name}` nie zawiera znacznika `{marker}`.")
            )

    license_path = ROOT / "LICENSE"
    if license_path.is_file():
        license_text = license_path.read_text(encoding="utf-8", errors="replace")
        if "Required Notice: Copyright (c) 2026 Sławomir Ramian" not in license_text:
            findings.append(Finding("ERROR", "Brak wymaganego Required Notice w LICENSE."))

    docs_license = ROOT / "LICENSE-DOCUMENTATION.md"
    if docs_license.is_file():
        text = docs_license.read_text(encoding="utf-8", errors="replace")
        if "CC BY 4.0" not in text or "Zenodo" not in text:
            findings.append(
                Finding("ERROR", "Nie opisano wyjątku CC BY 4.0 dla preprintu Zenodo.")
            )

    suspicious_names = {
        ".env",
        ".npmrc",
        ".pypirc",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        "service-account.json",
    }
    secret_patterns = [
        ("klucz prywatny", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
        ("token GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
        ("klucz OpenAI", re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b")),
        ("AWS Access Key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
        ("URL z danymi logowania", re.compile(r"https?://[^\s/:]+:[^\s/@]+@")),
    ]

    for path in files:
        rel = relative(path)
        size = path.stat().st_size
        if size >= GITHUB_LIMIT:
            findings.append(
                Finding("ERROR", f"`{rel}` ma {size / 1024 / 1024:.2f} MiB (limit GitHub: 100 MiB).")
            )
        elif size >= WARNING_LIMIT:
            findings.append(Finding("WARNING", f"`{rel}` ma {size / 1024 / 1024:.2f} MiB."))

        if path.name.lower() in suspicious_names or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            findings.append(Finding("ERROR", f"Podejrzany plik uwierzytelniający: `{rel}`."))

        text = readable_text(path)
        if text is None:
            continue
        scanned_text += 1
        for label, pattern in secret_patterns:
            if pattern.search(text):
                findings.append(Finding("ERROR", f"Możliwy {label} w `{rel}`."))
        if re.search(r"(?i)\b[A-Z]:\\(?:Users|BOHN)\\", text):
            absolute_windows_paths.append(rel)

    tracked_archives = [
        item
        for item in git_bytes("ls-files", "-z").decode("utf-8", errors="surrogateescape").split("\0")
        if item.lower().endswith((".zip", ".7z", ".rar"))
    ]
    for name in tracked_archives:
        findings.append(Finding("WARNING", f"Śledzone archiwum binarne: `{name}`."))

    emails = sorted(
        {
            item.strip()
            for item in git_bytes("log", "--format=%ae").decode("utf-8", errors="replace").splitlines()
            if item.strip()
        }
    )
    status = git_bytes("status", "--short").decode("utf-8", errors="replace").splitlines()
    errors = [finding for finding in findings if finding.level == "ERROR"]
    warnings = [finding for finding in findings if finding.level == "WARNING"]
    grade = "PASS" if not errors else "FAIL"

    lines = [
        "# Audyt publikacyjny BOHN-Original",
        "",
        f"- Wynik: **{grade}**",
        f"- Pliki objęte kontrolą: **{len(files)}**",
        f"- Pliki tekstowe przeskanowane pod kątem sekretów: **{scanned_text}**",
        f"- Błędy blokujące: **{len(errors)}**",
        f"- Ostrzeżenia do oceny: **{len(warnings)}**",
        "",
        "## Licencje",
        "",
        "- Kod: PolyForm Noncommercial 1.0.0.",
        "- Wcześniej opublikowany preprint Zenodo: CC BY 4.0.",
        "- Nowa dokumentacja i wyniki repozytorium: CC BY-NC 4.0.",
        "- Zastosowania komercyjne nowego kodu wymagają osobnej pisemnej licencji.",
        "",
        "## Błędy blokujące",
        "",
    ]
    lines.extend(f"- {finding.message}" for finding in errors)
    if not errors:
        lines.append("- Nie wykryto.")

    lines.extend(["", "## Ostrzeżenia", ""])
    lines.extend(f"- {finding.message}" for finding in warnings)
    if not warnings:
        lines.append("- Nie wykryto.")

    lines.extend(["", "## Adresy e-mail w historii Git", ""])
    lines.extend(f"- `{email}`" for email in emails)
    if not emails:
        lines.append("- Brak commitów lub brak adresów e-mail.")

    lines.extend(["", "## Historyczne ścieżki absolutne", ""])
    if absolute_windows_paths:
        lines.append(
            f"Wykryto je w **{len(set(absolute_windows_paths))}** plikach. Samo wystąpienie nie jest błędem: "
            "repozytorium zachowuje historyczne źródła i raporty. Przed publikacją należy ocenić, czy nie ujawniają "
            "danych osobowych innych niż zamierzone informacje o autorze."
        )
        lines.extend(f"- `{name}`" for name in sorted(set(absolute_windows_paths))[:50])
        if len(set(absolute_windows_paths)) > 50:
            lines.append("- … lista skrócona do pierwszych 50 plików")
    else:
        lines.append("- Nie wykryto.")

    lines.extend(["", "## Stan katalogu roboczego", "", "```text"])
    lines.extend(status or ["working tree clean"])
    lines.extend(
        [
            "```",
            "",
            "## Decyzja",
            "",
            "Raport `PASS` oznacza, że automatyczny audyt nie wykrył blokującego problemu. "
            "Nie wykonuje on publikacji i nie zastępuje końcowego przeglądu autora.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(
        f"GITHUB PUBLICATION AUDIT: {grade} | files={len(files)} | "
        f"errors={len(errors)} | warnings={len(warnings)}"
    )
    print(f"REPORT: {REPORT}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
