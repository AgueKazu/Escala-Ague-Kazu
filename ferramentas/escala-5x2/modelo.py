"""Equipe, datas e regras da escala 5x2 de 30/11/2026 a 03/01/2027.

Tudo o que é regra da casa fica neste arquivo. O otimizador (otimizador.py)
lê daqui; para mudar uma folga fixa, um domingo ou quem faz dobra, mexa aqui.
"""

import datetime as dt
from dataclasses import dataclass, field


def d(dia, mes):
    return dt.date(2026 if mes >= 11 else 2027, mes, dia)


INICIO = d(30, 11)
FIM = d(3, 1)
DIAS = [INICIO + dt.timedelta(i) for i in range((FIM - INICIO).days + 1)]  # 35 dias
INDICE = {dia: i for i, dia in enumerate(DIAS)}
SEMANAS = [list(range(i, i + 7)) for i in range(0, len(DIAS), 7)]  # segunda a domingo
PERIODO = "30/11/2026 a 03/01/2027"

NOMES_DIA = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]

# Datas especiais
FECHADO = {INDICE[d(25, 12)], INDICE[d(1, 1)]}  # restaurante fechado: não conta como folga
COLETIVA = {INDICE[d(30, 11)], INDICE[d(31, 12)], INDICE[d(2, 1)]}  # folga de todos, conta como folga semanal
SEMANA_FINAL = SEMANAS[-1]  # 28/12 a 03/01: 31/12 e 02/01 já são as duas folgas
DOMINGO_EXTRA = INDICE[d(3, 1)]  # domingo complementar: folga aqui é exceção (3ª folga da semana)
DOMINGOS = [INDICE[d(x, 12)] for x in (6, 13, 20, 27)]
TODOS_DOMINGOS = DOMINGOS + [DOMINGO_EXTRA]

# Domingos quinzenais permitidos para quem tem dois domingos de folga
PARES_QUINZENAIS = [
    (INDICE[d(6, 12)], INDICE[d(20, 12)]),
    (INDICE[d(13, 12)], INDICE[d(27, 12)]),
    (INDICE[d(20, 12)], DOMINGO_EXTRA),
]

DATAS_ESPECIAIS = [
    (d(30, 11), "Folga coletiva, contada como folga semanal"),
    (d(25, 12), "Restaurante fechado (Natal), não conta como folga"),
    (d(31, 12), "Folga coletiva, contada como folga semanal"),
    (d(1, 1), "Restaurante fechado (Ano-Novo), não conta como folga"),
    (d(2, 1), "Folga coletiva, contada como folga semanal"),
    (d(3, 1), "Domingo complementar: folga aqui é exceção ao 5x2"),
]


def eh_domingo(i):
    return DIAS[i].weekday() == 6


def dia_aberto(i):
    """Dia em que o restaurante funciona e a escala precisa de cobertura."""
    return i not in FECHADO and i not in COLETIVA


def rotulo_data(i):
    return f"{DIAS[i]:%d/%m} {NOMES_DIA[DIAS[i].weekday()]}"


# Horários
MANHA = "08:00–17:24"
NOITE = "13:30–22:48"
SALAO = "11:30–21:54"
DOBRA = "11:45–23:00"
DOMINGO = "10:30–19:54"

# Horas efetivas por jornada (o intervalo de domingo ainda não foi definido: considerado 1h)
HORAS = {MANHA: 8.4, NOITE: 8.3, SALAO: 8.4, "Dobra": 9.25, DOMINGO: 8.4}

TURNOS = {"manha": "Manhã", "noite": "Noite", "salao": "Salão", "cobertura": "Cobertura"}


@dataclass
class Pessoa:
    nome: str
    setor: str
    turno: str  # manha, noite, salao, cobertura
    horario: str
    intervalo: str
    mulher: bool = False
    domingos_fixos: list = field(default_factory=list)
    folgas_fixas: list = field(default_factory=list)
    evitar_folga: list = field(default_factory=list)  # datas
    evitar_dias_semana: set = field(default_factory=set)  # 0 = segunda ... 6 = domingo
    dias_sem_trabalho: set = field(default_factory=set)  # ausências fixas (contam como folga)
    pode_dobrar: bool = False
    sem_dobra_semana: set = field(default_factory=set)
    prioridade_dobra: bool = False
    restricao: str = ""

    @property
    def chave(self):
        return f"{self.setor}:{self.nome}"

    def __hash__(self):
        return hash(self.chave)

    @property
    def domingos_de_folga(self):
        """Quantos domingos de folga a pessoa deve ter (None = não se aplica)."""
        if 6 in self.dias_sem_trabalho:
            return None
        return 2 if self.mulher else 1


def P(*args, **kw):
    p = Pessoa(*args, **kw)
    p.domingos_fixos = [INDICE[x] for x in p.domingos_fixos]
    p.folgas_fixas = [INDICE[x] for x in p.folgas_fixas]
    p.evitar_folga = [INDICE[x] for x in p.evitar_folga]
    return p


# ---------------------------------------------------------------------------
# Equipe por setor
# ---------------------------------------------------------------------------
BAR = [
    P("Rafael", "Bar", "manha", MANHA, "1h", domingos_fixos=[d(27, 12)], pode_dobrar=True,
      restricao="Folga fixa no 4º domingo (27/12). Dobra quando Vinicius folga."),
    P("Vinicius", "Bar", "noite", NOITE, "1h", domingos_fixos=[d(20, 12)], pode_dobrar=True,
      folgas_fixas=[d(30, 11), d(7, 12), d(14, 12)],
      restricao="Folga fixa no 3º domingo (20/12) e nas segundas até 20/12. Dobra quando Rafael folga."),
]

