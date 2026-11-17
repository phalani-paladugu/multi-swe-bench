# syntax=docker/dockerfile:1
# Build context: this task directory. No x86 commands are executed.
FROM --platform=linux/amd64 mswebench/fasterxml_m_jackson-dataformat-xml@sha256:deab5905c2b9641164436d43a5a97ecf011b0bd29b4c24caa394bf1f5f9f0c7c AS upstream
FROM --platform=linux/arm64 ubuntu:jammy-20250126@sha256:ed1544e454989078f5dec1bfdabd8c5cc9c48e0705d07b678ab6ae3fb61952d2
ENV HTTP_PROXY="" http_proxy="" HTTPS_PROXY="" https_proxy=""
ENV DEBIAN_FRONTEND="noninteractive"
ENV LANG="C.UTF-8"
ENV LC_ALL="C.UTF-8"
WORKDIR /home/
COPY --from=upstream /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY packages.txt /tmp/upstream-packages.txt
COPY install-java.sh /tmp/install-java.sh
RUN bash /tmp/install-java.sh && rm /tmp/install-java.sh /tmp/upstream-packages.txt
# Retain the original Git history/refs without copying x86 build products.
RUN --mount=type=bind,from=upstream,source=/home/jackson-dataformat-xml/.git,target=/upstream-git,ro mkdir -p /home/jackson-dataformat-xml && cp -a /upstream-git /home/jackson-dataformat-xml/.git && git -C /home/jackson-dataformat-xml reset --hard HEAD
# Retain the exact upstream Maven downloads, including historical SNAPSHOTs.
RUN --mount=type=bind,from=upstream,source=/root,target=/upstream-root,ro if [ -d /upstream-root/.m2 ]; then cp -a /upstream-root/.m2 /root/; fi
COPY --from=upstream /home/fix.patch /home/fix.patch
COPY --from=upstream /home/test.patch /home/test.patch
COPY --from=upstream /home/check_git_changes.sh /home/check_git_changes.sh
COPY --from=upstream /home/prepare.sh /home/prepare.sh
COPY --from=upstream /home/run.sh /home/run.sh
COPY --from=upstream /home/test-run.sh /home/test-run.sh
COPY --from=upstream /home/fix-run.sh /home/fix-run.sh
RUN bash /home/prepare.sh
CMD ["/bin/bash"]
