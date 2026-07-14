#!/usr/bin/env bash
# Executa o gerador + o SAT solver CaDiCaL para uma bateria de instancias
# de tamanhos e configuracoes crescentes, registrando os resultados.
set -e

GEN=generator/gerador.py
SOLVER=/home/claude/cadical/build/cadical
OUT=results
INST=instances
CSV=$OUT/resultados.csv

mkdir -p "$OUT" "$INST"
echo "instancia,N,diagonal,clues,vars,clauses,resultado,tempo_s" > "$CSV"

# Bootstrap: gera um grid completo 9x9 que respeita a restricao diagonal
# (Sudoku-X), resolvendo a instancia "em branco" com o proprio SAT solver.
# Este grid e usado para extrair pistas consistentes no caso sudokux_9_c30_sat.
if [ ! -f "$INST/valid_diagonal_grid.txt" ]; then
  python3 "$GEN" 9 --diagonal > /tmp/blank_diag.cnf
  "$SOLVER" -q /tmp/blank_diag.cnf > /tmp/blank_diag.out 2>&1 || true
  python3 generator/reconstruct.py 9 /tmp/blank_diag.out > "$INST/valid_diagonal_grid.txt"
fi

run_case () {
  name=$1; N=$2; clues=$3; seed=$4; diag=$5; force_unsat=$6; grid_file=$7

  extra=""
  [ "$diag" = "1" ] && extra="$extra --diagonal"
  [ "$force_unsat" = "1" ] && extra="$extra --force-unsat"
  [ -n "$grid_file" ] && extra="$extra --load-grid $grid_file"

  cnf="$INST/${name}.cnf"
  out="$INST/${name}.out"

  python3 "$GEN" "$N" --clues "$clues" --seed "$seed" $extra > "$cnf" 2> "$INST/${name}.log"

  nvars=$(grep -m1 "^p cnf" "$cnf" | awk '{print $3}')
  nclauses=$(grep -m1 "^p cnf" "$cnf" | awk '{print $4}')

  start=$(date +%s.%N)
  "$SOLVER" -q "$cnf" > "$out" 2>&1 || true
  end=$(date +%s.%N)
  elapsed=$(echo "$end - $start" | bc)

  resultado=$(grep -m1 "^s " "$out" | awk '{print $2}')

  echo "$name,$N,$diag,$clues,$nvars,$nclauses,$resultado,$elapsed" >> "$CSV"
  echo "[$name] N=$N clues=$clues diag=$diag -> $resultado em ${elapsed}s ($nvars vars, $nclauses clausulas)"
}

run_case "sudoku_4_blank"      4  0   1 0 0 ""
run_case "sudoku_4_c6"         4  6   2 0 0 ""
run_case "sudoku_9_blank"      9  0   3 0 0 ""
run_case "sudoku_9_c17"        9  17  4 0 0 ""
run_case "sudoku_9_c30"        9  30  5 0 0 ""
run_case "sudoku_9_unsat"      9  30  6 0 1 ""
run_case "sudokux_9_c30_unsat" 9 30  5 1 0 ""
run_case "sudokux_9_c30_sat"   9 30  5 1 0 "instances/valid_diagonal_grid.txt"
run_case "sudoku_16_c50"       16 50  7 0 0 ""
run_case "sudoku_25_c100"      25 100 8 0 0 ""

echo
echo "Resumo (CSV): $CSV"
cat "$CSV"
