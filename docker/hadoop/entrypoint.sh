#!/bin/bash
set -e

HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}
HADOOP_CONF_DIR=${HADOOP_CONF_DIR:-$HADOOP_HOME/etc/hadoop/conf}

# Copy our config files into Hadoop's expected location
cp -f $HADOOP_CONF_DIR/*.xml $HADOOP_HOME/etc/hadoop/ 2>/dev/null || true

echo "[entrypoint] Starting as: ${HADOOP_ROLE}"
echo "[entrypoint] NameNode host: ${HADOOP_NAMENODE_HOST:-namenode}"
echo "[entrypoint] HADOOP_HOME: $HADOOP_HOME"

if [ "$HADOOP_ROLE" = "namenode" ]; then
    # Check if NameNode is already formatted
    if [ ! -d "/opt/hadoop/data/name/current" ]; then
        echo "[namenode] Formatting NameNode (first run)..."
        $HADOOP_HOME/bin/hdfs namenode -format -force -nonInteractive
        echo "[namenode] Format complete."
    else
        echo "[namenode] NameNode already formatted, skipping format."
    fi

    # Start SSH daemon (Hadoop scripts need it)
    service ssh start 2>/dev/null || true

    echo "[namenode] Starting NameNode..."
    exec $HADOOP_HOME/bin/hdfs namenode

elif [ "$HADOOP_ROLE" = "datanode" ]; then
    # Wait for NameNode to be ready
    echo "[datanode] Waiting for NameNode to become ready..."
    until nc -z ${HADOOP_NAMENODE_HOST:-namenode} 8020; do
        echo "[datanode]   ...still waiting for NameNode RPC"
        sleep 5
    done
    echo "[datanode] NameNode is ready."

    # Start SSH daemon
    service ssh start 2>/dev/null || true

    echo "[datanode] Starting DataNode..."
    exec $HADOOP_HOME/bin/hdfs datanode

else
    echo "[entrypoint] Unknown HADOOP_ROLE: $HADOOP_ROLE"
    echo "Valid roles: namenode, datanode"
    exit 1
fi
