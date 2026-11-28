"""Monta as folgas e as dobras de cada setor com o OR-Tools (CP-SAT).

Regras obrigatórias viram restrições (o programa não aceita violá-las).
Preferências e metas viram "pontos de problema": o otimizador procura a escala
com a menor soma de pontos. Os pesos seguem a ordem de prioridade do pedido:
descanso legal > datas coletivas > 5 dias seguidos > folgas obrigatórias >
duas folgas por semana > domingos > mínimo por turno > folgas simultâneas >
equilíbrio das dobras > folgas seguidas > preferências.

Códigos devolvidos por dia: T (horário normal), M (Daniel na manhã),
B (dobra), D (domingo), F (folga), X (fechado).
"""

from ortools.sat.python import cp_model

from modelo import (
    BAR, COLETIVA, COZINHA, DIAS, DOBRAS_POR_SEMANA, DOMINGO_EXTRA, FECHADO, INDICE,
    META_COZINHA, MINIMO_SALAO, PARES_QUINZENAIS, PIA, REFEITORIO, SALAO_EQUIPE,
    SEMANA_FINAL, SEMANAS, SUSHI, TODOS_DOMINGOS, d, dia_aberto, eh_domingo,
)

N = len(DIAS)

# Pesos (pontos de problema)
DOMINGO_FALTANDO = 3000
EXCESSO_FOLGA_MANHA = 1000
JUNTOS_PROIBIDO = 1000
JUNTOS_EVITAR = 800
DEFICIT_COZINHA = 300
DEFICIT_SALAO_FIM = 250
DEFICIT_SALAO_SEMANA = 70
DOMINGO_COMPLEMENTAR = 150
EVITAR_DATA = 200
FOLGA_SEGUIDA = 40
EVITAR_DIA_SEMANA = 30


