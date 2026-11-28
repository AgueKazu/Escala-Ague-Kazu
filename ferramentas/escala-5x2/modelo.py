"""Equipe, datas e regras da escala 5x2 de 30/11/2026 a 31/01/2027 (Restaurante Kazu).

Tudo o que for regra da casa fica neste arquivo. O otimizador (otimizador.py)
lê daqui e não conhece nenhum nome de funcionário.
"""

import datetime as dt
from dataclasses import dataclass, field


def d(dia, mes, ano=None):
    if ano is None:
        ano = 2026 if mes >= 11 else 2027
    return dt.date(ano, mes, dia)


INICIO = d(30, 11)
FIM = d(31, 1)
DIAS = [INICIO + dt.timedelta(i) for i in range((FIM - INICIO).days + 1)]
INDICE = {dia: i for i, dia in enumerate(DIAS)}
SEMANAS = [list(range(i, i + 7)) for i in range(0, len(DIAS), 7)]  # segunda a domingo

NOMES_DIA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# Datas especiais
FECHADO = {INDICE[d(25, 12)], INDICE[d(1, 1)]}  # restaurante fechado, não conta como folga
COLETIVA = {INDICE[d(30, 11)], INDICE[d(31, 12)], INDICE[d(2, 1)]}  # folga de toda a equipe
SEMANA_FIM_DE_ANO = next(s for s in SEMANAS if INDICE[d(31, 12)] in s)  # 28/12 a 03/01
JANELA_FIM_DE_ANO = set(range(INDICE[d(31, 12)], INDICE[d(3, 1)] + 1))  # folgas seguidas permitidas
DOMINGO_3_JAN = INDICE[d(3, 1)]

DATAS_ESPECIAIS = [
    (d(30, 11), "Folga geral, contabilizada na semana"),
    (d(25, 12), "Restaurante fechado, sem descontar folga"),
    (d(31, 12), "Folga geral contabilizada"),
    (d(1, 1), "Restaurante fechado, sem descontar folga"),
    (d(2, 1), "Folga geral contabilizada"),
    (d(3, 1), "Considerar na apuração dos domingos de janeiro"),
]


def eh_domingo(i):
    return DIAS[i].weekday() == 6


def dia_aberto(i):
    """Dia em que o restaurante funciona e a escala precisa de cobertura."""
    return i not in FECHADO and i not in COLETIVA


DOMINGOS_POR_MES = {
    "Dez": [i for i, x in enumerate(DIAS) if x.weekday() == 6 and x.month == 12],
    "Jan": [i for i, x in enumerate(DIAS) if x.weekday() == 6 and x.month == 1],
}


@dataclass
class Pessoa:
    nome: str
    setor: str
    turno: str  # "manha", "noite", "salao", "cobertura"
    horario: str
    intervalo: str
    domingos_mes: int | None = 1  # domingos de folga por mês (None = não se aplica)
    domingos_fixos: list = field(default_factory=list)  # domingos de folga já definidos
    folgas_fixas: list = field(default_factory=list)
    trabalho_fixo: list = field(default_factory=list)
    dias_sem_trabalho: set = field(default_factory=set)  # 0 = segunda ... 6 = domingo
    pode_dobrar: bool = False
    sem_dobra_semana: set = field(default_factory=set)
    peso_dobra: float = 1.0
    observacao: str = ""

    def __hash__(self):
        return hash(self.nome)


def P(*args, **kw):
    p = Pessoa(*args, **kw)
    p.domingos_fixos = [INDICE[x] for x in p.domingos_fixos]
    p.folgas_fixas = [INDICE[x] for x in p.folgas_fixas]
    p.trabalho_fixo = [INDICE[x] for x in p.trabalho_fixo]
    return p


MANHA = "08:00–17:24"
NOITE = "13:30–22:48"
SALAO = "11:30–21:54"
DOMINGO = "10:30–19:54"
DOBRA = "11:45–23:00"

# ---------------------------------------------------------------------------
# Equipe por setor
# ---------------------------------------------------------------------------
BAR = [
    P("Rafael", "Bar", "manha", MANHA, "1h", domingos_fixos=[d(27, 12), d(24, 1)],
      observacao="4º domingo"),
    P("Vinicius", "Bar", "noite", NOITE, "1h", domingos_fixos=[d(20, 12), d(17, 1)],
      folgas_fixas=[d(7, 12), d(14, 12)],
      observacao="3º domingo; folga às segundas até 20/12"),
]

