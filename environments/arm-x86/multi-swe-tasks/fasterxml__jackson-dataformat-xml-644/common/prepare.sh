#!/bin/bash
set -euxo pipefail
cd /home/jackson-dataformat-xml
while IFS=/ read -r dep revision; do
 git clone "https://github.com/FasterXML/$dep.git" "/opt/jackson-deps/$dep"
 git -C "/opt/jackson-deps/$dep" checkout --detach "$revision"
done < /opt/task/jackson-dependencies.txt
mvn -B -f /opt/jackson-deps/jackson-parent/pom.xml -N -DskipTests install
mvn -B -f /opt/jackson-deps/jackson-bom/pom.xml -DskipTests install
for dep in jackson-annotations jackson-core jackson-databind; do
 mvn -B -f "/opt/jackson-deps/$dep/pom.xml" -DskipTests -Djavac.src.version=8 -Djavac.target.version=8 -Dmaven.compiler.source=8 -Dmaven.compiler.target=8 install
done
mvn -B -f /opt/jackson-deps/jackson-modules-base/pom.xml -pl jakarta-xmlbind -am -DskipTests -Djavac.src.version=8 -Djavac.target.version=8 -Dmaven.compiler.source=8 -Dmaven.compiler.target=8 install
./mvnw -B -Dsurefire.useFile=false -DfailIfNoTests=false -DskipTests test-compile
set +e
./mvnw -B -Dsurefire.useFile=false -DfailIfNoTests=false test > /opt/task/preparation-tests.log 2>&1
status=$?
set -e
printf "%s\n" "$status" > /opt/task/preparation-tests.exit
git diff --exit-code
