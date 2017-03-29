#!/usr/bin/env bats

setup() {
  rm -rf outdir
}

teardown() {
  rm -rf outdir
}

@test "writetype: default(append)" {
  sashikomi.py csv.tmpl params.csv outdir
  run sashikomi.py csv.tmpl params.csv outdir
  diff outdir/ append/ > /dev/null
}

@test "writetype: overwrite" {
  sashikomi.py csv.tmpl params.csv outdir
  run sashikomi.py csv.tmpl params.csv outdir --overwrite
  diff outdir/ __n/ > /dev/null
}

@test "clean" {
  sashikomi.py csv.tmpl params.csv outdir
  run sashikomi.py csv.tmpl params.csv outdir --clean
  diff outdir/ __n/ > /dev/null
}

