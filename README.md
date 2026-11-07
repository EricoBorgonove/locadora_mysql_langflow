# Locadora IA Demo

Base de dados fictícia para demonstração de MySQL + Langflow + Ollama em aulas e protótipos.

## Visão geral

Este repositório contém um banco de exemplo para uma locadora de veículos, com dados sintéticos gerados para simular operações reais de clientes, veículos, locações, pagamentos e manutenção.

O projeto foi pensado para uso didático e para testes iniciais de agentes de IA que precisam consultar dados estruturados em SQL sem expor a conta `root` do MySQL.

## Arquivos

- `locadora_veiculos_mysql.sql`: script SQL pronto com banco, tabelas, registros e views.
- `gerar_locadora.py`: script em Python para regenerar a base com dados fictícios usando `Faker`.
- `README.md`: documentação do projeto.

## Pré-requisitos

- MySQL 8+
- Python 3
- (opcional) Langflow / Ollama para testes com agentes e IA

## Importar o banco

No terminal, na pasta do projeto, execute:

```bash
mysql -u root -p < locadora_veiculos_mysql.sql
```

Depois informe a senha do MySQL quando solicitada.

Também é possível abrir o arquivo `.sql` no MySQL Workbench e executar o script inteiro.

> Atenção: o script usa `DROP DATABASE IF EXISTS locadora_ia_demo` e recria o banco. Não o execute em um ambiente que contenha dados importantes.

## Verificação rápida

```sql
USE locadora_ia_demo;
SHOW TABLES;
SELECT COUNT(*) AS total_clientes FROM clientes;
SELECT COUNT(*) AS total_veiculos FROM veiculos;
SELECT COUNT(*) AS total_locacoes FROM locacoes;
SELECT status, COUNT(*) FROM locacoes GROUP BY status;
SELECT * FROM vw_faturamento_mensal ORDER BY mes DESC LIMIT 12;
SELECT * FROM vw_veiculos_mais_locados ORDER BY total_locacoes DESC LIMIT 10;
```

## Estrutura do banco

- `filiais`: cinco unidades fictícias em Manaus.
- `clientes`: registros simulados com e-mails em domínio `.test` e documentos artificiais.
- `veiculos`: marca, modelo, categoria, diária, quilometragem, filial e status.
- `locacoes`: períodos, valores e estados (`concluida`, `ativa`, `reservada`).
- `pagamentos`: parcelas, forma e status do pagamento.
- `manutencoes`: histórico de serviços e custos.
- `vw_faturamento_mensal`, `vw_veiculos_mais_locados`, `vw_clientes_frequentes`: visões prontas para consulta.

## Gerar outro volume de dados

```bash
python -m pip install Faker
python gerar_locadora.py --clientes 1000 --veiculos 200 --semente 2026 --saida minha_locadora.sql
```

## Acesso seguro para Langflow

Para consultas somente leitura, evite usar a conta `root` do MySQL. Crie um usuário específico:

```sql
CREATE USER 'langflow_leitura'@'localhost' IDENTIFIED BY 'TROQUE_POR_SENHA_FORTE';
GRANT SELECT ON locadora_ia_demo.* TO 'langflow_leitura'@'localhost';
```

Se o Langflow estiver em contêiner, VM ou outra máquina, ajuste o host e o endereço de conexão conforme o ambiente. Não exponha o MySQL diretamente à internet. Para operações de escrita, use uma conta separada com privilégios mínimos e parâmetros validados.

## Licença

Este projeto é destinado a uso educacional e demonstrativo.
