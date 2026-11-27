from solver import *
import random

def inter(sol, a, b, ignora_dom=False):
    A = set().union(*sol[a]); B = set().union(*sol[b])
    return [d for d in (A & B) - GLOBAL_F if not (ignora_dom and d % 7 == 6)]

def balance(pessoas, sol, peso=1):
    cnt = folgas_dia(pessoas, sol)
    return peso * sum(c*c for i, c in enumerate(cnt) if i not in GLOBAL_F and i not in FECHADO)

# dias fixos de cada mês por ordinal de domingo
D3 = {20, 48}; D4 = {27, 55}

def setor_dupla(n1, f1, n2, f2):
    ps = [P(n1, 'M', dom_fixos=f1), P(n2, 'N', dom_fixos=f2)]
    def extra(sol): return 100*len(inter(sol, n1, n2)), 0
    return ps, extra

SETORES = {}

# ---------- Bar
ps, ex = setor_dupla('Rafael', D4, 'Vinicius', D3)
SETORES['Bar'] = dict(pessoas=ps, extra=ex, horario={'Rafael': '08:00–17:24 (1h int.)', 'Vinicius': '13:30–22:48 (1h int.)'}, dobra='dupla')
# ---------- Sushi
ps, ex = setor_dupla('Diogo', D3, 'Allan', D4)
SETORES['Sushi'] = dict(pessoas=ps, extra=ex, horario={'Diogo': '08:00–17:24 (1h int.)', 'Allan': '13:30–22:48 (1h int.)'}, dobra='dupla')

# ---------- Salão
sal = [P('Juliana', 'M', mulher=True), P('Elaine', mulher=True), P('Sivanilda', mulher=True, forcadas={ix(19,12,2026)}),
       P('Marcos', forcadas={ix(26,12,2026)}), P('Adriano'), P('Guilherme'), P('Jonatan'), P('Candidato')]
def ex_sal(sol):
    d = 100*(len(inter(sol, 'Elaine', 'Marcos')) + len(inter(sol, 'Guilherme', 'Adriano')))
    J = set().union(*sol['Juliana']) - GLOBAL_F
    for dia in J:
        outros = sum(1 for p in sal[1:] if any(dia in c for c in sol[p.nome]))
        d += 100*max(0, outros-2)
    return d, balance(sal, sol)
hs = {p.nome: '11:30–21:54 (2h int.)' for p in sal}; hs['Juliana'] = '08:00–17:24 (1h int.)'
SETORES['Salão'] = dict(pessoas=sal, extra=ex_sal, horario=hs, dobra=None)

# ---------- Cozinha
def fixo_edna(w):
    s = {7*w+5, 7*w+6}
    if w == 0: s.add(0)
    if w == SEMANA_FIXA: s |= GLOBAL_F & set(range(28, 35))
    return s
def fixo_moura(w):
    s = {7*w, 7*w+1}
    if w == SEMANA_FIXA: s |= GLOBAL_F & set(range(28, 35))
    return s
MIRO_SEG = {ix(7,12,2026), ix(21,12,2026), ix(4,1,2027), ix(18,1,2027)}
coz = [P('Rafael', 'M', dobra=True, dobra_proib={1, 2}, dom_fixos=D3), P('Felix', 'M', dobra=True), P('Rony', 'M'),
       P('Jair', 'M', dobra=True), P('Edna', 'M', mulher=True, fixo=fixo_edna, sem_regra_dom=True), P('Chef', 'M', dobra=True),
       P('Moura', 'M', fixo=fixo_moura, sem_regra_dom=True),
       P('Vinicius', 'N', dobra=True), P('Andressa', 'N', mulher=True, dobra=True), P('Samuel', 'N', dobra=True),
       P('Miro', 'N', dobra=True, dom_fixos=D4, forcadas=MIRO_SEG), P('Daniela', 'N', mulher=True, dobra=True),
       P('Arten', 'N', dobra=True)]
def trabalha(sol, nome, dia): return dia not in FECHADO and not any(dia in c for c in sol[nome])
def cobertura(sol, dia):
    mf = sum(1 for p in coz if p.turno == 'M' and not trabalha(sol, p.nome, dia))
    nf = sum(1 for p in coz if p.turno == 'N' and not trabalha(sol, p.nome, dia))
    em = [p for p in coz if p.turno == 'M' and p.dobra and dia % 7 not in p.dobra_proib and trabalha(sol, p.nome, dia)]
    en = [p for p in coz if p.turno == 'N' and p.dobra and trabalha(sol, p.nome, dia)]
    return mf, nf, em, en
def dias_cobertura():
    return [i for i in range(1, N) if i not in FECHADO and i not in GLOBAL_F and i % 7 != 6]
def ex_coz(sol):
    d = 100*(len(inter(sol, 'Miro', 'Rafael')) + len(inter(sol, 'Miro', 'Chef')) + len(inter(sol, 'Rafael', 'Chef')))
    m = 0
    for dia in dias_cobertura():
        mf, nf, em, en = cobertura(sol, dia)
        d += 100*(max(0, nf-len(em)) + max(0, mf-len(en)))
        m += 2*(mf+nf)**2
    cnt = folgas_dia(coz, sol)
    m += 3*sum(cnt[i]**2 for i in DOM_DEZ+DOM_JAN)
    return d, m
hc = {p.nome: ('08:00–17:24 (1h int.)' if p.turno == 'M' else '13:30–22:48 (1h int.)') for p in coz}
SETORES['Cozinha'] = dict(pessoas=coz, extra=ex_coz, horario=hc, dobra='cozinha')

# ---------- Pia
pia = [P('Ilma', 'M', mulher=True), P('Claudia', 'N', mulher=True), P('Daniel', 'N')]
def ex_pia(sol):
    d = 100*(len(inter(sol, 'Ilma', 'Daniel')) + len(inter(sol, 'Claudia', 'Daniel', True)) + len(inter(sol, 'Ilma', 'Claudia', True)))
    m = 5*(len(inter(sol, 'Claudia', 'Daniel')) - len(inter(sol, 'Claudia', 'Daniel', True)))
    d += 100*(len(inter(sol, 'Ilma', 'Claudia')) - len(inter(sol, 'Ilma', 'Claudia', True)))
    return d, m
SETORES['Pia'] = dict(pessoas=pia, extra=ex_pia, horario={'Ilma': '08:00–17:24 (1h int.)', 'Claudia': '13:30–22:48 (1h int.)', 'Daniel': '13:30–22:48 (1h int.)'}, dobra='pia')
