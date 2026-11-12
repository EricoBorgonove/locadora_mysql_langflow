#!/usr/bin/env python3
"""Versão PostgreSQL da base fictícia da locadora (semente 2026).
Os dados são fictícios; para correspondência exata com o SQL original é preciso converter
seu arquivo, pois a versão da biblioteca Faker pode alterar a sequência de nomes/datas.
"""
from faker import Faker
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import random, argparse

ap=argparse.ArgumentParser()
ap.add_argument('--clientes',type=int,default=500)
ap.add_argument('--veiculos',type=int,default=120)
ap.add_argument('--semente',type=int,default=2026)
ap.add_argument('--saida',default='locadora_veiculos_postgresql.sql')
a=ap.parse_args()
if a.clientes<1 or a.veiculos<1: ap.error('clientes e veiculos devem ser positivos')
rng=random.Random(a.semente)
fake=Faker('pt_BR');Faker.seed(a.semente)
D=Decimal
def money(x):return D(str(x)).quantize(D('0.01'),rounding=ROUND_HALF_UP)
def q(x):
    if x is None:return 'NULL'
    if isinstance(x,datetime):return "'"+x.isoformat(sep=' ')+"'"
    if isinstance(x,date):return "'"+x.isoformat()+"'"
    if isinstance(x,(int,Decimal)):return str(x)
    # String literal escaping compatible with standard_conforming_strings=on
    return "'"+str(x).replace("'","''").replace('\x00','').replace('\n',' ').replace('\r',' ')+"'"
def emit_insert(f,table,cols,rows,chunk=300):
    for k in range(0,len(rows),chunk):
        f.write(f"INSERT INTO {table} ({', '.join(cols)}) VALUES\n")
        f.write(',\n'.join('('+', '.join(q(x) for x in row)+')' for row in rows[k:k+chunk]))
        f.write(';\n\n')

filiais=[(1,'Aeroporto','Av. Santos Dumont, 1350','Tarumã','Manaus','AM'),(2,'Centro','Av. Eduardo Ribeiro, 520','Centro','Manaus','AM'),(3,'Adrianópolis','Av. Mário Ypiranga, 1100','Adrianópolis','Manaus','AM'),(4,'Ponta Negra','Av. Coronel Teixeira, 4800','Ponta Negra','Manaus','AM'),(5,'Cidade Nova','Av. Noel Nutels, 2500','Cidade Nova','Manaus','AM')]
modelos=[('Fiat','Mobi','Econômico',129),('Renault','Kwid','Econômico',125),('Hyundai','HB20','Compacto',165),('Chevrolet','Onix','Compacto',169),('Volkswagen','Polo','Compacto',179),('Fiat','Argo','Compacto',159),('Toyota','Corolla','Sedã',279),('Honda','City','Sedã',235),('Nissan','Versa','Sedã',219),('Jeep','Renegade','SUV',299),('Volkswagen','T-Cross','SUV',319),('Hyundai','Creta','SUV',315),('Chevrolet','Tracker','SUV',329),('Fiat','Strada','Picape',269),('Toyota','Hilux','Picape',529),('Chevrolet','Spin','Minivan',289)]
cores=['Branco','Prata','Preto','Cinza','Azul','Vermelho']
customers=[]
for i in range(1,a.clientes+1):
    nome=fake.name(); email=f'cliente{i:05d}@exemplo.test';birth=fake.date_of_birth(minimum_age=21,maximum_age=74)
    cpf=f'9{i:010d}'[-11:];cnh=f'8{i:010d}'[-11:]
    customers.append((i,nome,email,f'(92) 9{rng.randrange(1000,10000)}-{rng.randrange(1000,10000)}',cpf,birth,cnh,date(2022,1,1)+timedelta(days=rng.randrange(0,700))))
vehicles=[]
for i in range(1,a.veiculos+1):
    brand,model,cat,price=rng.choice(modelos)
    plate=f'ZZ{(i//10000)%10}{(i//1000)%10}{(i//100)%10}{(i//10)%10}{i%10}'
    vehicles.append((i,rng.randint(1,5),brand,model,cat,rng.randint(2020,2026),rng.choice(cores),plate,rng.randrange(4000,105000),money(price+rng.choice([-10,0,0,10,20])),'disponivel'))
rentals=[]
for v in vehicles:
    vid,fid,_,_,_,_,_,_,_,daily,_=v
    cursor=datetime(2024,1,1,9,0)+timedelta(days=rng.randrange(0,50))
    while cursor<datetime(2026,10,10):
        cursor+=timedelta(days=rng.randint(3,19))
        if cursor>datetime(2026,10,20):break
        n_days=rng.randint(1,12);end=cursor+timedelta(days=n_days)
        if end>datetime(2026,10,31):break
        customer=rng.randint(1,a.clientes)
        extras=money(rng.choice([0,0,0,29,49,79,120,150]));base=money(daily*n_days)
        discount=money(base*D('0.05')) if rng.random()<.10 else D('0.00')
        total=money(base+extras-discount)
        real=end+timedelta(hours=rng.choice([-3,-2,0,0,0,1,2]))
        rentals.append((customer,vid,fid,fid,cursor,end,real,n_days,base,extras,discount,total,'concluida'))
        cursor=end+timedelta(days=1)
