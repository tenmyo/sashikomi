#!/usr/bin/env bats

setup() {
  rm -rf outdir
}

teardown() {
  rm -rf outdir
}

@test "escape" {
  run sashikomi.py csv.tmpl params.csv outdir
  diff outdir/ escape/ > /dev/null
}
