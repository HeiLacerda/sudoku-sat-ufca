#!/usr/bin/env python3
"""
Gerador de instancias DIMACS CNF para o problema 2D-Sudoku.

Codificacao:
  Variavel proposicional x[i][j][v]  (i,j,v em 1..N)
    x[i][j][v] = verdadeiro  <=>  a celula (i,j) contem o valor v

  Numeracao da variavel (1-indexada, exigida pelo formato DIMACS):
    id(i,j,v) = (i-1)*N*N + (j-1)*N + v

Familias de clausulas:
  F1 - Existencia:      cada celula tem ao menos um valor
  F2 - Unicidade-celula: cada celula tem no maximo um valor
  F3 - Linha-existe:     cada valor aparece ao menos uma vez em cada linha
  F4 - Linha-unica:      cada valor aparece no maximo uma vez em cada linha
  F5 - Coluna-existe / F6 - Coluna-unica  (analogas, por coluna)
  F7 - Bloco-existe / F8 - Bloco-unica    (analogas, por bloco sqrt(N) x sqrt(N))
  F9 - Diagonal-existe / F10 - Diagonal-unica  (opcional, --diagonal)
  F11 - Pistas (clues): unidades fixando valores conhecidos

Uso:
  python3 gerador.py N [--clues K] [--seed S] [--diagonal] [--force-unsat] > instancia.cnf

  N somente e' aceito se possuir raiz quadrada inteira (4, 9, 16, 25, ...).
"""
import sys
import argparse
import random
import math


def var_id(i, j, v, N):
    """Retorna o id da variavel x[i][j][v], 1-indexado."""
    return (i - 1) * N * N + (j - 1) * N + v


def at_least_one(vars_list):
    return [list(vars_list)]


def at_most_one_pairwise(vars_list):
    clauses = []
    lst = list(vars_list)
    for a in range(len(lst)):
        for b in range(a + 1, len(lst)):
            clauses.append([-lst[a], -lst[b]])
    return clauses


def block_top_left(bi, bj, n):
    """(bi,bj) indices do bloco (1..n) -> celula superior-esquerda (1-indexada)."""
    return (bi - 1) * n + 1, (bj - 1) * n + 1


def build_clauses(N, diagonal=False):
    n = int(round(math.sqrt(N)))
    if n * n != N:
        raise ValueError("N precisa ter raiz quadrada inteira (ex.: 4, 9, 16, 25)")

    clauses = []

    # F1 / F2 - existencia e unicidade por celula
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            cell_vars = [var_id(i, j, v, N) for v in range(1, N + 1)]
            clauses += at_least_one(cell_vars)
            clauses += at_most_one_pairwise(cell_vars)

    # F3 / F4 - linhas
    for i in range(1, N + 1):
        for v in range(1, N + 1):
            row_vars = [var_id(i, j, v, N) for j in range(1, N + 1)]
            clauses += at_least_one(row_vars)
            clauses += at_most_one_pairwise(row_vars)

    # F5 / F6 - colunas
    for j in range(1, N + 1):
        for v in range(1, N + 1):
            col_vars = [var_id(i, j, v, N) for i in range(1, N + 1)]
            clauses += at_least_one(col_vars)
            clauses += at_most_one_pairwise(col_vars)

    # F7 / F8 - blocos n x n
    for bi in range(1, n + 1):
        for bj in range(1, n + 1):
            i0, j0 = block_top_left(bi, bj, n)
            for v in range(1, N + 1):
                block_vars = [
                    var_id(i0 + di, j0 + dj, v, N)
                    for di in range(n)
                    for dj in range(n)
                ]
                clauses += at_least_one(block_vars)
                clauses += at_most_one_pairwise(block_vars)

    # F9 / F10 - diagonais (opcional)
    if diagonal:
        for v in range(1, N + 1):
            main_diag = [var_id(k, k, v, N) for k in range(1, N + 1)]
            anti_diag = [var_id(k, N + 1 - k, v, N) for k in range(1, N + 1)]
            clauses += at_least_one(main_diag)
            clauses += at_most_one_pairwise(main_diag)
            clauses += at_least_one(anti_diag)
            clauses += at_most_one_pairwise(anti_diag)

    return clauses, N * N * N


