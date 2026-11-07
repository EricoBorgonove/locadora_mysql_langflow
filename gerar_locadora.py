#!/usr/bin/env python3
"""Gera um banco MySQL 8 ficticio e coerente de uma locadora de veiculos.
Uso: pip install Faker; python gerar_locadora.py
"""
from faker import Faker
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import random
import argparse

P = argparse.ArgumentParser()
P.add_argument('--clientes', type=int, default=500)
P.add_argument('--veiculos', type=int, default=120)
P.add_argument('--semente', type=int, default=2026)
P.add_argument('--saida', default='locadora_veiculos_mysql.sql')
args = P.parse_args()
if args.clientes < 1 or args.veiculos < 1: P.error('clientes e veiculos devem ser positivos')
rng = random.Random(args.semente)
fake = Faker('pt_BR'); Faker.seed(args.semente)
D = Decimal

def money(v): return D(str(v)).quantize(D('0.01'), rounding=ROUND_HALF_UP)
def q(s):
    if s is None: return 'NULL'
    if isinstance(s, (datetime, date)): return "'" + (s.isoformat(sep=" ") if isinstance(s, datetime) else s.isoformat()) + "'"
    if isinstance(s, (int, Decimal)): return str(s)
    return "'"+str(s).replace('\\','\\\\').replace("'","''").replace('\0','').replace('\n',' ').replace('\r',' ')+"'"
def sql_date(d): return "'"+d.strftime('%Y-%m-%d')+"'"
def insert(table, cols, rows, f, chunk=300):
    for i in range(0,len(rows),chunk):
        f.write(f"INSERT INTO `{table}` ({', '.join('`'+c+'`' for c in cols)}) VALUES\n")
        f.write(',\n'.join('('+', '.join(q(v) for v in row)+')' for row in rows[i:i+chunk]))
        f.write(';\n\n')

filiais=[
(1,'Aeroporto', 'Av. Santos Dumont, 1350','Tarumã','Manaus','AM'),
(2,'Centro', 'Av. Eduardo Ribeiro, 520','Centro','Manaus','AM'),
(3,'Adrianópolis', 'Av. Mário Ypiranga, 1100','Adrianópolis','Manaus','AM'),
(4,'Ponta Negra', 'Av. Coronel Teixeira, 4800','Ponta Negra','Manaus','AM'),
(5,'Cidade Nova', 'Av. Noel Nutels, 2500','Cidade Nova','Manaus','AM')]
modelos=[
('Fiat','Mobi','Econômico',129),('Renault','Kwid','Econômico',125),('Hyundai','HB20','Compacto',165),
('Chevrolet','Onix','Compacto',169),('Volkswagen','Polo','Compacto',179),('Fiat','Argo','Compacto',159),
('Toyota','Corolla','Sedã',279),('Honda','City','Sedã',235),('Nissan','Versa','Sedã',219),
('Jeep','Renegade','SUV',299),('Volkswagen','T-Cross','SUV',319),('Hyundai','Creta','SUV',315),
('Chevrolet','Tracker','SUV',329),('Fiat','Strada','Picape',269),('Toyota','Hilux','Picape',529),
('Chevrolet','Spin','Minivan',289)]
cores=['Branco','Prata','Preto','Cinza','Azul','Vermelho']