class Modelo:
    def __init__(self):
        self.m = cp_model.CpModel()
        self.custos = []  # (peso, expressão)
        self.f = {}  # (pessoa, dia) -> folga
        self.b = {}  # (pessoa, dia) -> dobra

    def bool(self):
        return self.m.NewBoolVar("")

    def custo(self, peso, expr):
        self.custos.append((peso, expr))

    def excesso(self, expr, limite, peso):
        """Penaliza o quanto expr passa de limite."""
        v = self.m.NewIntVar(0, 50, "")
        self.m.Add(v >= expr - limite)
        self.custo(peso, v)
        return v

    def juntos(self, a, b, peso, dias=None):
        """Penaliza (ou proíbe, se peso=None) folga de a e b no mesmo dia aberto."""
        for i in dias if dias is not None else range(N):
            if not dia_aberto(i):
                continue
            if peso is None:
                self.m.Add(self.f[a, i] + self.f[b, i] <= 1)
            else:
                self.excesso(self.f[a, i] + self.f[b, i], 1, peso)

    # -------------------------------------------------------------------
    def pessoa(self, p):
        m = self.m
        forcadas = set(COLETIVA)
        forcadas |= set(p.folgas_fixas) | set(p.domingos_fixos)
        forcadas |= {i for i in range(N) if DIAS[i].weekday() in p.dias_sem_trabalho}
        forcadas -= FECHADO
        for i in range(N):
            if i in FECHADO:
                continue
            self.f[p, i] = v = self.bool()
            if i in forcadas:
                m.Add(v == 1)
        f = lambda i: self.f[p, i] if i not in FECHADO else 0  # noqa: E731

        # Duas folgas por semana (ausências fixas podem passar de 2: Edna e Moura)
        for s in SEMANAS:
            fixas = [i for i in s if i in forcadas]
            livres = [i for i in s if i not in forcadas and i not in FECHADO]
            if s == SEMANA_FINAL:
                for i in livres:  # 31/12 e 02/01 já são as duas folgas
                    if i != DOMINGO_EXTRA:
                        m.Add(self.f[p, i] == 0)
                continue
            if len(fixas) >= 2:
                for i in livres:
                    m.Add(self.f[p, i] == 0)
            else:
                m.Add(sum(f(i) for i in s) == 2)

        # Máximo de 5 dias seguidos (fechado também quebra a sequência)
        trabalha = [0 if i in FECHADO else 1 - self.f[p, i] for i in range(N)]
        for i in range(N - 5):
            m.Add(sum(trabalha[i:i + 6]) <= 5)

        # Domingos de folga
        q = p.domingos_de_folga
        if q == 2:
            z = [self.bool() for _ in PARES_QUINZENAIS]
            m.AddExactlyOne(z)
            for s in TODOS_DOMINGOS:
                m.Add(self.f[p, s] == sum(zk for zk, par in zip(z, PARES_QUINZENAIS) if s in par))
        elif q == 1:
            total = sum(self.f[p, s] for s in TODOS_DOMINGOS)
            m.Add(total <= 1)
            falta = self.bool()
            m.Add(total + falta >= 1)
            self.custo(DOMINGO_FALTANDO, falta)
        if q:
            self.custo(DOMINGO_COMPLEMENTAR, self.f[p, DOMINGO_EXTRA])

        # Preferências
        for i in range(N - 1):
            if i in FECHADO or i + 1 in FECHADO or (i in forcadas and i + 1 in forcadas):
                continue
            self.excesso(self.f[p, i] + self.f[p, i + 1], 1, FOLGA_SEGUIDA)
        for i in p.evitar_folga:
            self.custo(EVITAR_DATA, self.f[p, i])
        for i in range(N):
            if dia_aberto(i) and DIAS[i].weekday() in p.evitar_dias_semana:
                self.custo(EVITAR_DIA_SEMANA, self.f[p, i])

        # Dobras
        for i in range(N):
            if not dia_aberto(i) or eh_domingo(i):
                continue
            if p.pode_dobrar and DIAS[i].weekday() not in p.sem_dobra_semana:
                self.b[p, i] = v = self.bool()
                m.AddImplication(v, self.f[p, i].Not())

        # Descanso de 11h entre jornadas: quem entra às 08:00 não pode ter feito dobra
        # (saída 23:00) na véspera. Domingo começa 10:30, então sábado com dobra é permitido.
        if p.turno == "manha":
            for i in range(N - 1):
                if (p, i) not in self.b or eh_domingo(i + 1) or not dia_aberto(i + 1):
                    continue
                prox = [self.f[p, i + 1]] + ([self.b[p, i + 1]] if (p, i + 1) in self.b else [])
                m.AddBoolOr(prox).OnlyEnforceIf(self.b[p, i])

    def dobra(self, p, i):
        return self.b.get((p, i), 0)

    def resolver(self, segundos=60):
        self.m.Minimize(sum(peso * e for peso, e in self.custos))
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = segundos
        s.parameters.num_workers = 1  # resultado sempre igual a cada execução
        s.parameters.random_seed = 7
        st = s.Solve(self.m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError(f"Sem solução: {s.StatusName(st)}")
        self.solver = s
        return s.ObjectiveValue(), s.StatusName(st)

    def valor(self, v):
        return int(self.solver.Value(v)) if not isinstance(v, int) else v

    def codigos(self, p, manha_daniel=None):
        cod = []
        for i in range(N):
            if i in FECHADO:
                cod.append("X")
            elif self.valor(self.f[p, i]):
                cod.append("F")
            elif eh_domingo(i):
                cod.append("D")
            elif self.valor(self.dobra(p, i)):
                cod.append("B")
            elif manha_daniel and self.valor(manha_daniel.get(i, 0)):
                cod.append("M")
            else:
                cod.append("T")
        return cod


# ---------------------------------------------------------------------------
# Setores
# ---------------------------------------------------------------------------
def dupla(pessoas):
    """Bar e Sushi: os dois nunca folgam juntos; quem fica faz dobra (domingo é turno único)."""
    M = Modelo()
    for p in pessoas:
        M.pessoa(p)
    a, b = pessoas
    M.juntos(a, b, None)
    for i in range(N):
        if not dia_aberto(i):
            continue
        if eh_domingo(i):
            continue
        M.m.Add(M.b[a, i] == M.f[b, i])
        M.m.Add(M.b[b, i] == M.f[a, i])
    pontos, status = M.resolver(30)
    return {p: M.codigos(p) for p in pessoas}, pontos, status


def salao(pessoas):
    M = Modelo()
    for p in pessoas:
        M.pessoa(p)
    por = {p.nome: p for p in pessoas}
    M.juntos(por["Elaine"], por["Marcos"], None)
    M.juntos(por["Adriano"], por["Guilherme"], None)
    jantar = [p for p in pessoas if p.turno == "salao"]
    for i in range(N):
        if not dia_aberto(i):
            continue
        fim = DIAS[i].weekday() >= 4
        peso = DEFICIT_SALAO_FIM if fim else DEFICIT_SALAO_SEMANA
        no_jantar = sum(1 - M.f[p, i] for p in jantar)
        no_almoco = no_jantar + 1 - M.f[por["Juliana"], i]
        M.excesso(MINIMO_SALAO - no_jantar, 0, peso)
        M.excesso(MINIMO_SALAO - no_almoco, 0, peso)
        if fim:  # quadro mais cheio de sexta a domingo
            M.custo(10, sum(M.f[p, i] for p in pessoas))
    pontos, status = M.resolver(60)
    return {p: M.codigos(p) for p in pessoas}, pontos, status


def cozinha_e_refeitorio(cozinha, refeitorio):
    M = Modelo()
    for p in cozinha + refeitorio:
        M.pessoa(p)
    por = {p.nome: p for p in cozinha}
    joelma = refeitorio[0]
    manha = [p for p in cozinha if p.turno == "manha"]
    noite = [p for p in cozinha if p.turno == "noite"]

    # Folgas simultâneas
    for a, b in (("Rafael", "Miro"), ("Rafael", "Chef"), ("Miro", "Chef")):
        M.juntos(por[a], por[b], JUNTOS_EVITAR)
    M.juntos(por["Rafael"], por["Felix"], JUNTOS_PROIBIDO)
    M.juntos(por["Rafael"], joelma, JUNTOS_PROIBIDO)

    # Miro: duas segundas de folga em dezembro (28/12 é semana de fim de ano, todos trabalham)
    segundas = [INDICE[d(x, 12)] for x in (7, 14, 21)]
    M.m.Add(sum(M.f[por["Miro"], i] for i in segundas) == 2)

    # Joelma: folga de preferência em dia de menor movimento (seg a qua)
    for i in range(N):
        if dia_aberto(i) and DIAS[i].weekday() in (3, 4):
            M.custo(10, M.f[joelma, i])

    for i in range(N):
        if not dia_aberto(i):
            continue
        folga_manha = sum(M.f[p, i] for p in manha)
        M.excesso(folga_manha, 2, EXCESSO_FOLGA_MANHA)  # inclui Edna e Moura
        na_manha = sum(1 - M.f[p, i] for p in manha) + sum(M.dobra(p, i) for p in noite)
        na_noite = sum(1 - M.f[p, i] for p in noite) + sum(M.dobra(p, i) for p in manha)
        peso = DEFICIT_COZINHA  # domingo também conta: é dia de movimento (sem dobra, turno único)
        for meta, presentes in ((META_COZINHA["manha"], na_manha), (META_COZINHA["noite"], na_noite)):
            M.excesso(meta - presentes, 0, peso)
            M.excesso(meta - presentes, 2, 2 * peso)  # falta de 3 ou mais pesa o triplo

    # Dobras: teto semanal, prioridade para Rafael, Miro e Chef, equilíbrio entre os demais
    total = {}
    for p in cozinha:
        if not p.pode_dobrar:
            continue
        teto = DOBRAS_POR_SEMANA["prioridade" if p.prioridade_dobra else "normal"]
        for s in SEMANAS:
            M.m.Add(sum(M.dobra(p, i) for i in s) <= teto)
        total[p] = sum(M.dobra(p, i) for i in range(N))
        M.custo(6 if p.prioridade_dobra else 10, total[p])
    normais = [p for p in total if not p.prioridade_dobra]
    maior, menor = M.m.NewIntVar(0, 40, ""), M.m.NewIntVar(0, 40, "")
    for p in normais:
        M.m.Add(maior >= total[p])
        M.m.Add(menor <= total[p])
    M.custo(25, maior - menor)
    for p in total:
        if p.prioridade_dobra:
            M.excesso(maior + 1 - total[p], 0, 40)

    pontos, status = M.resolver(120)
    return ({p: M.codigos(p) for p in cozinha}, {joelma: M.codigos(joelma)}), pontos, status


def pia(pessoas):
    M = Modelo()
    for p in pessoas:
        M.pessoa(p)
    ilma, claudia, daniel = pessoas
    M.juntos(daniel, ilma, None)
    M.juntos(daniel, claudia, None)
    M.juntos(ilma, claudia, JUNTOS_EVITAR)
    manha = {}
    for i in range(N):
        if not dia_aberto(i) or eh_domingo(i):
            continue
        fi, fc = M.f[ilma, i], M.f[claudia, i]
        manha[i] = mi = M.bool()
        # Daniel na manhã quando só Ilma folga; dobra quando as duas folgam
        M.m.AddBoolAnd([fi, fc.Not()]).OnlyEnforceIf(mi)
        M.m.AddBoolOr([fi.Not(), fc, mi])
        bi = M.b[daniel, i]
        M.m.AddBoolAnd([fi, fc]).OnlyEnforceIf(bi)
        M.m.AddBoolOr([fi.Not(), fc.Not(), bi])
    # Descanso de 11h: Daniel só entra às 08:00 se na véspera folgou, fez manhã ou era domingo
    for i, mi in manha.items():
        ontem = i - 1
        if ontem < 0 or not dia_aberto(ontem) or eh_domingo(ontem):
            continue
        opcoes = [M.f[daniel, ontem]] + ([manha[ontem]] if ontem in manha else [])
        M.m.AddBoolOr(opcoes).OnlyEnforceIf(mi)
    pontos, status = M.resolver(30)
    return {p: M.codigos(p, manha if p is daniel else None) for p in pessoas}, pontos, status


def montar_escala():
    """Devolve {setor: {pessoa: [códigos por dia]}} e a situação do otimizador por setor."""
    escala, situacao = {}, {}
    for nome, pessoas in (("Bar", BAR), ("Sushi", SUSHI)):
        escala[nome], *situacao[nome] = dupla(pessoas)
    escala["Salão"], *situacao["Salão"] = salao(SALAO_EQUIPE)
    (escala["Cozinha"], escala["Refeitório"]), *situacao["Cozinha + Refeitório"] = \
        cozinha_e_refeitorio(COZINHA, REFEITORIO)
    escala["Pia"], *situacao["Pia"] = pia(PIA)
    ordem = ["Bar", "Sushi", "Salão", "Cozinha", "Pia", "Refeitório"]
    return {s: escala[s] for s in ordem}, situacao
