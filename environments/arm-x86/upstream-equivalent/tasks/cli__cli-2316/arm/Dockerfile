# syntax=docker/dockerfile:1
# Build context: this task directory. No x86 commands are executed.
FROM --platform=linux/amd64 mswebench/cli_m_cli@sha256:f7e3174769a5a168cade12f130f75dfc684ab1251ed199c9c8657d900476e7be AS upstream
FROM --platform=linux/arm64 golang:1.24.1-bookworm@sha256:fa1a01d362a7b9df68b021d59a124d28cae6d99ebd1a876e3557c4dd092f1b1d
ENV HTTP_PROXY="" http_proxy="" HTTPS_PROXY="" https_proxy=""
WORKDIR /home/
# Retain the original Git history/refs without copying x86 build products.
RUN --mount=type=bind,from=upstream,source=/home/cli/.git,target=/upstream-git,ro mkdir -p /home/cli && cp -a /upstream-git /home/cli/.git && git -C /home/cli reset --hard HEAD
# Go module sources are portable; the x86 compilation cache is excluded.
RUN --mount=type=bind,from=upstream,source=/go,target=/upstream-go,ro if [ -d /upstream-go/pkg/mod ]; then mkdir -p /go/pkg && cp -a /upstream-go/pkg/mod /go/pkg/; fi
COPY --from=upstream /home/fix.patch /home/fix.patch
COPY --from=upstream /home/test.patch /home/test.patch
COPY --from=upstream /home/check_git_changes.sh /home/check_git_changes.sh
COPY --from=upstream /home/prepare.sh /home/prepare.sh
COPY --from=upstream /home/run.sh /home/run.sh
COPY --from=upstream /home/test-run.sh /home/test-run.sh
COPY --from=upstream /home/fix-run.sh /home/fix-run.sh
RUN GOMAXPROCS=4 bash /home/prepare.sh
CMD ["bash"]
