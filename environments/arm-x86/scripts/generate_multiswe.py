#!/usr/bin/env python3
"""Generate matching ARM/x86 CARP task environments; retain upstream snapshots."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "alibaba__fastjson2-2775": (
        "java",
        "ubuntu:22.04",
        "./mvnw -B -pl core -Dsurefire.useFile=false -DfailIfNoTests=false test",
    ),
    "apache__dubbo-11781": (
        "java",
        "ubuntu:22.04",
        "./mvnw -B -pl dubbo-common -Dsurefire.useFile=false -DfailIfNoTests=false test",
    ),
    "fasterxml__jackson-dataformat-xml-644": (
        "java",
        "ubuntu:22.04",
        "./mvnw -B -Dsurefire.useFile=false -DfailIfNoTests=false test",
    ),
    "sharkdp__bat-3108": ("rust", "rust:1.77.2-bookworm", "cargo test --locked"),
    "nushell__nushell-10381": ("rust", "rust:1.70.0-bookworm", "cargo test --locked"),
    "BurntSushi__ripgrep-2626": ("rust", "rust:1.77.2-bookworm", "cargo test --locked"),
    "zeromicro__go-zero-964": ("go", "ubuntu:22.04", "go test -v -count=1 ./..."),
    "cli__cli-2316": ("go", "ubuntu:22.04", "go test -vet=off -v -count=1 ./..."),
    "grpc__grpc-go-3119": ("go", "ubuntu:22.04", "go test -v -count=1 ./..."),
}
LIMITATIONS = {
    "zeromicro__go-zero-964": [
        "Image/application build succeeds, but the gold manifest adds gomonkey v2.0.2, which has no ARM64 buildJmpDirective. Gold tests fail to compile in that dependency. An ARM backend backport or a documented, pinned dependency migration is required. Both options remain unimplemented.",
        "The supplied gold/test combination also calls UnaryCrashInterceptor() with a signature incompatible with the pinned source. This requires correcting the benchmark fixture upstream, not an architecture-only Dockerfile edit.",
    ],
    "grpc__grpc-go-3119": [
        "The full suite reports a Go 1.18 vet error for int-to-string conversion in internal/transport/http_util_test.go:195. A diagnostic run uses -vet=off without editing source.",
        "The full suite stalls at Test/CZSocketGetSecurityValueTLS and reaches the 10-minute Go test timeout. The architecture dependence of that stall is unverified; a focused balancer/grpclb check is recorded separately.",
    ],
    "apache__dubbo-11781": [
        "The broader dubbo-common NetUtils tests require a non-loopback interface. Use the runner's --internal-network flag: an isolated bridge supplies an interface while blocking external access.",
    ],
}
JACKSON_DEPS = """jackson-parent/e50b83d5a52b73d70dd8b178b6f88d85fd854937
jackson-bom/80aef2e97ee1514bfef4dce456070756b9e05db3
jackson-annotations/b7c3500719f7ca5a437a22b182663259b991b3b4
jackson-core/d29507fe5f3aa696e483a4de416e8195bb4af47c
jackson-databind/8956915c6409d1d5854a040d85f8bad17f23898c
jackson-modules-base/e1b1666c7e70973cd55fefec24aad1c74f6f6c00"""


def generate():
    for name, (language, base, command) in PROFILES.items():
        task = ROOT / "multi-swe-tasks" / name
        data = json.loads((task / "source.json").read_text())
        common = task / "common"
        common.mkdir(exist_ok=True)
        base += (
            "@"
            + json.loads((ROOT / "multi-swe-base-images.json").read_text())[base][
                "index_digest"
            ]
        )
        repo = data["repo"]
        commit = data["base"]["sha"]
        source = f"https://github.com/{data['org']}/{repo}.git"
        packages = "git ca-certificates curl python3 patch build-essential pkg-config libssl-dev"
        env = "ENV LANG=C.UTF-8 LC_ALL=C.UTF-8\n"
        prepare = "#!/bin/bash\nset -euxo pipefail\ncd /home/" + repo + "\n"
        notes = [
            "Both variants pin the same multiarchitecture base-image index; apt package versions are recorded after building but are not frozen by this recipe.",
            "Both variants check out the exact CARP/dataset base commit and preserve source and evaluation patches.",
            "Both variants keep gold/test patches outside the image; validation mounts them into disposable containers.",
            "Both variants provide /testbed as a symlink to the upstream /home repository path.",
        ]
        if language == "java":
            packages += " openjdk-17-jdk-headless maven unzip"
            env += 'ENV MAVEN_OPTS="-Xmx4g"\n'
            notes += [
                "JDK 17 follows CARP on both architectures. Upstream fastjson2 and Jackson used JDK 8; Dubbo already used 17.",
                "The repository Maven wrapper is used on both architectures to preserve its declared Maven version.",
                "Preparation requires test compilation; a separate baseline warm-up records its exit status without treating expected test failures as build failures.",
            ]
            if "fastjson" in name:
                env += 'ENV JAVA_TOOL_OPTIONS="-Dfile.encoding=UTF-8 -Duser.timezone=Asia/Shanghai"\n'
                notes += [
                    "Validation is scoped to the core module used by the CARP trajectory; upstream runs the full reactor with documentation profiles."
                ]
            if "dubbo" in name:
                prepare += "./mvnw -B -pl dubbo-build-tools -DskipTests install\n"
                notes += [
                    "Install dubbo-build-tools before compiling dubbo-common; the historical reactor depends on that local build extension.",
                    "Validation is scoped to dubbo-common, which contains the CARP change; this is not full upstream-reactor validation.",
                ]
            if "jackson" in name:
                (common / "jackson-dependencies.txt").write_text(JACKSON_DEPS + "\n")
                prepare += """while IFS=/ read -r dep revision; do
 git clone "https://github.com/FasterXML/$dep.git" "/opt/jackson-deps/$dep"
 git -C "/opt/jackson-deps/$dep" checkout --detach "$revision"
