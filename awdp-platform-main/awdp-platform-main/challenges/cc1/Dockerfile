# ============================================================
# CC1 Deserialization Challenge
# JDK < 8u71 required for AnnotationInvocationHandler gadget
# ============================================================

# Build stage
FROM ubuntu:18.04 AS builder

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    maven openjdk-8-jdk \
    && apt-get clean

ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

WORKDIR /build
COPY pom.xml .
COPY src ./src/
RUN mvn package -DskipTests

# Runtime stage
FROM ubuntu:18.04

# Install JDK 8u65 (< 8u71 for CC1 chain)
COPY jdk-8u65-linux-x64.tar.gz /tmp/jdk.tar.gz
RUN mkdir -p /opt/jdk8 && \
    tar -xzf /tmp/jdk.tar.gz -C /opt/jdk8 --strip-components=1 && \
    rm /tmp/jdk.tar.gz

ENV JAVA_HOME=/opt/jdk8
ENV PATH=$JAVA_HOME/bin:$PATH

# Install Tomcat 8 + Python 3 (for exp.py)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y wget python3 && \
    wget -q "https://archive.apache.org/dist/tomcat/tomcat-8/v8.5.61/bin/apache-tomcat-8.5.61.tar.gz" \
        -O /tmp/tomcat.tar.gz && \
    tar -xzf /tmp/tomcat.tar.gz -C /opt/ && \
    mv /opt/apache-tomcat-8.5.61 /opt/tomcat && \
    rm /tmp/tomcat.tar.gz && \
    apt-get remove -y wget && apt-get clean

ENV CATALINA_HOME=/opt/tomcat
ENV PATH=$CATALINA_HOME/bin:$PATH

# Remove Tomcat default ROOT app, deploy vulnerable WAR
RUN rm -rf /opt/tomcat/webapps/ROOT
COPY --from=builder /build/target/ROOT.war /opt/tomcat/webapps/ROOT.war

# Start script
COPY web/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8080

CMD ["/start.sh"]
