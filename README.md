# 2D-Sudoku em SAT

Formalização do problema **2D-Sudoku** (incluindo a variante com restrição
de diagonais, *Sudoku-X*) em Lógica Proposicional / CNF, com gerador de
instâncias no formato DIMACS e experimentação com o SAT solver **CaDiCaL**.

Trabalho da disciplina Lógica para Ciência da Computação (UFCA, 2026.1).

## Estrutura

```
.
├── generator/
│   ├── gerador.py        # gerador de instancias DIMACS CNF
│   └── reconstruct.py    # reconstroi o grid a partir da saida do solver
├── instances/             # instancias .cnf geradas (nao versionadas, ver .gitignore)
├── results/
│   └── resultados.csv    # tabela de resultados dos experimentos
└── run_experiments.sh     # roda a bateria completa de experimentos
```

## Uso do gerador

```bash
python3 generator/gerador.py N [--clues K] [--seed S] [--diagonal] [--force-unsat] > instancia.cnf
```

- `N`: tamanho da grade (precisa ter raiz quadrada inteira: 4, 9, 16, 25, ...)
- `--clues K`: numero de celulas pre-preenchidas (pistas), extraidas de um
  grid solucao valido gerado internamente
- `--seed S`: semente aleatoria (grid solucao e escolha das pistas)
- `--diagonal`: adiciona a restricao das duas diagonais principais (Sudoku-X)
- `--force-unsat`: insere deliberadamente duas pistas conflitantes na mesma
  linha, produzindo uma instancia UNSAT
- `--load-grid ARQUIVO`: extrai as pistas de um grid solucao fornecido em
  arquivo texto (N linhas, N inteiros), em vez de gerar um novo

Exemplo:

```bash
python3 generator/gerador.py 9 --clues 30 --seed 5 > sudoku_9.cnf
```

## Reconstrucao da solucao

```bash
cadical -q sudoku_9.cnf > sudoku_9.out
python3 generator/reconstruct.py 9 sudoku_9.out
```

## Rodando todos os experimentos

```bash
bash run_experiments.sh
```

Gera as instancias em `instances/`, executa o CaDiCaL em cada uma, mede o
tempo de execucao e grava um resumo em `results/resultados.csv`.

## Dependencias

- Python 3
- [CaDiCaL](https://github.com/arminbiere/cadical) (compilado com `./configure && make`)

## Autores

- Heitor Lacerda Santana de Sousa — github: [HeiLacerda](https://github.com/HeiLacerda)
- Iago Fernando Barbosa Nunes Conserva — github: [IagoBNC](https://github.com/IagoBNC)
