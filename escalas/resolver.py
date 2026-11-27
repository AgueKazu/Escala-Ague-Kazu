import datetime as dt, json, sys
from ortools.sat.python import cp_model

INICIO = dt.date(2026,11,30)
DIAS = [INICIO + dt.timedelta(i) for i in range(63)]  # 30/11/2026 .. 31/01/2027
N = len(DIAS)
FECHADO = {dt.date(2026,12,25), dt.date(2027,1,1)}
COLETIVA = {dt.date(2026,11,30), dt.date(2026,12,31), dt.date(2027,1,2)}
idx = {d:i for i,d in enumerate(DIAS)}
dom = lambda i: DIAS[i].weekday()==6
dow = lambda i: DIAS[i].weekday()
semana = lambda i: i//7
dom_dez = [i for i in range(N) if dom(i) and DIAS[i].month==12]
dom_jan = [i for i in range(N) if dom(i) and DIAS[i].month==1]
def D(d,m,y=None): return idx[dt.date(y or (2026 if m>=11 else 2027),m,d)]

M_ = "08:00–17:24"; N_ = "13:30–22:48"; S_ = "11:30–21:54"
# (setor, id, nome, horario, mulher, pode_dobrar)
P = []
def add(setor, id_, nome, h, mulher=False, dobra=True, grupo=None):
    P.append(dict(setor=setor,id=id_,nome=nome,h=h,mulher=mulher,dobra=dobra,grupo=grupo))
add("Bar","bar_rafael","Rafael",M_); add("Bar","bar_vinicius","Vinicius",N_)
add("Sushi","su_diogo","Diogo",M_); add("Sushi","su_allan","Allan",N_)
add("Salão","juliana","Juliana",M_,True)
for n,mu in [("Elaine",True),("Sivanilda",True),("Marcos",False),("Adriano",False),("Guilherme",False),("Jonatan",False),("Candidato",False)]:
    add("Salão",n.lower(),n,S_,mu)
for n,mu,db in [("Rafael",False,True),("Felix",False,True),("Adilton",False,True),("Rony",False,False),("Jair",False,True),("Edna",True,False),("Chef",False,True)]:
    add("Cozinha","co_"+n.lower(),n,M_,mu,db,"Manhã")
for n,mu in [("Vinicius",False),("Andressa",True),("Samuel",False),("Miro",False),("Daniela",True),("Arten",False)]:
    add("Cozinha","co_"+n.lower(),n,N_,mu,True,"Noite")
add("Pia","ilma","Ilma",M_,True); add("Pia","claudia","Claudia",N_,True); add("Pia","daniel","Daniel",N_)
add("Refeitório","joelma","Joelma",M_,True)
E = {p["id"]:p for p in P}

m = cp_model.CpModel()
off = {}
for e in E:
    for i in range(N):
        if DIAS[i] in FECHADO: off[e,i] = 0
        elif DIAS[i] in COLETIVA: off[e,i] = 1
        else: off[e,i] = m.NewBoolVar(f"off_{e}_{i}")
def work(e,i): return 0 if DIAS[i] in FECHADO else 1-off[e,i]
livre = lambda i: DIAS[i] not in FECHADO and DIAS[i] not in COLETIVA
pen = []

for e,p in E.items():
    for w in range(9):
        dias_w = range(7*w,7*w+7)
        if e=="co_adilton": continue
        m.Add(sum(off[e,i] for i in dias_w)==2)
    lim = 6 if e=="co_adilton" else 5
    for s in range(N-lim):
        m.Add(sum(work(e,i) for i in range(s,s+lim+1))<=lim)
    # evitar folgas seguidas (penalidade)
    for i in range(N-1):
        a,b = off[e,i],off[e,i+1]
        if isinstance(a,int) or isinstance(b,int):
            if isinstance(a,int) and isinstance(b,int): continue
            v = b if isinstance(a,int) else a
            if (a if isinstance(a,int) else b)==1: pen.append(10*v)
            continue
        z = m.NewBoolVar(""); m.AddBoolAnd([a,b]).OnlyEnforceIf(z); m.AddBoolOr([a.Not(),b.Not()]).OnlyEnforceIf(z.Not())
        pen.append(10*z)
    # domingos
    if e=="joelma" or True:
        q = 2 if p["mulher"] else 1
        for lst in (dom_dez, dom_jan):
            m.Add(sum(off[e,i] for i in lst)==q)
        if p["mulher"]:
            todos = dom_dez+dom_jan
            for a,b in zip(todos,todos[1:]):
                if not isinstance(off[e,a],int) and not isinstance(off[e,b],int):
                    m.Add(off[e,a]+off[e,b]<=1)

def fixa(e,i): m.Add(off[e,i]==1)
# domingos fixos (3º/4º domingo; janeiro conta a partir de 03/01)
for e,k in [("bar_rafael",3),("bar_vinicius",2),("su_diogo",2),("su_allan",3),("co_rafael",2),("co_miro",3)]:
    fixa(e,dom_dez[k]); fixa(e,dom_jan[k])