done < /opt/task/jackson-dependencies.txt
mvn -B -f /opt/jackson-deps/jackson-parent/pom.xml -N -DskipTests install
mvn -B -f /opt/jackson-deps/jackson-bom/pom.xml -DskipTests install
for dep in jackson-annotations jackson-core jackson-databind; do
 mvn -B -f "/opt/jackson-deps/$dep/pom.xml" -DskipTests -Djavac.src.version=8 -Djavac.target.version=8 -Dmaven.compiler.source=8 -Dmaven.compiler.target=8 install
done
mvn -B -f /opt/jackson-deps/jackson-modules-base/pom.xml -pl jakarta-xmlbind -am -DskipTests -Djavac.src.version=8 -Djavac.target.version=8 -Dmaven.compiler.source=8 -Dmaven.compiler.target=8 install
"""
                notes += [
                    "Six dependency repositories are pinned to the CARP revisions and installed locally. This retains the original 2.17.0-SNAPSHOT pom instead of upstream rewriting it to 2.17.4-SNAPSHOT."
                ]
            prepare += command.rsplit(" test", 1)[0] + " -DskipTests test-compile\n"
            prepare += (
                "set +e\n"
                + command
                + ' > /opt/task/preparation-tests.log 2>&1\nstatus=$?\nset -e\nprintf "%s\\n" "$status" > /opt/task/preparation-tests.exit\n'
            )
        elif language == "rust":
            env += "ENV CARGO_BUILD_JOBS=4\n"
            prepare += "cargo fetch --locked\ncargo build --locked\ncargo test --locked --no-run\n"
            notes += [
                "Pin the CARP compiler (bat/ripgrep 1.77.2; nushell 1.70.0) instead of upstream rust:latest, on both architectures.",
                "Use the committed Cargo.lock with --locked; do not re-resolve the historical dependency graph.",
                "Four Cargo workers bound memory use during both preparation and runtime on both architectures.",
                "Official Rust bookworm images provide native toolchains; CARP uses Ubuntu with rustup, so OS parity with CARP is not claimed.",
            ]
        else:
            packages += " golang-go"
            prepare += "go mod download\ngo build ./...\n"
            if name.startswith("cli__"):
                notes += [
                    "Go 1.18 vet rejects historical Errorf(%w) and Fprintln newline usage in unrelated CLI packages. Disable vet only for this task to run the test suite; the original failure remains in attempt-1. Source files are not edited."
                ]
                prepare += "git config --local user.useConfigOnly true\n"
            notes += [
                "Ubuntu 22.04 golang-go follows CARP Go 1.18 instead of the moving upstream golang:latest image, on both architectures.",
                "Module downloads and go build must succeed; evaluation runs independently and records failures.",
            ]
        prepare += "git diff --exit-code\n"
        (common / "entrypoint.sh").write_text(
            '#!/bin/bash\nset -e\n# Docker network=none does not always map the container hostname.\nif ! grep -qw "$(hostname)" /etc/hosts; then\n  printf "127.0.0.1 %s\\n" "$(hostname)" >> /etc/hosts\nfi\nexec "$@"\n'
        )
        notes += [
            "Runtime compatibility: map an otherwise unresolved container hostname to loopback in /etc/hosts. Docker network=none omitted this entry on the build host, preventing Dubbo Surefire from starting its test JVM."
        ]
        (common / "prepare.sh").write_text(prepare)
        (common / "run.sh").write_text(
            "#!/bin/bash\nset -euo pipefail\ncd /home/" + repo + "\n" + command + "\n"
        )
        prefetch = ""
        if language in ("rust", "go"):
            fetch = "cargo fetch --locked" if language == "rust" else "go mod download"
            prefetch = f"""RUN --mount=type=bind,source=upstream/task,target=/tmp/evaluation-patches,ro cd /home/{repo} && git apply --whitespace=nowarn /tmp/evaluation-patches/test.patch /tmp/evaluation-patches/fix.patch && {fetch} && git reset --hard {commit} && git clean -fd && git diff --exit-code