schema='''-- BASE FICTICIA PARA FINS DIDATICOS. NENHUM DADO PESSOAL E REAL.
-- MySQL 8.0+; exige permissao CREATE DATABASE. Evite executar em servidor com
-- banco real de mesmo nome: o comando abaixo substitui a base locadora_ia_demo.
SET NAMES utf8mb4;
DROP DATABASE IF EXISTS locadora_ia_demo;
CREATE DATABASE locadora_ia_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE locadora_ia_demo;

CREATE TABLE filiais (
 id INT PRIMARY KEY, nome VARCHAR(80) NOT NULL, endereco VARCHAR(160) NOT NULL,
 bairro VARCHAR(80) NOT NULL, cidade VARCHAR(80) NOT NULL, uf CHAR(2) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE clientes (
 id INT PRIMARY KEY AUTO_INCREMENT, nome VARCHAR(140) NOT NULL,
 email VARCHAR(160) NOT NULL UNIQUE, telefone VARCHAR(22) NOT NULL,
 cpf_ficticio CHAR(11) NOT NULL UNIQUE, data_nascimento DATE NOT NULL,
 cnh_ficticia CHAR(11) NOT NULL UNIQUE, criado_em DATE NOT NULL,
 INDEX idx_clientes_nome(nome)
) ENGINE=InnoDB;

CREATE TABLE veiculos (
 id INT PRIMARY KEY AUTO_INCREMENT, filial_id INT NOT NULL,
 marca VARCHAR(50) NOT NULL, modelo VARCHAR(60) NOT NULL,
 categoria VARCHAR(35) NOT NULL, ano SMALLINT NOT NULL, cor VARCHAR(30) NOT NULL,
 placa_ficticia CHAR(7) NOT NULL UNIQUE, quilometragem INT NOT NULL,
 diaria_base DECIMAL(10,2) NOT NULL, status ENUM('disponivel','alugado','manutencao') NOT NULL DEFAULT 'disponivel',
 FOREIGN KEY (filial_id) REFERENCES filiais(id), INDEX idx_veiculos_categoria(categoria),
 INDEX idx_veiculos_status(status)
) ENGINE=InnoDB;

CREATE TABLE locacoes (
 id INT PRIMARY KEY AUTO_INCREMENT, cliente_id INT NOT NULL, veiculo_id INT NOT NULL,
 filial_retirada_id INT NOT NULL, filial_devolucao_id INT NOT NULL,
 retirada_em DATETIME NOT NULL, devolucao_prevista_em DATETIME NOT NULL,
 devolucao_real_em DATETIME NULL, dias_cobrados INT NOT NULL,
 valor_diarias DECIMAL(12,2) NOT NULL, valor_extras DECIMAL(12,2) NOT NULL,
 desconto DECIMAL(12,2) NOT NULL DEFAULT 0, valor_total DECIMAL(12,2) NOT NULL,
 status ENUM('concluida','ativa','reservada','cancelada') NOT NULL,
 FOREIGN KEY (cliente_id) REFERENCES clientes(id), FOREIGN KEY (veiculo_id) REFERENCES veiculos(id),
 FOREIGN KEY (filial_retirada_id) REFERENCES filiais(id),
 FOREIGN KEY (filial_devolucao_id) REFERENCES filiais(id),
 INDEX idx_locacoes_periodo(retirada_em), INDEX idx_locacoes_status(status),
 INDEX idx_locacoes_veiculo_datas(veiculo_id, retirada_em, devolucao_prevista_em),
 CHECK (devolucao_prevista_em > retirada_em), CHECK (dias_cobrados > 0),
 CHECK (valor_total >= 0)
) ENGINE=InnoDB;

CREATE TABLE pagamentos (
 id INT PRIMARY KEY AUTO_INCREMENT, locacao_id INT NOT NULL,
 data_pagamento DATETIME NULL, valor DECIMAL(12,2) NOT NULL,
 forma ENUM('pix','cartao_credito','cartao_debito','boleto') NOT NULL,
 status ENUM('pago','pendente','estornado') NOT NULL,
 FOREIGN KEY (locacao_id) REFERENCES locacoes(id), INDEX idx_pagamentos_status(status),
 INDEX idx_pagamentos_data(data_pagamento)
) ENGINE=InnoDB;

CREATE TABLE manutencoes (
 id INT PRIMARY KEY AUTO_INCREMENT, veiculo_id INT NOT NULL, data_entrada DATE NOT NULL,
 data_saida DATE NULL, tipo VARCHAR(70) NOT NULL, descricao VARCHAR(180) NOT NULL,
 custo DECIMAL(12,2) NOT NULL,
 FOREIGN KEY (veiculo_id) REFERENCES veiculos(id), INDEX idx_manutencoes_data(data_entrada)
) ENGINE=InnoDB;

'''

