# syntax=docker/dockerfile:1
# Build context: this task directory. No x86 commands are executed.
FROM --platform=linux/amd64 mswebench/alibaba_m_fastjson2@sha256:03561c4a35cab50a78c18ae6f8b29d30141e119c9e0df8444a3fbc82e23eda15 AS upstream
FROM --platform=linux/arm64 ubuntu:focal-20241011@sha256:8e5c4f0285ecbb4ead070431d29b576a530d3166df73ec44affc1cd27555141b
ENV HTTP_PROXY="" http_proxy="" HTTPS_PROXY="" https_proxy=""
ENV JAVA_TOOL_OPTIONS="-Dfile.encoding=UTF-8 -Duser.timezone=Asia/Shanghai"
ENV DEBIAN_FRONTEND="noninteractive"
ENV LANG="C.UTF-8"
ENV LC_ALL="C.UTF-8"
WORKDIR /home/
COPY --from=upstream /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=upstream /usr/share/keyrings/azul.gpg /usr/share/keyrings/azul.gpg
COPY packages.txt /tmp/upstream-packages.txt
COPY install-java.sh /tmp/install-java.sh
RUN bash /tmp/install-java.sh && rm /tmp/install-java.sh /tmp/upstream-packages.txt
# Retain the original Git history/refs without copying x86 build products.
RUN --mount=type=bind,from=upstream,source=/home/fastjson2/.git,target=/upstream-git,ro mkdir -p /home/fastjson2 && cp -a /upstream-git /home/fastjson2/.git && git -C /home/fastjson2 reset --hard HEAD
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