"""
            notes += [
                "Offline evaluation: prefetch dependencies from the patched manifest in a single BuildKit bind-mount step, then reset source to the base commit. The patch files and patched source do not persist in the image layer."
            ]
        for arch, platform in (("arm", "arm64"), ("x86", "amd64")):
            directory = task / arch
            directory.mkdir(exist_ok=True)
            dockerfile = f"""# syntax=docker/dockerfile:1
# Generated by scripts/generate_multiswe.py; build context is the task directory.
FROM --platform=linux/{platform} {base}
ENV DEBIAN_FRONTEND=noninteractive
{env}RUN apt-get update && apt-get install -y --no-install-recommends {packages} && rm -rf /var/lib/apt/lists/*
RUN git clone {source} /home/{repo} && git -C /home/{repo} checkout --detach {commit}
COPY common/ /opt/task/
RUN bash /opt/task/prepare.sh
{prefetch}RUN ln -s /home/{repo} /testbed
WORKDIR /testbed
ENTRYPOINT ["/bin/bash", "/opt/task/entrypoint.sh"]
CMD ["/bin/bash"]
"""
            (directory / "Dockerfile").write_text(dockerfile)
        (task / ".dockerignore").write_text(
            "*\n!common/\n!common/**\n!arm/\n!arm/Dockerfile\n!x86/\n!x86/Dockerfile\n!upstream/\n!upstream/task/\n!upstream/task/test.patch\n!upstream/task/fix.patch\n"
        )
        (task / "environment.json").write_text(
            json.dumps(
                dict(
                    instance_id=name,
                    language=language,
                    base_image=base,
                    base_commit=commit,
                    repository=source,
                    test_command=command,
                    shared_changes=notes,
                    known_limitations=LIMITATIONS.get(name, []),
                    architecture_changes=[
                        "FROM explicitly selects linux/arm64 or linux/amd64. Package managers and multiarch base images supply the native binaries."
                    ],
                    validation_scope="CARP Java module"
                    if language == "java" and "jackson" not in name
                    else "upstream test command, with pinned CARP compiler",
                ),
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    generate()
