"""Traduz os códigos internos (T, F, X, B, D, M) para os códigos impressos na escala.

Códigos impressos:
  M  Manhã 08:00–17:24          N  Noite 13:30–22:48       I  Integral 11:30–21:54
  S  Domingo 10:30–19:54        D  Dobra 11:45–23:00       DS Cobertura de domingo 10:30–19:54
  F  Folga                      H  Restaurante fechado
"""

from modelo import DIAS, DOBRA, DOMINGO, MANHA, NOITE, SALAO

LEGENDA = [
    ("M", "Manhã", MANHA, "1h"),
    ("N", "Noite", NOITE, "1h"),
    ("I", "Integral", SALAO, "2h"),
    ("S", "Domingo", DOMINGO, "A definir"),
    ("D", "Dobra", DOBRA, "2h"),
    ("DS", "Cobertura domingo", DOMINGO, "A definir"),
    ("F", "Folga", "—", "—"),
    ("H", "Restaurante fechado", "—", "—"),
]

CORES = {
    "cinza": "D9D9D9",   # datas e dias da semana
    "F": "FF7B7B",       # folgas (vermelho)
    "H": "8FD18F",       # restaurante fechado (verde)
    "D": "FFB25B",       # dobras (laranja)
    "DS": "FFB25B",
    "S": "F9C6DD",       # domingos (rosa)
    "domingo": "F9C6DD",
    "titulo": "1F3864",
    "alerta": "FFC7CE",
}

TRABALHO = ("M", "N", "I", "S", "D", "DS")
DOBRAS = ("D", "DS")

# Quem cobre o colega no domingo (turno único): pares do Bar e do Sushi e Daniel na Pia
COBERTURA_DOMINGO = {"Bar": None, "Sushi": None, "Pia": "Daniel"}


def codigo_turno(p):
    return {"manha": "M", "noite": "N", "salao": "I", "cobertura": "N"}[p.turno]


def traduzir_setor(setor, pessoas):
    """{pessoa: [códigos internos]} -> {pessoa: [códigos impressos]}"""
    lista = list(pessoas.items())
    saida = {}
    for p, cod in lista:
        novo = []
        for i, x in enumerate(cod):
            if x == "X":
                novo.append("H")
            elif x == "F":
                novo.append("F")
            elif x == "B":
                novo.append("D")
            elif x == "M":
                novo.append("M")
            elif x == "D":  # domingo trabalhado
                novo.append("DS" if cobre_domingo(setor, p, lista, i) else "S")
            else:
                novo.append(codigo_turno(p))
        saida[p] = novo
    return saida


def cobre_domingo(setor, p, lista, i):
    if setor not in COBERTURA_DOMINGO:
        return False
    responsavel = COBERTURA_DOMINGO[setor]
    if responsavel and p.nome != responsavel:
        return False
    colegas = [c for q, c in lista if q is not p]
    return any(c[i] == "F" for c in colegas)


def traduzir(escala):
    return {setor: traduzir_setor(setor, pessoas) for setor, pessoas in escala.items()}


def eh_domingo(i):
    return DIAS[i].weekday() == 6


MESES = {
    "Dez": ("Dezembro/2026 (30/11 a 31/12)", [i for i, x in enumerate(DIAS) if x.month in (11, 12)]),
    "Jan": ("Janeiro/2027 (01/01 a 31/01)", [i for i, x in enumerate(DIAS) if x.month == 1]),
}

REGRAS_GERAIS = [
    "Regime de trabalho 5x2, com duas folgas semanais por colaborador.",
    "Não ultrapassar cinco dias consecutivos de trabalho, inclusive na transição entre os meses.",
    "Evitar duas folgas consecutivas, sempre que possível.",
    "Considerar a semana de segunda-feira a domingo.",
    "Homens: uma folga dominical por mês.",
    "Mulheres: duas folgas dominicais por mês, preferencialmente quinzenais.",
    "Respeitar os domingos fixos e as restrições individuais.",
    "Distribuir as folgas de maneira equilibrada, garantindo a cobertura operacional.",
    "Distribuir as dobras entre os colaboradores autorizados, respeitando as prioridades de cada setor.",
    "Considerar 03/01/2027 na apuração das folgas dominicais de janeiro.",
]

PADRONIZACAO = [
    ("cinza", "Cinza", "Datas e dias da semana"),
    ("F", "Vermelho", "Folgas"),
    ("H", "Verde", "Feriados com restaurante fechado"),
    ("D", "Laranja", "Dobras de horário"),
    ("S", "Rosa", "Domingos"),
]

PONTOS_DE_ATENCAO = [
    "Cozinha: nem sempre é possível garantir sete pessoas de manhã e seis à noite apenas com os "
    "colaboradores disponíveis e autorizados a dobrar. Além disso, a dobra iniciada às 11h45 não "
    "cobre uma ausência às 8h.",
    "Edna: por não trabalhar aos finais de semana, terá mais de dois domingos de folga no mês.",
    "Moura: por ter segunda e terça-feira fixas, terá necessariamente folgas consecutivas.",
    "Folgas gerais: prevalecem sobre as restrições de colaboradores que não podem folgar juntos.",
    "Domingos: considerado um único turno de funcionamento.",
]

SETORES_RESUMO = [
    ("Bar", 2), ("Sushi", 2), ("Salão", 8), ("Cozinha — manhã", 7), ("Cozinha — noite", 6),
    ("Pia", 3), ("Refeitório", 1),
]


def turno_legivel(p):
    return {"manha": "Manhã", "noite": "Noite", "salao": "Integral", "cobertura": "Cobertura"}[p.turno]


def agrupar_pendencias(ocorrencias):
    """Junta as exceções e preferências não atendidas por setor e regra."""
    grupos = {}
    for o in ocorrencias:
        if o["tipo"] == "Aceita":
            continue
        regra = o["regra"]
        if o["tipo"] == "Atenção":  # preferências: junta dezembro e janeiro
            regra = regra.replace(" (Dez)", "").replace(" (Jan)", "")
        g = grupos.setdefault((o["tipo"], o["setor"], regra), [])
        g.append(o)
    ordem = {"Exceção": 0, "Atenção": 1}
    saida = []
    for (tipo, setor, regra), itens in sorted(grupos.items(), key=lambda kv: (ordem[kv[0][0]], kv[0][1])):
        pessoas = []
        for o in itens:
            if o["pessoa"] and o["pessoa"] not in pessoas and "/" not in o["pessoa"]:
                pessoas.append(o["pessoa"])
        datas = [o["data"] for o in itens if o["data"] and "/" in o["data"]]
        if tipo == "Exceção":
            detalhe = itens[0]["detalhe"]
        else:
            detalhe = "; ".join(f"{o['pessoa']}: {o['detalhe']}" for o in itens)
        saida.append({
            "tipo": "Pendência obrigatória" if tipo == "Exceção" else "Preferência não atendida",
            "setor": setor, "regra": regra,
            "pessoas": ", ".join(p for p in pessoas if p[0:2] not in ("0", "1", "2", "3")),
            "datas": ", ".join(dict.fromkeys(datas)),
            "detalhe": detalhe,
        })
    return saida
