import json, sys
from setores import *
res = {}
for nome, s in SETORES.items():
    print(nome, file=sys.stderr)
    c, d, sol = resolver(s['pessoas'], s['extra'], iters=int(sys.argv[1]) if len(sys.argv) > 1 else 40000, seed=7)
    print(nome, 'custo', c, 'duro', d, file=sys.stderr)
    res[nome] = {k: [sorted(x) for x in v] for k, v in sol.items()}
# Refeitório depende do Rafael da cozinha
raf = set().union(*[set(x) for x in res['Cozinha']['Rafael']])
jo = [P('Joelma', 'M', mulher=True, evita_sab=True)]
def ex_jo(sol):
    J = set().union(*sol['Joelma'])
    return 100*len((J & raf) - GLOBAL_F), 0
c, d, sol = resolver(jo, ex_jo, iters=20000, seed=3)
print('Refeitório custo', c, 'duro', d, file=sys.stderr)
res['Refeitório'] = {k: [sorted(x) for x in v] for k, v in sol.items()}
json.dump(res, open('solucao.json', 'w'))
