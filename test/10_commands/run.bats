#!/usr/bin/env bats

setup() {
  rm -rf outdir
}

teardown() {
  rm -rf outdir
}

@test "include" {
  run sashikomi.py include.tmpl params.csv outdir --fname fname
  diff outdir/ include/ > /dev/null
}
