# Locadora Dados SQL

Bases de dados fictícias de uma locadora de veículos para uso didático, testes e demonstrações com MySQL e PostgreSQL.

Todos os clientes, documentos, veículos e demais registros são sintéticos.

## Estrutura

- `mysql/locadora_veiculos_mysql.sql`: base pronta para MySQL 8+.
- `mysql/gerar_locadora_mysql.py`: gerador da base MySQL.
- `postgresql/locadora_veiculos_postgresql.sql`: base pronta para PostgreSQL 14+.
- `postgresql/gerar_locadora_postgresql.py`: gerador da base PostgreSQL.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Importar

MySQL:

```bash
mysql -u root -p < mysql/locadora_veiculos_mysql.sql
```

> O script MySQL recria o banco `locadora_ia_demo`. Não o execute onde existam dados importantes com esse nome.

PostgreSQL, depois de criar um banco vazio:

```bash
createdb locadora_ia_pg
psql -d locadora_ia_pg -f postgresql/locadora_veiculos_postgresql.sql
```

## Regenerar os dados

```bash
python mysql/gerar_locadora_mysql.py --saida mysql/locadora_veiculos_mysql.sql
python postgresql/gerar_locadora_postgresql.py --saida postgresql/locadora_veiculos_postgresql.sql
```

Os geradores aceitam `--clientes`, `--veiculos`, `--semente` e `--saida`.

## Licença

Conteúdo destinado a uso educacional e demonstrativo.
