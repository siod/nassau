#!/bin/bash

NASSAU_DIR=`dirname $0`
source "$NASSAU_DIR/../bin/activate"
#source ./../bin/activate
prequest $NASSAU_DIR/development.ini /update