selected=rng.sample(range(1,a.veiculos+1),min(30,a.veiculos))
active_ids=set(selected[:min(15,len(selected)//2)])
for vid in selected:
    v=vehicles[vid-1];fid,daily=v[1],v[9];active=vid in active_ids
    start=datetime(2026,11,3 if active else 15,10,0);duration=7 if active else 4
    end=start+timedelta(days=duration);base=money(daily*duration)
    rentals.append((rng.randint(1,a.clientes),vid,fid,fid,start,end,None,duration,base,D('0.00'),D('0.00'),base,'ativa' if active else 'reservada'))
vehicles=[(*v[:-1],'alugado' if v[0] in active_ids else v[-1]) for v in vehicles]
rng.shuffle(rentals);rentals=[(i,*row) for i,row in enumerate(rentals,1)]
payments=[]
for row in rentals:
    rental_id,*_,total,status=row
    if status!='concluida':
        payments.append((rental_id,None,total,'pix','pendente'));continue
    method=rng.choice(['pix','cartao_credito','cartao_debito','boleto']);d=row[5]
    if rng.random()<.1:
        part=money(total/2)
        payments.append((rental_id,d,part,method,'pago'))
        payments.append((rental_id,d+timedelta(days=1),money(total-part),method,'pago'))
    else:payments.append((rental_id,d,total,method,'pago'))
maint=[]
for v in vehicles:
    vid=v[0]
    for _ in range(rng.randint(1,3)):
        d=date(2024,1,1)+timedelta(days=rng.randint(0,990))
        typ,descr,cost=rng.choice([('Preventiva','Troca de oleo e filtros',rng.randint(250,800)),('Pneus','Troca e alinhamento de pneus',rng.randint(900,2700)),('Freios','Revisao do sistema de freios',rng.randint(350,1400)),('Ar-condicionado','Higienizacao e revisao do ar-condicionado',rng.randint(180,700)),('Corretiva','Reparo mecanico geral',rng.randint(450,3200))])
        maint.append((vid,d,d+timedelta(days=rng.randint(1,3)),typ,descr,money(cost)))

schema="""-- PostgreSQL 14+ | Locadora Dados SQL | Dados totalmente fictícios
-- EXECUTAR EM BANCO NOVO E VAZIO locadora_ia_pg (crie previamente: createdb locadora_ia_pg)
-- NÃO apaga outros bancos. A transação reverte alterações se ocorrer erro.
BEGIN;
SET client_encoding = 'UTF8';
CREATE TABLE filiais (
 id INTEGER PRIMARY KEY, nome VARCHAR(80) NOT NULL, endereco VARCHAR(160) NOT NULL,
 bairro VARCHAR(80) NOT NULL, cidade VARCHAR(80) NOT NULL, uf CHAR(2) NOT NULL
);
CREATE TABLE clientes (
 id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY, nome VARCHAR(140) NOT NULL,
 email VARCHAR(160) NOT NULL UNIQUE, telefone VARCHAR(22) NOT NULL,
 cpf_ficticio CHAR(11) NOT NULL UNIQUE, data_nascimento DATE NOT NULL,
 cnh_ficticia CHAR(11) NOT NULL UNIQUE, criado_em DATE NOT NULL
);
CREATE TABLE veiculos (
 id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY, filial_id INTEGER NOT NULL REFERENCES filiais(id),
 marca VARCHAR(50) NOT NULL, modelo VARCHAR(60) NOT NULL, categoria VARCHAR(35) NOT NULL,
 ano SMALLINT NOT NULL, cor VARCHAR(30) NOT NULL, placa_ficticia CHAR(7) NOT NULL UNIQUE,
 quilometragem INTEGER NOT NULL, diaria_base NUMERIC(10,2) NOT NULL,
 status VARCHAR(16) NOT NULL DEFAULT 'disponivel' CHECK (status IN ('disponivel','alugado','manutencao'))
);
CREATE TABLE locacoes (
 id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
 cliente_id INTEGER NOT NULL REFERENCES clientes(id), veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
 filial_retirada_id INTEGER NOT NULL REFERENCES filiais(id),
 filial_devolucao_id INTEGER NOT NULL REFERENCES filiais(id),
 retirada_em TIMESTAMP NOT NULL, devolucao_prevista_em TIMESTAMP NOT NULL,
 devolucao_real_em TIMESTAMP NULL, dias_cobrados INTEGER NOT NULL,
 valor_diarias NUMERIC(12,2) NOT NULL, valor_extras NUMERIC(12,2) NOT NULL,
 desconto NUMERIC(12,2) NOT NULL DEFAULT 0, valor_total NUMERIC(12,2) NOT NULL,
 status VARCHAR(16) NOT NULL CHECK (status IN ('concluida','ativa','reservada','cancelada')),
 CHECK (devolucao_prevista_em > retirada_em), CHECK (dias_cobrados > 0), CHECK (valor_total >= 0)
);
CREATE TABLE pagamentos (
 id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
 locacao_id INTEGER NOT NULL REFERENCES locacoes(id), data_pagamento TIMESTAMP NULL,
 valor NUMERIC(12,2) NOT NULL,
 forma VARCHAR(24) NOT NULL CHECK (forma IN ('pix','cartao_credito','cartao_debito','boleto')),
 status VARCHAR(16) NOT NULL CHECK (status IN ('pago','pendente','estornado'))
);
CREATE TABLE manutencoes (
 id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
 veiculo_id INTEGER NOT NULL REFERENCES veiculos(id), data_entrada DATE NOT NULL,
 data_saida DATE NULL, tipo VARCHAR(70) NOT NULL, descricao VARCHAR(180) NOT NULL,
 custo NUMERIC(12,2) NOT NULL
);
CREATE INDEX idx_clientes_nome ON clientes(nome);
CREATE INDEX idx_veiculos_categoria ON veiculos(categoria);
CREATE INDEX idx_veiculos_status ON veiculos(status);
CREATE INDEX idx_locacoes_periodo ON locacoes(retirada_em);
CREATE INDEX idx_locacoes_status ON locacoes(status);
CREATE INDEX idx_locacoes_veiculo_datas ON locacoes(veiculo_id,retirada_em,devolucao_prevista_em);
CREATE INDEX idx_pagamentos_status ON pagamentos(status);
CREATE INDEX idx_pagamentos_data ON pagamentos(data_pagamento);
CREATE INDEX idx_manutencoes_data ON manutencoes(data_entrada);
\n"""
views="""
-- Ajusta sequências após a carga de IDs explícitos.
SELECT setval(pg_get_serial_sequence('clientes','id'),(SELECT MAX(id) FROM clientes),true);
SELECT setval(pg_get_serial_sequence('veiculos','id'),(SELECT MAX(id) FROM veiculos),true);
SELECT setval(pg_get_serial_sequence('locacoes','id'),(SELECT MAX(id) FROM locacoes),true);
SELECT setval(pg_get_serial_sequence('pagamentos','id'),(SELECT MAX(id) FROM pagamentos),true);
SELECT setval(pg_get_serial_sequence('manutencoes','id'),(SELECT MAX(id) FROM manutencoes),true);

CREATE VIEW vw_faturamento_mensal AS
 SELECT to_char(l.retirada_em,'YYYY-MM') AS mes,
 COUNT(*) AS quantidade_locacoes, SUM(l.valor_total) AS faturamento_bruto
 FROM locacoes l WHERE l.status='concluida'
 GROUP BY to_char(l.retirada_em,'YYYY-MM');

CREATE VIEW vw_veiculos_mais_locados AS
 SELECT v.id AS veiculo_id,v.marca,v.modelo,v.categoria,
 COUNT(l.id) AS total_locacoes,COALESCE(SUM(l.valor_total),0) AS receita_gerada
 FROM veiculos v LEFT JOIN locacoes l ON l.veiculo_id=v.id AND l.status='concluida'
 GROUP BY v.id,v.marca,v.modelo,v.categoria;

CREATE VIEW vw_clientes_frequentes AS
 SELECT c.id AS cliente_id,c.nome,COUNT(l.id) AS total_locacoes,
 COALESCE(SUM(l.valor_total),0) AS valor_total
 FROM clientes c LEFT JOIN locacoes l ON l.cliente_id=c.id AND l.status='concluida'
 GROUP BY c.id,c.nome;
COMMIT;

-- Consultas de verificação (opcionais):
-- SELECT COUNT(*) FROM clientes;
-- SELECT COUNT(*) FROM veiculos;
-- SELECT COUNT(*) FROM locacoes;
-- SELECT * FROM vw_faturamento_mensal ORDER BY mes DESC LIMIT 12;
"""
out=Path(a.saida)
with out.open('w',encoding='utf-8') as f:
    f.write(schema)
    emit_insert(f,'filiais',['id','nome','endereco','bairro','cidade','uf'],filiais)
    emit_insert(f,'clientes',['id','nome','email','telefone','cpf_ficticio','data_nascimento','cnh_ficticia','criado_em'],customers)
    emit_insert(f,'veiculos',['id','filial_id','marca','modelo','categoria','ano','cor','placa_ficticia','quilometragem','diaria_base','status'],vehicles)
    emit_insert(f,'locacoes',['id','cliente_id','veiculo_id','filial_retirada_id','filial_devolucao_id','retirada_em','devolucao_prevista_em','devolucao_real_em','dias_cobrados','valor_diarias','valor_extras','desconto','valor_total','status'],rentals)
    emit_insert(f,'pagamentos',['locacao_id','data_pagamento','valor','forma','status'],payments)
    emit_insert(f,'manutencoes',['veiculo_id','data_entrada','data_saida','tipo','descricao','custo'],maint)
    f.write(views)
print('Arquivo:',out.resolve())
print(f'Filiais {len(filiais)} | Clientes {len(customers)} | Veículos {len(vehicles)} | Locações {len(rentals)} | Pagamentos {len(payments)} | Manutenções {len(maint)}')
