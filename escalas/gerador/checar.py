from grade import *
G = grade()
for setor, g in G.items():
    print('==', setor)
    for n, row in g.items():
        run = mx = 0; adj = []
        for i in range(N):
            if row[i] in ('F', 'FEC'): run = 0
            else: run += 1; mx = max(mx, run)
        for i in range(N-1):
            if row[i] == 'F' and row[i+1] == 'F': adj.append(DATAS[i].strftime('%d/%m'))
        semanas = [sum(1 for i in range(7*w, 7*w+7) if row[i] == 'F') for w in range(9)]
        doms = [DATAS[i].strftime('%d/%m') for i in DOM_DEZ+DOM_JAN if row[i] == 'F']
        dz = sum(1 for i in range(1, 32) if row[i] == 'D'); jn = sum(1 for i in range(32, 63) if row[i] == 'D')
        print(f'{n:10} max_seq={mx} folgas/sem={semanas} dom_folga={doms} seguidas={adj} dobras dez={dz} jan={jn}')
    if setor == 'Cozinha':
        bad = []
        for i in dias_cobertura():
            m = sum(1 for p in coz if (p.turno == 'M' and g[p.nome][i] in 'TD') or (p.turno == 'N' and g[p.nome][i] == 'D'))
            nn = sum(1 for p in coz if (p.turno == 'N' and g[p.nome][i] in 'TD') or (p.turno == 'M' and g[p.nome][i] == 'D'))
            if m != 7 or nn != 6: bad.append((DATAS[i], m, nn))
        print('cobertura com problema:', bad)