def solved_grid(N, seed):
    """Gera um grid completo valido (linha i = deslocamento ciclico) e
    embaralha linhas/colunas/simbolos para nao ficar trivial."""
    n = int(round(math.sqrt(N)))
    rng = random.Random(seed)
    base = [[((i * n + i // n + j) % N) + 1 for j in range(N)] for i in range(N)]

    # embaralha bandas de linhas e linhas dentro da banda (preserva blocos)
    row_bands = list(range(n))
    rng.shuffle(row_bands)
    rows = []
    for b in row_bands:
        band_rows = list(range(n))
        rng.shuffle(band_rows)
        for r in band_rows:
            rows.append(base[b * n + r])
    grid = rows

    col_bands = list(range(n))
    rng.shuffle(col_bands)
    col_order = []
    for b in col_bands:
        band_cols = list(range(n))
        rng.shuffle(band_cols)
        for c in band_cols:
            col_order.append(b * n + c)
    grid = [[row[c] for c in col_order] for row in grid]

    symbols = list(range(1, N + 1))
    rng.shuffle(symbols)
    grid = [[symbols[val - 1] for val in row] for row in grid]

    return grid


def clue_clauses(N, clues, seed, force_unsat, diagonal, preset_grid=None):
    grid = preset_grid if preset_grid is not None else solved_grid(N, seed)
    rng = random.Random(seed + 1)
    cells = [(i, j) for i in range(1, N + 1) for j in range(1, N + 1)]
    rng.shuffle(cells)
    chosen = cells[:clues]
    unit_clauses = [[var_id(i, j, grid[i - 1][j - 1], N)] for (i, j) in chosen]

    if force_unsat and len(chosen) >= 2:
        # Forca duas pistas conflitantes na mesma linha (mesmo valor),
        # violando deliberadamente a restricao de unicidade de linha.
        (i1, j1) = chosen[0]
        (i2, j2) = chosen[1]
        i2 = i1
        while j2 == j1:
            j2 = rng.randint(1, N)
        v_conflict = grid[i1 - 1][j1 - 1]
        unit_clauses[0] = [var_id(i1, j1, v_conflict, N)]
        unit_clauses[1] = [var_id(i2, j2, v_conflict, N)]

    return unit_clauses, grid


def main():
    ap = argparse.ArgumentParser(description="Gerador DIMACS para 2D-Sudoku")
    ap.add_argument("N", type=int, help="tamanho da grade (4, 9, 16, 25, ...)")
    ap.add_argument("--clues", type=int, default=0,
                     help="numero de celulas pre-preenchidas (pistas)")
    ap.add_argument("--seed", type=int, default=42, help="semente aleatoria")
    ap.add_argument("--diagonal", action="store_true",
                     help="adiciona restricao das duas diagonais principais")
    ap.add_argument("--force-unsat", action="store_true",
                     help="insere pistas conflitantes para gerar instancia UNSAT")
    ap.add_argument("--load-grid", type=str, default=None,
                     help="arquivo texto com grid solucao valido (N linhas, N inteiros) "
                          "para extrair pistas consistentes (ex.: grids que ja' respeitam "
                          "a restricao diagonal)")
    args = ap.parse_args()

    N = args.N
    clauses, n_vars_expected = build_clauses(N, diagonal=args.diagonal)

    grid = None
    preset_grid = None
    if args.load_grid:
        with open(args.load_grid) as f:
            preset_grid = [[int(x) for x in line.split()] for line in f if line.strip()]

    if args.clues > 0 or args.force_unsat:
        unit_clauses, grid = clue_clauses(
            N, max(args.clues, 2 if args.force_unsat else 0),
            args.seed, args.force_unsat, args.diagonal, preset_grid=preset_grid
        )
        clauses += unit_clauses

    n_vars = N * N * N
    n_clauses = len(clauses)

    # Verificacao de sanidade: recontar variaveis realmente usadas
    used_vars = set()
    for c in clauses:
        for lit in c:
            used_vars.add(abs(lit))
    assert max(used_vars) <= n_vars, "variavel fora do intervalo declarado"
    assert n_vars == n_vars_expected, "contagem de variaveis nao bate com N^3"

    out = sys.stdout
    out.write(f"c Instancia 2D-Sudoku N={N} diagonal={args.diagonal} "
              f"clues={args.clues} seed={args.seed} force_unsat={args.force_unsat}\n")
    out.write(f"c Variavel x(i,j,v) = (i-1)*N*N + (j-1)*N + v, com i,j,v em 1..{N}\n")
    if grid is not None and not args.force_unsat:
        out.write("c Grid solucao usada para gerar as pistas (para conferencia):\n")
        for row in grid:
            out.write("c " + " ".join(str(v) for v in row) + "\n")
    out.write(f"p cnf {n_vars} {n_clauses}\n")
    for c in clauses:
        out.write(" ".join(str(lit) for lit in c) + " 0\n")

    sys.stderr.write(f"[gerador] N={N} vars={n_vars} clauses={n_clauses}\n")


if __name__ == "__main__":
    main()
