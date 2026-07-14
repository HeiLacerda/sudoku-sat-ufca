#!/usr/bin/env python3
"""Reconstroi o grid de Sudoku a partir da saida do solver (formato DIMACS 'v ...').

Uso: python3 reconstruct.py N arquivo_saida_solver.txt
"""
import sys
import math


def var_id(i, j, v, N):
    return (i - 1) * N * N + (j - 1) * N + v


def main():
    N = int(sys.argv[1])
    out_path = sys.argv[2]

    true_vars = set()
    sat = False
    with open(out_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("s "):
                sat = "SATISFIABLE" in line and "UNSATISFIABLE" not in line
            elif line.startswith("v "):
                for tok in line[2:].split():
                    lit = int(tok)
                    if lit == 0:
                        continue
                    if lit > 0:
                        true_vars.add(lit)

    if not sat:
        print("UNSAT (nenhuma solucao para reconstruir)")
        return

    grid = [[0] * N for _ in range(N)]
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            for v in range(1, N + 1):
                if var_id(i, j, v, N) in true_vars:
                    grid[i - 1][j - 1] = v
                    break

    width = len(str(N))
    for row in grid:
        print(" ".join(str(v).rjust(width) for v in row))


if __name__ == "__main__":
    main()