# Bar e Sushi: nunca os dois de folga
for a,b in [("bar_rafael","bar_vinicius"),("su_diogo","su_allan")]:
    for i in range(N):
        if livre(i): m.Add(off[a,i]+off[b,i]<=1)

# Salão
fixa("sivanilda",D(19,12)); fixa("marcos",D(26,12))
outros = ["elaine","sivanilda","marcos","adriano","guilherme","jonatan","candidato"]
for i in range(N):
    if not livre(i): continue
    m.Add(off["elaine",i]+off["marcos",i]<=1)
    m.Add(off["guilherme",i]+off["adriano",i]<=1)
    tot = sum(off[o,i] for o in outros)
    m.Add(tot<=3)
    m.Add(tot<=2).OnlyEnforceIf(off["juliana",i])
    # Juliana: folgas em terça/sábado (domingo só no domingo quinzenal)
    if dow(i) not in (1,5,6): m.Add(off["juliana",i]==0)

# Cozinha
manha = [e for e in E if E[e]["grupo"]=="Manhã"]; noite=[e for e in E if E[e]["grupo"]=="Noite"]
dob = {}
for e in manha+noite:
    for i in range(N):
        if livre(i) and not dom(i) and E[e]["dobra"] and not (e=="co_rafael" and dow(i) in (1,2)):
            v = m.NewBoolVar(""); m.Add(v<=work(e,i)); dob[e,i]=v
for i in range(N):
    if not livre(i): continue
    if not dom(i):
        m.Add(sum(dob.get((e,i),0) for e in noite)==sum(off[e,i] for e in manha))
        m.Add(sum(dob.get((e,i),0) for e in manha)==sum(off[e,i] for e in noite))
    for a,b in [("co_miro","co_rafael"),("co_miro","co_chef"),("co_rafael","co_chef")]:
        m.Add(off[a,i]+off[b,i]<=1)
    m.Add(off["joelma",i]+off["co_rafael",i]<=1)
# Adilton: 1 folga fixa (quarta) + domingo do mês
for i in range(N):
    if not livre(i): continue
    if dom(i): continue
    w28 = semana(i)==semana(D(28,12))
    m.Add(off["co_adilton",i]==(1 if dow(i)==2 and not w28 else 0))
# Miro: 2 segundas por mês
seg_dez=[i for i in range(N) if dow(i)==0 and DIAS[i].month==12]; seg_jan=[i for i in range(N) if dow(i)==0 and DIAS[i].month==1]
for lst in (seg_dez,seg_jan):
    m.Add(sum(off["co_miro",i] for i in lst)==2)
    for a,b in zip(lst,lst[1:]): m.Add(off["co_miro",a]+off["co_miro",b]<=1)
# equilíbrio de dobras e folgas por dia
for mes in (12,1):
    mx = m.NewIntVar(0,40,"")
    for e in manha+noite:
        if E[e]["dobra"]:
            m.Add(sum(v for (ee,i),v in dob.items() if ee==e and DIAS[i].month==mes)<=mx)
    pen.append(5*mx)
for grupo in (manha,noite,outros):
    for i in range(N):
        if livre(i) and not dom(i):
            t = sum(off[e,i] for e in grupo)
            ex = m.NewIntVar(0,7,""); m.Add(ex>=t-2); pen.append(3*ex)

# Pia
for i in range(N):
    if not livre(i): continue
    I,C,Dn = off["ilma",i],off["claudia",i],off["daniel",i]
    if dom(i): m.Add(Dn+I<=1); m.Add(Dn+C<=1)
    else: m.Add(I+C+Dn<=1)

m.Minimize(sum(pen))
s = cp_model.CpSolver(); s.parameters.max_time_in_seconds=120; s.parameters.num_workers=8
r = s.Solve(m)
print(s.StatusName(r), s.ObjectiveValue() if r in (cp_model.OPTIMAL,cp_model.FEASIBLE) else "")
if r not in (cp_model.OPTIMAL,cp_model.FEASIBLE): sys.exit(1)
val = lambda x: x if isinstance(x,int) else s.Value(x)
out = {"dias":[d.isoformat() for d in DIAS],"pessoas":P,"celulas":{}}
for e,p in E.items():
    row=[]
    for i in range(N):
        d=DIAS[i]
        if d in FECHADO: row.append(("FECHADO","fechado")); continue
        if val(off[e,i]): row.append(("FOLGA","folga")); continue
        if dom(i): row.append(("10:30–19:54","domingo")); continue
        dobra=False
        if (e,i) in dob: dobra = s.Value(dob[e,i])==1
        par={"bar_rafael":"bar_vinicius","bar_vinicius":"bar_rafael","su_diogo":"su_allan","su_allan":"su_diogo"}
        if e in par and val(off[par[e],i]): dobra=True
        if e=="daniel" and val(off["ilma",i]): dobra=True
        row.append(("DOBRA 11:45–23:00","dobra") if dobra else (p["h"],"normal"))
    out["celulas"][e]=row
json.dump(out,open(sys.argv[1],"w"),ensure_ascii=False)
