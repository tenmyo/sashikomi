#!/usr/bin/env bats

setup() {
  rm -rf outdir
}

teardown() {
  rm -rf outdir
}

@test "fname: default" {
  run sashikomi.py csv.tmpl params.csv outdir
  diff outdir/ __n/ > /dev/null
}

@test "fname: fname" {
  run sashikomi.py csv.tmpl params.csv outdir --fname fname
  diff outdir/ fname/ > /dev/null
}
