# Hadoop 3.3.6 base image for NameNode and DataNode
FROM eclipse-temurin:11-jdk

ARG HADOOP_VERSION=3.3.6
ARG HADOOP_HOME=/opt/hadoop

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    openssh-client \
    openssh-server \
    netcat-openbsd \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Download and install Hadoop
RUN wget -q -O /tmp/hadoop.tar.gz \
    "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" \
    && tar -xzf /tmp/hadoop.tar.gz -C /opt/ \
    && mv /opt/hadoop-${HADOOP_VERSION} ${HADOOP_HOME} \
    && rm /tmp/hadoop.tar.gz

# Set environment variables
ENV HADOOP_HOME=${HADOOP_HOME}
ENV HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop/conf
ENV HADOOP_LOG_DIR=${HADOOP_HOME}/logs
ENV PATH=${PATH}:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin
ENV JAVA_HOME=/opt/java/openjdk
ENV HDFS_NAMENODE_USER=root
ENV HDFS_DATANODE_USER=root
ENV HDFS_SECONDARYNAMENODE_USER=root

# Create directories
RUN mkdir -p ${HADOOP_HOME}/data/name ${HADOOP_HOME}/data/data ${HADOOP_HOME}/logs \
    && mkdir -p ${HADOOP_CONF_DIR}

# Copy entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# SSH setup (required by Hadoop scripts)
RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa \
    && cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys \
    && chmod 0600 ~/.ssh/authorized_keys \
    && echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config

WORKDIR ${HADOOP_HOME}
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