SUSHI = [
    P("Diogo", "Sushi", "manha", MANHA, "1h", domingos_fixos=[d(20, 12), d(17, 1)],
      observacao="3º domingo"),
    P("Allan", "Sushi", "noite", NOITE, "1h", domingos_fixos=[d(27, 12), d(24, 1)],
      observacao="4º domingo"),
]

SALAO_EQUIPE = [
    P("Juliana", "Salão", "manha", MANHA, "1h", domingos_mes=2, observacao="Somente um turno"),
    P("Elaine", "Salão", "salao", SALAO, "2h", domingos_mes=2, observacao="Não folga com Marcos"),
    P("Sivanilda", "Salão", "salao", SALAO, "2h", domingos_mes=2, folgas_fixas=[d(19, 12)],
      observacao="Folga em 19/12"),
    P("Marcos", "Salão", "salao", SALAO, "2h", folgas_fixas=[d(26, 12)], trabalho_fixo=[d(13, 12)],
      observacao="Folga em 26/12; trabalha 13/12; evitar seg/ter"),
    P("Adriano", "Salão", "salao", SALAO, "2h", observacao="Não folga com Guilherme"),
    P("Guilherme", "Salão", "salao", SALAO, "2h", observacao="Não folga com Adriano"),
    P("Jonatan", "Salão", "salao", SALAO, "2h", observacao="Escala normal"),
    P("Candidato", "Salão", "salao", SALAO, "2h", observacao="Escala normal"),
]

COZINHA = [
    P("Rafael", "Cozinha", "manha", MANHA, "1h", domingos_fixos=[d(20, 12), d(17, 1)],
      pode_dobrar=True, sem_dobra_semana={1, 2}, peso_dobra=1.5,
      observacao="3º domingo; sem dobra ter/qua"),
    P("Felix", "Cozinha", "manha", MANHA, "1h", pode_dobrar=True, observacao="Escala normal"),
    P("Rony", "Cozinha", "manha", MANHA, "1h", observacao="Não faz dobra"),
    P("Jair", "Cozinha", "manha", MANHA, "1h", pode_dobrar=True, observacao="Escala normal"),
    P("Edna", "Cozinha", "manha", MANHA, "1h", domingos_mes=None, dias_sem_trabalho={5, 6},
      observacao="Não trabalha fim de semana nem dobra"),
    P("Chef", "Cozinha", "manha", MANHA, "1h", pode_dobrar=True, peso_dobra=1.6,
      observacao="Prioridade nas dobras"),
    P("Moura", "Cozinha", "manha", MANHA, "1h", dias_sem_trabalho={0, 1},
      observacao="Não trabalha seg/ter nem dobra"),
    P("Vinicius", "Cozinha", "noite", NOITE, "1h", pode_dobrar=True, observacao="Escala normal"),
    P("Andressa", "Cozinha", "noite", NOITE, "1h", domingos_mes=2, pode_dobrar=True,
      observacao="Dois domingos de folga"),
    P("Samuel", "Cozinha", "noite", NOITE, "1h", pode_dobrar=True, observacao="Escala normal"),
    P("Miro", "Cozinha", "noite", NOITE, "1h", domingos_fixos=[d(27, 12), d(24, 1)],
      pode_dobrar=True, peso_dobra=1.5, observacao="4º domingo; duas segundas de folga por mês"),
    P("Daniela", "Cozinha", "noite", NOITE, "1h", domingos_mes=2, pode_dobrar=True,
      observacao="Dois domingos de folga"),
    P("Arten", "Cozinha", "noite", NOITE, "1h", pode_dobrar=True, observacao="Escala normal"),
]

PIA = [
    P("Ilma", "Pia", "manha", MANHA, "1h", domingos_mes=2, observacao="Turno da manhã"),
    P("Claudia", "Pia", "noite", NOITE, "1h", domingos_mes=2, observacao="Turno da noite"),
    P("Daniel", "Pia", "cobertura", NOITE, "1h", observacao="Cobre as folgas de Ilma e Claudia"),
]

REFEITORIO = [
    P("Joelma", "Refeitório", "manha", MANHA, "1h", domingos_mes=2,
      observacao="Não folga junto com Rafael da cozinha; evitar sábado"),
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
