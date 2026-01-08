#!/bin/sh
#
# Run AnyLogic Experiment
#
DIR_BACKUP_XJAL=$(pwd)
SCRIPT_DIR_XJAL=$(dirname "$0")
# commented out by anylogic-export --> export AL_OMNIVERSE_CONNECTOR_PATH=$(realpath $SCRIPT_DIR_XJAL/omniverse-connector/AnyLogicOmniverseConnector)
cd "$SCRIPT_DIR_XJAL"
# commented out by anylogic-export --> chmod +x chromium/chromium-linux64/chrome

java $OPTIONS_XJAL -cp model.jar:lib/ProcessModelingLibrary.jar:lib/MarkupDescriptors.jar:lib/RackSystemModule.jar:lib/Core.jar:lib/MaterialHandlingLibrary.jar:lib/NavigationMesh.jar:lib/LevelSystem.jar:lib/jts-core-1.20.0.jar:lib/com.anylogic.engine.jar:lib/com.anylogic.engine.database.jar:lib/com.anylogic.engine.datautil.jar:lib/com.anylogic.engine.editorapi.jar:lib/com.anylogic.engine.gis.jar:lib/com.anylogic.engine.sa.jar:lib/sa/com.anylogic.engine.sa.web.jar:lib/al-spark-core-2.9.4-with-jetty-9.4.57.jar:lib/jackson-annotations-2.16.2.jar:lib/jackson-core-2.16.2.jar:lib/jackson-databind-2.16.2.jar:lib/javax.servlet-api-3.1.0.jar:lib/jetty-client-9.4.57.v20241219.jar:lib/jetty-continuation-9.4.57.v20241219.jar:lib/jetty-http-9.4.57.v20241219.jar:lib/jetty-io-9.4.57.v20241219.jar:lib/jetty-security-9.4.57.v20241219.jar:lib/jetty-server-9.4.57.v20241219.jar:lib/jetty-servlet-9.4.57.v20241219.jar:lib/jetty-servlets-9.4.57.v20241219.jar:lib/jetty-util-9.4.57.v20241219.jar:lib/jetty-util-ajax-9.4.57.v20241219.jar:lib/jetty-webapp-9.4.57.v20241219.jar:lib/jetty-xml-9.4.57.v20241219.jar:lib/sa/executor-basic-8.3.jar:lib/sa/ioutil-8.3.jar:lib/sa/util-8.3.jar:lib/slf4j-api-1.7.25.jar:lib/websocket-api-9.4.57.v20241219.jar:lib/websocket-client-9.4.57.v20241219.jar:lib/websocket-common-9.4.57.v20241219.jar:lib/websocket-server-9.4.57.v20241219.jar:lib/websocket-servlet-9.4.57.v20241219.jar:lib/querydsl-core-5.1.0.jar:lib/querydsl-sql-5.1.0.jar:lib/querydsl-sql-codegen-5.1.0.jar:lib/commons-codec-1.16.0.jar:lib/commons-collections4-4.4.jar:lib/commons-compress-1.27.1.jar:lib/commons-io-2.18.0.jar:lib/commons-lang3-3.10.jar:lib/commons-math3-3.6.1.jar:lib/commons-pool-1.5.4.jar:lib/commons-text-1.12.0.jar:lib/log4j-api-2.24.3.jar:lib/log4j-core-2.24.3.jar:lib/poi-5.4.1.jar:lib/poi-examples-5.4.1.jar:lib/poi-excelant-5.4.1.jar:lib/poi-ooxml-5.4.1.jar:lib/poi-ooxml-lite-5.4.1.jar:lib/poi-scratchpad-5.4.1.jar:lib/xmlbeans-5.3.0.jar:lib/joml-1.10.6.jar -Xmx512m distribution_center.CustomExperiment $*

EXIT_CODE=$?
cd "$DIR_BACKUP_XJAL"
