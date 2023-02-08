#!/bin/bash

# VERSION=1.6
# http://collab.lge.com/main/x/ujHlFg

DIR=$1
ARCH=$2
OUTPUT=$3

if [ "$ARCH" == "" ]
    then
    ARCH="ARM"
fi

if [ "$DIR" == "" ]
    then
    DIR="."
fi

if [ "$OUTPUT" == "" ]
    then
    OUTPUT="binary.txt"
fi

echo -e "Binary" > $OUTPUT
find $DIR -type f -exec file "{}" \; | grep -i -e " $ARCH" -e " archive data" -e " TrueType Font" -e " PostScript" -e " OpenType font" | \
    grep -Ev "\.o:|*.txt:" | awk -F":" '{print $1}' | awk -F" " '{print $1}' | uniq | \
    while read fname; do
    binaryname=$fname
    echo -e "$binaryname" | tee -a $OUTPUT
done
