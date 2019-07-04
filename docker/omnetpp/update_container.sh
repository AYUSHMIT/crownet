#!/bin/bash
RANDOM=$(date +%s)
docker build -t sam-dev.cs.hm.edu:5023/rover/rover-main/omnetpp:latest --build-arg NOCACHE_PULL=$RANDOM .

if [ $? -eq 0 ]; then
   docker login sam-dev.cs.hm.edu:5023
   docker push sam-dev.cs.hm.edu:5023/rover/rover-main/omnetpp:latest
else 
   echo "Container build did not succeed - no upload to registry."
fi
