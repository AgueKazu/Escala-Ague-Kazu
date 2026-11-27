import datetime as dt, random, itertools, math, json, sys

D0 = dt.date(2026, 11, 30)
N = 63
DATAS = [D0 + dt.timedelta(i) for i in range(N)]
def ix(d, m, a): return (dt.date(a, m, d) - D0).days
FECHADO = {ix(25,12,2026), ix(1,1,2027)}
GLOBAL_F = {0, ix(31,12,2026), ix(2,1,2027)}
DOM_DEZ = [6, 13, 20, 27]
DOM_JAN = [34, 41, 48, 55, 62]
SEMANA_FIXA = 4  # 28/12 a 03/01
def mes(i): return DATAS[i].month

class P:
    def __init__(s, nome, turno='M', mulher=False, dobra=False, dobra_proib=(), dom_fixos=None,
                 forcadas=(), fixo=None, sem_regra_dom=False, evita_sab=False):
        s.nome, s.turno, s.mulher, s.dobra = nome, turno, mulher, dobra
        s.dobra_proib = set(dobra_proib)   # dias da semana (0=seg) sem dobra
        s.dom_fixos = set(dom_fixos) if dom_fixos is not None else None
        s.forcadas = set(forcadas) | {0}
        s.fixo = fixo                       # função semana -> conjunto fixo
        s.sem_regra_dom = sem_regra_dom
        s.evita_sab = evita_sab

def candidatos(p, w):
    dias = list(range(7*w, 7*w+7))
    if p.fixo: return [frozenset(p.fixo(w))]
    if w == SEMANA_FIXA: return [frozenset(GLOBAL_F & set(dias))]
    forc = {d for d in dias if d in p.forcadas}
    if p.dom_fixos is not None: forc |= {d for d in dias if d in p.dom_fixos}
    k = 2 - len(forc)
    livres = [d for d in dias if d not in FECHADO and d not in forc]
    dom = 7*w+6
    out = []
    for c in itertools.combinations(livres, max(k, 0)):
        s = frozenset(c) | forc
        if p.dom_fixos is not None and (dom in s) != (dom in p.dom_fixos): continue
        out.append(s)
    return out

_cache = {}
def _fixos(p):
    if p.nome not in _cache or _cache[p.nome][0] is not p:
        f = set(p.forcadas) | (p.dom_fixos or set())
        for w in range(9):
            c = candidatos(p, w)
            if len(c) == 1: f |= c[0]
        _cache[p.nome] = (p, f)
    return _cache[p.nome][1]

def custo_base(pessoas, sol):
    duro = mole = 0
    for p in pessoas:
        F = set().union(*sol[p.nome])
        fixos = _fixos(p)
        run = 0
        for i in range(N):
            if i in F or i in FECHADO: run = 0
            else:
                run += 1
                if run > 5: duro += 100
        for i in range(N-1):
            if i in F and i+1 in F and not (i in fixos and i+1 in fixos): mole += 40
            if (i in F and i+1 in FECHADO) or (i in FECHADO and i+1 in F):
                if not (i in fixos or i+1 in fixos): mole += 1
        if p.evita_sab:
            mole += 3 * sum(1 for i in F if i % 7 == 5 and i not in GLOBAL_F)
        if not p.sem_regra_dom and p.dom_fixos is None:
            for doms in (DOM_DEZ, DOM_JAN):
                fd = [d for d in doms if d in F]
                if p.mulher:
                    duro += 60 * abs(len(fd) - 2)
                    if len(fd) == 2 and fd[1] - fd[0] != 14: duro += 60
                else:
                    duro += 60 * abs(len(fd) - 1)
    return duro, mole

def folgas_dia(pessoas, sol):
    cnt = [0]*N
    for p in pessoas:
        for c in sol[p.nome]:
            for d in c: cnt[d] += 1
    return cnt

def resolver(pessoas, extra, iters=60000, seed=None, tentativas=8):
    melhor = None
    for t in range(tentativas):
        rnd = random.Random((seed or 0) + t)
        cands = {p.nome: [candidatos(p, w) for w in range(9)] for p in pessoas}
        sol = {p.nome: [rnd.choice(cands[p.nome][w]) for w in range(9)] for p in pessoas}
        def total(s):
            d, m = custo_base(pessoas, s); d2, m2 = extra(s); return (d+d2)*1000 + m + m2, d+d2
        cur, curd = total(sol)
        vars_ = [(p.nome, w) for p in pessoas for w in range(9) if len(cands[p.nome][w]) > 1]
        T = 2000.0
        for it in range(iters):
            n, w = rnd.choice(vars_)
            old = sol[n][w]
            sol[n][w] = rnd.choice(cands[n][w])
            new, newd = total(sol)
            if new <= cur or rnd.random() < math.exp((cur-new)/T):
                cur, curd = new, newd
            else:
                sol[n][w] = old
            T = max(0.3, T*0.9997)
        if melhor is None or cur < melhor[0]:
            melhor = (cur, curd, {k: list(v) for k, v in sol.items()})
            print(f'  tentativa {t}: custo {cur} duro {curd}', file=sys.stderr)
        if melhor[1] == 0 and melhor[0] % 1000 < 40 and t >= 2: break
    return melhor
