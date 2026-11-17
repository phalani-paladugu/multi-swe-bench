#!/usr/bin/env python3
"""Generate ARM adaptations of immutable published upstream task images."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate():
    for item in json.loads((ROOT / "images.json").read_text()):
        task = ROOT / "tasks" / item["instance_id"]
        (task / "arm").mkdir(parents=True, exist_ok=True)
        (task / "x86").mkdir(exist_ok=True)
        official = item["upstream_image"]
        base = item["base_image"]
        repo = item["repository_name"]
        lines = [
            "# syntax=docker/dockerfile:1",
            "# Build context: this task directory. No x86 commands are executed.",
            f"FROM --platform=linux/amd64 {official} AS upstream",
            f"FROM --platform=linux/arm64 {base}",
            'ENV HTTP_PROXY="" http_proxy="" HTTPS_PROXY="" https_proxy=""',
        ]
        for entry in item.get("extra_environment", []):
            key, value = entry.split("=", 1)
            lines.append("ENV " + key + "=" + json.dumps(value))
        lines.append("WORKDIR /home/")
        if item.get("java_install"):
            lines += [
                "COPY --from=upstream /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt"
            ]
            if item["instance_id"].startswith("alibaba"):
                lines += [
                    "COPY --from=upstream /usr/share/keyrings/azul.gpg /usr/share/keyrings/azul.gpg"
                ]
            lines += [
                "COPY packages.txt /tmp/upstream-packages.txt",
                "COPY install-java.sh /tmp/install-java.sh",
                "RUN bash /tmp/install-java.sh && rm /tmp/install-java.sh /tmp/upstream-packages.txt",
            ]
        lines += [
            "# Retain the original Git history/refs without copying x86 build products.",
            f"RUN --mount=type=bind,from=upstream,source=/home/{repo}/.git,target=/upstream-git,ro mkdir -p /home/{repo} && cp -a /upstream-git /home/{repo}/.git && git -C /home/{repo} reset --hard HEAD",
        ]
        language = item["language"]
        if language == "rust":
            lines += [
                "# Reuse source downloads; compiled x86 targets and tool binaries are excluded.",
                'RUN --mount=type=bind,from=upstream,source=/usr/local/cargo,target=/upstream-cargo,ro for directory in registry git; do if [ -d "/upstream-cargo/$directory" ]; then cp -a "/upstream-cargo/$directory" /usr/local/cargo/; fi; done',
            ]
        elif language == "go":
            lines += [
                "# Go module sources are portable; the x86 compilation cache is excluded.",
                "RUN --mount=type=bind,from=upstream,source=/go,target=/upstream-go,ro if [ -d /upstream-go/pkg/mod ]; then mkdir -p /go/pkg && cp -a /upstream-go/pkg/mod /go/pkg/; fi",
            ]
        else:
            lines += [
                "# Retain the exact upstream Maven downloads, including historical SNAPSHOTs.",
                "RUN --mount=type=bind,from=upstream,source=/root,target=/upstream-root,ro if [ -d /upstream-root/.m2 ]; then cp -a /upstream-root/.m2 /root/; fi",
            ]
        for name in [
            "fix.patch",
            "test.patch",
            "check_git_changes.sh",
            "prepare.sh",
            "run.sh",
            "test-run.sh",
            "fix-run.sh",
        ]:
            lines.append(f"COPY --from=upstream /home/{name} /home/{name}")
        # These variables bound build resource use only; they are not image ENV.
        prefix = {"rust": "CARGO_BUILD_JOBS=4 ", "go": "GOMAXPROCS=4 ", "java": ""}[
            language
        ]
        lines += [
            f"RUN {prefix}bash /home/prepare.sh",
            "CMD " + json.dumps(item["command"]),
            "",
        ]
        (task / "arm/Dockerfile").write_text("\n".join(lines))
        (task / "x86/Dockerfile").write_text(
            "# The immutable official x86 image is the baseline; no CARP adaptations.\nFROM --platform=linux/amd64 "
            + official
            + "\n"
        )
        (task / ".dockerignore").write_text(
            "*\n!arm/\n!arm/Dockerfile\n!x86/\n!x86/Dockerfile\n!packages.txt\n!install-java.sh\n"
        )
        (task / "upstream-reference.json").write_text(json.dumps(item, indent=2) + "\n")


if __name__ == "__main__":
    generate()
