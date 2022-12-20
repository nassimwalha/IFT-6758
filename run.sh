#!/bin/bash

docker run -it -p 127.0.0.1:1234:1234 --env COMET_API_KEY=$COMET_API_KEY ift6758/serving:1.0.0