customers=[]
used_emails=set()
for i in range(1,args.clientes+1):
    nome=fake.name()
    email=f'cliente{i:05d}@exemplo.test' # dominio reservado, nunca envio real
    birth=fake.date_of_birth(minimum_age=21, maximum_age=74)
    # CPFs / CNHs deliberadamente INVALIDOS (sequenciais), nao representam documentos reais
    cpf=f'9{i:010d}'[-11:]
    cnh=f'8{i:010d}'[-11:]
    customers.append((i,nome,email,f'(92) 9{rng.randrange(1000,10000)}-{rng.randrange(1000,10000)}',cpf,birth,cnh,
                      date(2022,1,1)+timedelta(days=rng.randrange(0,700))))

vehicles=[]
used_plates=set()
for i in range(1,args.veiculos+1):
    brand,model,cat,price=rng.choice(modelos)
    plate=f'ZZ{(i//10000)%10}{(i//1000)%10}{(i//100)%10}{(i//10)%10}{i%10}' # 7 caracteres formato intencionalmente nao valido
    vehicles.append((i,rng.randint(1,5),brand,model,cat,rng.randint(2020,2026),rng.choice(cores),plate,
                     rng.randrange(4000,105000),money(price+rng.choice([-10,0,0,10,20])),'disponivel'))

rentals=[]
# Distribuir locacoes por carro e sem sobreposicao para esse veiculo
for v in vehicles:
    vid, fid, _,_,_,_,_,_,_,daily,_=v
    cursor=datetime(2024,1,1,9,0)+timedelta(days=rng.randrange(0,50))
    while cursor < datetime(2026,10,10):
        cursor+=timedelta(days=rng.randint(3,19))
        if cursor>datetime(2026,10,20):break
        n_days=rng.randint(1,12)
        end=cursor+timedelta(days=n_days)
        if end>datetime(2026,10,31):break
        customer=rng.randint(1,args.clientes)
        extras=money(rng.choice([0,0,0,29,49,79,120,150]))
        base=money(daily*n_days)
        discount=money(base*D('0.05')) if rng.random()<0.10 else D('0.00')
        total=money(base+extras-discount)
        real=end+timedelta(hours=rng.choice([-3,-2,0,0,0,1,2]))
        rentals.append((customer,vid,fid,fid,cursor,end,real,n_days,base,extras,discount,total,'concluida'))
        cursor=end+timedelta(days=1)