SUSHI = [
    P("Diogo", "Sushi", "manha", MANHA, "1h", domingos_fixos=[d(20, 12)], pode_dobrar=True,
      restricao="Folga fixa no 3º domingo (20/12). Dobra quando Allan folga."),
    P("Allan", "Sushi", "noite", NOITE, "1h", domingos_fixos=[d(27, 12)], pode_dobrar=True,
      restricao="Folga fixa no 4º domingo (27/12). Dobra quando Diogo folga."),
]

SALAO_EQUIPE = [
    P("Juliana", "Salão", "manha", MANHA, "1h", mulher=True,
      restricao="Conta só no turno da manhã (almoço). Não faz dobra."),
    P("Elaine", "Salão", "salao", SALAO, "2h", mulher=True, restricao="Não folga no mesmo dia que Marcos."),
    P("Sivanilda", "Salão", "salao", SALAO, "2h", mulher=True, folgas_fixas=[d(19, 12)],
      restricao="Folga obrigatória em 19/12."),
    P("Marcos", "Salão", "salao", SALAO, "2h", folgas_fixas=[d(26, 12)], evitar_folga=[d(13, 12)],
      evitar_dias_semana={0, 1},
      restricao="Evitar folga seg/ter e em 13/12. Folga obrigatória em 26/12. Não folga com Elaine."),
    P("Adriano", "Salão", "salao", SALAO, "2h", restricao="Não folga no mesmo dia que Guilherme."),
    P("Guilherme", "Salão", "salao", SALAO, "2h", restricao="Não folga no mesmo dia que Adriano."),
    P("Jonatan", "Salão", "salao", SALAO, "2h", restricao="Regras gerais."),
    P("Candidato", "Salão", "salao", SALAO, "2h", restricao="Regras gerais."),
]

COZINHA = [
    P("Rafael", "Cozinha", "manha", MANHA, "1h", domingos_fixos=[d(20, 12)], pode_dobrar=True,
      sem_dobra_semana={1, 2}, prioridade_dobra=True,
      restricao="Folga fixa em 20/12. Sem dobra ter/qua. Prioridade nas dobras."),
    P("Felix", "Cozinha", "manha", MANHA, "1h", pode_dobrar=True, restricao="Não folga junto com Rafael."),
    P("Rony", "Cozinha", "manha", MANHA, "1h", restricao="Não faz dobra."),
    P("Jair", "Cozinha", "manha", MANHA, "1h", pode_dobrar=True, restricao="Dobra conforme necessidade."),
    P("Edna", "Cozinha", "manha", MANHA, "1h", mulher=True, dias_sem_trabalho={5, 6},
      restricao="Não trabalha sábado e domingo. Não faz dobra."),
    P("Chef", "Cozinha", "manha", MANHA, "1h", pode_dobrar=True, prioridade_dobra=True,
      restricao="Prioridade nas dobras. Não folga junto com Rafael nem Miro."),
    P("Moura", "Cozinha", "manha", MANHA, "1h", dias_sem_trabalho={0, 1},
      restricao="Não trabalha segunda e terça. Não faz dobra."),
    P("Vinicius", "Cozinha", "noite", NOITE, "1h", pode_dobrar=True, restricao="Dobra conforme necessidade."),
    P("Andressa", "Cozinha", "noite", NOITE, "1h", mulher=True, pode_dobrar=True,
      restricao="Dois domingos de folga, quinzenais."),
    P("Samuel", "Cozinha", "noite", NOITE, "1h", pode_dobrar=True, restricao="Dobra conforme necessidade."),
    P("Miro", "Cozinha", "noite", NOITE, "1h", domingos_fixos=[d(27, 12)], pode_dobrar=True,
      prioridade_dobra=True,
      restricao="Folga fixa em 27/12. Duas segundas de folga no mês. Prioridade nas dobras."),
    P("Daniela", "Cozinha", "noite", NOITE, "1h", mulher=True, pode_dobrar=True,
      restricao="Dois domingos de folga, quinzenais."),
    P("Arten", "Cozinha", "noite", NOITE, "1h", pode_dobrar=True, restricao="Dobra conforme necessidade."),
]

PIA = [
    P("Ilma", "Pia", "manha", MANHA, "1h", mulher=True, restricao="Dois domingos quinzenais. Daniel cobre a folga."),
    P("Claudia", "Pia", "noite", NOITE, "1h", mulher=True, restricao="Dois domingos quinzenais. Daniel cobre a folga."),
    P("Daniel", "Pia", "cobertura", NOITE, "1h", pode_dobrar=True,
      restricao="Cobre as folgas de Ilma (manhã) e Claudia (noite). Não folga com elas."),
]

REFEITORIO = [
    P("Joelma", "Refeitório", "manha", MANHA, "1h", mulher=True, evitar_dias_semana={5},
      restricao="Não folga junto com Rafael da cozinha. Evitar sábado. Dois domingos quinzenais."),
]

SETORES = [
    ("Bar", BAR),
    ("Sushi", SUSHI),
    ("Salão", SALAO_EQUIPE),
    ("Cozinha", COZINHA),
    ("Pia", PIA),
    ("Refeitório", REFEITORIO),
]

META_COZINHA = {"manha": 7, "noite": 6}
MINIMO_SALAO = 5
DOBRAS_POR_SEMANA = {"prioridade": 3, "normal": 2}  # teto semanal por pessoa na cozinha


def horario_do_codigo(p, cod):
    """Texto que aparece na célula do calendário para cada código."""
    return {
        "T": p.horario,
        "M": MANHA,
        "B": "Dobra",
        "D": DOMINGO,
        "F": "Folga",
        "X": "Fechado",
    }[cod]
