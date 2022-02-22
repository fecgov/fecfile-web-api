#!/bin/bash

CURRENT_DIR=${PWD##*/}
OUTFILE="./docs/license_report.md"

echo "Saving report as a markdown formatted file in ${OUTFILE}"

if [ "$CURRENT_DIR" != "fecfile-web-api" ]; then
  echo "Run this script from the root directory of the fecfile-validate repository:"
fi;

mkdir -p docs

echo "The following dependencies are used by this application:"  > "$OUTFILE"
echo ""                                                          >> "$OUTFILE"
echo ""                                                          >> "$OUTFILE"
echo "| Package | Version | License |"                           >> "$OUTFILE"
echo "| --- | --- | --- |"                                       >> "$OUTFILE"

liccheck |
  grep ": " |
  sed "s/://" |
  sed "s/\[//" |
  sed "s/\]//" |
  sed "s/'//g" |
  awk '{
        gsub(/\(/, "", $2)
        gsub(/\)/, "", $2)
        printf "| %s | %s | ", $1, $2
        for (i=3; i <= NF; i++) printf "%s ", $i
        printf "|\n"
        }'  >> "$OUTFILE"

  echo "" >> "$OUTFILE"