# Adiciona locacoes ativas e reservas futuras, sem conflito entre carros.
# Referencia temporal fixa para reproducibilidade: 06/11/2026.
selected = rng.sample(range(1, args.veiculos+1), min(30, args.veiculos))
active_ids = set(selected[:min(15, len(selected)//2)])
reserved_ids = set(selected[len(active_ids):])
for vid in selected:
    v = vehicles[vid-1]
    fid, daily = v[1], v[9]
    active = vid in active_ids
    start = datetime(2026, 11, 3 if active else 15, 10, 0)
    duration = 7 if active else 4
    end = start + timedelta(days=duration)
    base = money(daily*duration)
    extra = D('0.00')
    rentals.append((rng.randint(1,args.clientes),vid,fid,fid,start,end,None,duration,base,extra,D('0.00'),base,'ativa' if active else 'reservada'))
vehicles = [(*v[:-1], 'alugado' if v[0] in active_ids else v[-1]) for v in vehicles]
# Embaralhar ids para deixar registros menos previsiveis
rng.shuffle(rentals)
rentals=[(i,*row) for i,row in enumerate(rentals,1)]

payments=[]
for row in rentals:
    rental_id, *_, total, status = row
    # Locacoes ativas e futuras ainda tem pagamento pendente.
    if status != 'concluida':
        payments.append((rental_id,None,total,'pix','pendente'))
        continue
    # 90% pagamento total e 10% parcelas pagas; locacoes concluidas todas quitadas
    method=rng.choice(['pix','cartao_credito','cartao_debito','boleto'])
    d=row[5]
    if rng.random()<.1:
        part=money(total/2); payments.append((rental_id,d,part,method,'pago'))
        payments.append((rental_id,d+timedelta(days=1),money(total-part),method,'pago'))
    else: payments.append((rental_id,d,total,method,'pago'))

maint=[]
for v in vehicles:
    vid=v[0]
    for _ in range(rng.randint(1,3)):
        d=date(2024,1,1)+timedelta(days=rng.randint(0,990))
        typ,descr,cost=rng.choice([
            ('Preventiva','Troca de oleo e filtros',rng.randint(250,800)),
            ('Pneus','Troca e alinhamento de pneus',rng.randint(900,2700)),
            ('Freios','Revisao do sistema de freios',rng.randint(350,1400)),
            ('Ar-condicionado','Higienizacao e revisao do ar-condicionado',rng.randint(180,700)),
            ('Corretiva','Reparo mecanico geral',rng.randint(450,3200))])
        maint.append((vid,d,d+timedelta(days=rng.randint(1,3)),typ,descr,money(cost)))

views='''-- Views de apoio para os agentes do Langflow
CREATE OR REPLACE VIEW vw_faturamento_mensal AS
SELECT DATE_FORMAT(l.retirada_em,'%Y-%m') AS mes,
       COUNT(*) AS quantidade_locacoes, SUM(l.valor_total) AS faturamento_bruto
FROM locacoes l WHERE l.status = 'concluida'
GROUP BY DATE_FORMAT(l.retirada_em,'%Y-%m');

CREATE OR REPLACE VIEW vw_veiculos_mais_locados AS
SELECT v.id AS veiculo_id, v.marca, v.modelo, v.categoria,
       COUNT(l.id) AS total_locacoes, COALESCE(SUM(l.valor_total),0) AS receita_gerada
FROM veiculos v LEFT JOIN locacoes l ON l.veiculo_id=v.id AND l.status='concluida'
GROUP BY v.id,v.marca,v.modelo,v.categoria;

CREATE OR REPLACE VIEW vw_clientes_frequentes AS
SELECT c.id AS cliente_id, c.nome, COUNT(l.id) AS total_locacoes,
       COALESCE(SUM(l.valor_total),0) AS valor_total
FROM clientes c LEFT JOIN locacoes l ON l.cliente_id=c.id AND l.status='concluida'
GROUP BY c.id,c.nome;

-- Consultas para testar:
-- SELECT COUNT(*) FROM clientes;
-- SELECT COUNT(*) FROM veiculos;
-- SELECT COUNT(*) FROM locacoes;
-- SELECT * FROM vw_faturamento_mensal ORDER BY mes DESC LIMIT 12;
-- SELECT * FROM vw_veiculos_mais_locados ORDER BY total_locacoes DESC LIMIT 10;
-- SELECT * FROM vw_clientes_frequentes ORDER BY valor_total DESC LIMIT 10;
'''

out=Path(args.saida)
with out.open('w',encoding='utf-8') as f:
    f.write(schema)
    insert('filiais',['id','nome','endereco','bairro','cidade','uf'],filiais,f)
    insert('clientes',['id','nome','email','telefone','cpf_ficticio','data_nascimento','cnh_ficticia','criado_em'],customers,f)
    insert('veiculos',['id','filial_id','marca','modelo','categoria','ano','cor','placa_ficticia','quilometragem','diaria_base','status'],vehicles,f)
    insert('locacoes',['id','cliente_id','veiculo_id','filial_retirada_id','filial_devolucao_id','retirada_em','devolucao_prevista_em','devolucao_real_em','dias_cobrados','valor_diarias','valor_extras','desconto','valor_total','status'],rentals,f)
    insert('pagamentos',['locacao_id','data_pagamento','valor','forma','status'],payments,f)
    insert('manutencoes',['veiculo_id','data_entrada','data_saida','tipo','descricao','custo'],maint,f)
    f.write(views)
print(f'Arquivo: {out.resolve()}')
print(f'Filiais: {len(filiais)} | Clientes: {len(customers)} | Veiculos: {len(vehicles)} | Locacoes: {len(rentals)} | Pagamentos: {len(payments)} | Manutencoes: {len(maint)}')
