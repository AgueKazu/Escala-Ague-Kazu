import json
from setores import *
sol = json.load(open('solucao.json'))
HOR = {n: s['horario'] for n, s in SETORES.items()}
HOR['Refeitório'] = {'Joelma': '08:00–17:24 (1h int.)'}
TURNO = {n: {p.nome: p.turno for p in s['pessoas']} for n, s in SETORES.items()}
TURNO['Refeitório'] = {'Joelma': 'M'}

def grade():
    G = {}
    for setor, pes in sol.items():
        F = {n: set().union(*[set(x) for x in ws]) for n, ws in pes.items()}
        g = {}
        for n in pes:
            g[n] = []
            for i in range(N):
                if i in FECHADO: g[n].append('FEC')
                elif i in F[n]: g[n].append('F')
                elif i % 7 == 6: g[n].append('DOM')
                else: g[n].append('T')
        nomes = list(pes)
        dobra = SETORES.get(setor, {}).get('dobra')
        for i in range(N):
            if i % 7 == 6 or i in FECHADO: continue
            if dobra == 'dupla':
                a, b = nomes
                if g[a][i] == 'F' and g[b][i] == 'T': g[b][i] = 'D'
                if g[b][i] == 'F' and g[a][i] == 'T': g[a][i] = 'D'
            elif dobra == 'pia':
                if g['Ilma'][i] == 'F' and g['Daniel'][i] == 'T': g['Daniel'][i] = 'D'
        if dobra == 'cozinha':
            cont = {p.nome: 0 for p in coz}
            ontem = set()
            for i in dias_cobertura():
                mf, nf, em, en = cobertura({k: [set(x) for x in v] for k, v in pes.items()}, i)
                hoje = set()
                for lista, k in ((em, nf), (en, mf)):
                    lista = sorted(lista, key=lambda p: (cont[p.nome] if DATAS[i].month == 12 else cont[p.nome], p.nome in ontem, p.nome))
                    for p in lista[:k]:
                        g[p.nome][i] = 'D'; cont[p.nome] += 1; hoje.add(p.nome)
                ontem = hoje
        G[setor] = g
    return G
