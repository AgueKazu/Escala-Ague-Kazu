"""Monta as folgas e as dobras de cada setor.

Método: busca local (recozimento simulado). Para cada pessoa e cada semana
existe uma lista de combinações de folga possíveis (já respeitando as regras
fixas: domingos fixos, dias em que a pessoa não trabalha, folgas coletivas).
O programa troca combinações ao acaso e fica com as que diminuem a
"pontuação de problemas". Regras obrigatórias valem muitos pontos;
preferências valem poucos.
"""

import math
import random
from itertools import combinations

from modelo import (
    COLETIVA, DIAS, DOMINGO_3_JAN, DOMINGOS_POR_MES, FECHADO, JANELA_FIM_DE_ANO,
    META_COZINHA, MINIMO_SALAO, SEMANA_FIM_DE_ANO, SEMANAS, dia_aberto, eh_domingo,
)

N = len(DIAS)

# Pesos da pontuação
GRAVE = 1000
DOMINGO_ERRADO = 500
COBERTURA = 300
DOBRA_FALTANDO = 300


# ---------------------------------------------------------------------------
# Combinações de folga por semana
# ---------------------------------------------------------------------------
def forcadas_da_semana(p, semana):
    f = {i for i in semana if i in COLETIVA}
    f |= {i for i in semana if i in p.folgas_fixas}
    f |= {i for i in semana if DIAS[i].weekday() in p.dias_sem_trabalho and i not in FECHADO}
    f |= {i for i in semana if i in p.domingos_fixos}
    return f


def opcoes_da_semana(p, semana):
    forcadas = forcadas_da_semana(p, semana)
    livres = [
        i for i in semana
        if i not in FECHADO and i not in forcadas and i not in p.trabalho_fixo
        and not (eh_domingo(i) and p.domingos_fixos)
    ]
    if semana == SEMANA_FIM_DE_ANO:
        opcoes = [frozenset(forcadas)]
        if DOMINGO_3_JAN in livres:
            opcoes.append(frozenset(forcadas | {DOMINGO_3_JAN}))
        return opcoes
    k = max(0, 2 - len(forcadas))
    return [frozenset(forcadas | set(c)) for c in combinations(livres, k)]


def todas_forcadas(p):
    f = set()
    for s in SEMANAS:
        f |= forcadas_da_semana(p, s)
    return f


# ---------------------------------------------------------------------------
# Pontuação individual (depende só da pessoa)
# ---------------------------------------------------------------------------
def custo_pessoa(p, st, extra=None, forcadas=frozenset()):
    c = 0
    seguidos = 0
    for i in range(N):
        if st[i] == "W":
            seguidos += 1
            if seguidos > 5:
                c += GRAVE
        else:
            seguidos = 0
    for i in range(1, N):
        if st[i] == "F" and st[i - 1] == "F":
            if i in JANELA_FIM_DE_ANO and i - 1 in JANELA_FIM_DE_ANO:
                continue
            if i in forcadas and i - 1 in forcadas:
                continue
            c += 40
    if p.domingos_mes:
        for idx in DOMINGOS_POR_MES.values():
            folgas = [i for i in idx if st[i] == "F"]
            c += DOMINGO_ERRADO * abs(len(folgas) - p.domingos_mes)
            if p.domingos_mes == 2 and len(folgas) == 2 and folgas[1] - folgas[0] == 7:
                c += 20  # preferir domingos quinzenais
    if extra:
        c += extra(p, st)
    return c


# ---------------------------------------------------------------------------
# Pontuação diária de cada setor (depende de todos do setor naquele dia)
# ---------------------------------------------------------------------------
def custo_dia_dupla(pessoas, sts, i):
    """Bar e Sushi: um cobre o outro com dobra; os dois não podem folgar juntos."""
    if not dia_aberto(i):
        return 0
    return GRAVE if all(sts[p][i] == "F" for p in pessoas) else 0


def custo_dia_salao(pessoas, sts, i):
    if not dia_aberto(i):
        return 0
    c = 0
    por_nome = {p.nome: p for p in pessoas}
    no_salao = sum(1 for p in pessoas if p.turno == "salao" and sts[p][i] == "W")
    falta = max(0, MINIMO_SALAO - no_salao)
    peso = 200 if DIAS[i].weekday() >= 4 else 60  # sexta, sábado e domingo primeiro
    c += falta * peso
    for a, b in (("Elaine", "Marcos"), ("Adriano", "Guilherme")):
        if sts[por_nome[a]][i] == "F" and sts[por_nome[b]][i] == "F":
            c += GRAVE
    return c


def pode_dobrar_no_dia(p, i):
    return p.pode_dobrar and DIAS[i].weekday() not in p.sem_dobra_semana


def custo_dia_cozinha(pessoas, sts, i):
    if not dia_aberto(i):
        return 0
    c = 0
    manha = [p for p in pessoas if p.turno == "manha"]
    noite = [p for p in pessoas if p.turno == "noite"]
    folga_m = sum(1 for p in manha if sts[p][i] == "F")
    folga_n = sum(1 for p in noite if sts[p][i] == "F")
    if folga_m >= 3:
        c += GRAVE * (folga_m - 2)
    por_nome = {p.nome: p for p in pessoas}
    trio = [por_nome[n] for n in ("Rafael", "Miro", "Chef")]
    for a, b in combinations(trio, 2):
        if sts[a][i] == "F" and sts[b][i] == "F":
            c += 50
    if eh_domingo(i):
        c += 50 * max(0, folga_m + folga_n - 3)  # domingo é turno único, sem dobra
        return c
    cobre_manha = sum(1 for p in noite if sts[p][i] == "W" and pode_dobrar_no_dia(p, i))
    cobre_noite = sum(1 for p in manha if sts[p][i] == "W" and pode_dobrar_no_dia(p, i))
    c += DOBRA_FALTANDO * max(0, folga_m - cobre_manha)
    c += DOBRA_FALTANDO * max(0, folga_n - cobre_noite)
    c += 5 * (folga_m ** 2 + folga_n ** 2)  # espalhar as folgas ao longo da semana
    return c


def custo_dia_pia(pessoas, sts, i):
    if not dia_aberto(i):
        return 0
    folgas = sum(1 for p in pessoas if sts[p][i] == "F")
    if eh_domingo(i):
        return GRAVE if folgas == 3 else 0  # domingo: turno único, basta um
    return COBERTURA * max(0, folgas - 1)


def custo_dia_nenhum(pessoas, sts, i):
    return 0


# ---------------------------------------------------------------------------
# Regras individuais extras
# ---------------------------------------------------------------------------
def extra_marcos(p, st):
    return sum(30 for i in range(N) if st[i] == "F" and dia_aberto(i) and DIAS[i].weekday() in (0, 1))


def extra_miro(p, st):
    c = 0
    for mes in (12, 1):
        segundas = sum(1 for i in range(N)
                       if DIAS[i].month == mes and DIAS[i].weekday() == 0 and st[i] == "F" and dia_aberto(i))
        c += 200 * abs(segundas - 2)
    return c


def extra_joelma(rafael_st):
    def f(p, st):
        c = 0
        for i in range(N):
            if st[i] != "F" or not dia_aberto(i):
                continue
            if rafael_st[i] == "F":
                c += 200
            if DIAS[i].weekday() == 5:
                c += 30
        return c
    return f


EXTRAS = {("Salão", "Marcos"): extra_marcos, ("Cozinha", "Miro"): extra_miro}


# ---------------------------------------------------------------------------
# Busca
# ---------------------------------------------------------------------------
def status_de(escolhas):
    st = ["X" if i in FECHADO else "W" for i in range(N)]
    for s in escolhas:
        for i in s:
            st[i] = "F"
    return st


def resolver_setor(pessoas, custo_dia, extras=None, iteracoes=120000, tentativas=4, semente=7):
    extras = extras or {}
    opcoes = {p: [opcoes_da_semana(p, s) for s in SEMANAS] for p in pessoas}
    forcadas = {p: frozenset(todas_forcadas(p)) for p in pessoas}
    variaveis = [(p, w) for p in pessoas for w in range(len(SEMANAS)) if len(opcoes[p][w]) > 1]
    melhor_total, melhor = None, None

    for t in range(tentativas):
        rnd = random.Random(semente + t)
        esc = {p: [rnd.choice(o) for o in opcoes[p]] for p in pessoas}
        sts = {p: status_de(esc[p]) for p in pessoas}
        cp = {p: custo_pessoa(p, sts[p], extras.get(p), forcadas[p]) for p in pessoas}
        cd = [custo_dia(pessoas, sts, i) for i in range(N)]
        total = sum(cp.values()) + sum(cd)
        if not variaveis:
            melhor_total, melhor = total, esc
            break
        temp_ini, temp_fim = 300.0, 0.5
        for it in range(iteracoes):
            temp = temp_ini * (temp_fim / temp_ini) ** (it / iteracoes)
            p, w = rnd.choice(variaveis)
            atual = esc[p][w]
            nova = rnd.choice(opcoes[p][w])
            if nova == atual:
                continue
            semana = SEMANAS[w]
            antigo_st = sts[p][:]
            for i in semana:
                if i not in FECHADO:
                    sts[p][i] = "W"
            for i in nova:
                sts[p][i] = "F"
            novo_cp = custo_pessoa(p, sts[p], extras.get(p), forcadas[p])
            novos_cd = {i: custo_dia(pessoas, sts, i) for i in semana}
            delta = novo_cp - cp[p] + sum(novos_cd[i] - cd[i] for i in semana)
            if delta <= 0 or rnd.random() < math.exp(-delta / temp):
                esc[p][w] = nova
                cp[p] = novo_cp
                for i in semana:
                    cd[i] = novos_cd[i]
                total += delta
            else:
                sts[p] = antigo_st
        if melhor_total is None or total < melhor_total:
            melhor_total, melhor = total, {p: list(v) for p, v in esc.items()}
    return {p: status_de(melhor[p]) for p in pessoas}, melhor_total


# ---------------------------------------------------------------------------
# Códigos finais (T, F, X, B, D, M)
# ---------------------------------------------------------------------------
def codigos_basicos(st):
    cod = []
    for i, s in enumerate(st):
        if s == "X":
            cod.append("X")
        elif s == "F":
            cod.append("F")
        elif eh_domingo(i):
            cod.append("D")
        else:
            cod.append("T")
    return cod


def codigos_dupla(pessoas, sts):
    cods = {p: codigos_basicos(sts[p]) for p in pessoas}
    a, b = pessoas
    for i in range(N):
        if eh_domingo(i) or not dia_aberto(i):
            continue
        if sts[a][i] == "F" and sts[b][i] == "W":
            cods[b][i] = "B"
        elif sts[b][i] == "F" and sts[a][i] == "W":
            cods[a][i] = "B"
    return cods


def codigos_pia(pessoas, sts):
    ilma, claudia, daniel = pessoas
    cods = {p: codigos_basicos(sts[p]) for p in pessoas}
    for i in range(N):
        if eh_domingo(i) or not dia_aberto(i) or sts[daniel][i] != "W":
            continue
        fi, fc = sts[ilma][i] == "F", sts[claudia][i] == "F"
        if fi and fc:
            cods[daniel][i] = "B"
        elif fi:
            cods[daniel][i] = "M"
    return cods


def codigos_cozinha(pessoas, sts):
    """Distribui as dobras de forma proporcional ao peso de cada um."""
    cods = {p: codigos_basicos(sts[p]) for p in pessoas}
    manha = [p for p in pessoas if p.turno == "manha"]
    noite = [p for p in pessoas if p.turno == "noite"]
    dobras = {p: 0 for p in pessoas}
    for i in range(N):
        if eh_domingo(i) or not dia_aberto(i):
            continue
        for faltam_de, cobrem in ((manha, noite), (noite, manha)):
            faltas = sum(1 for p in faltam_de if sts[p][i] == "F")
            candidatos = [p for p in cobrem if sts[p][i] == "W" and pode_dobrar_no_dia(p, i)
                          and cods[p][i] == "T"]

            def ordem(p):
                ontem = 1 if i > 0 and cods[p][i - 1] == "B" else 0
                return (dobras[p] / p.peso_dobra + ontem * 0.75, p.nome)

            candidatos.sort(key=ordem)
            for p in candidatos[:faltas]:
                cods[p][i] = "B"
                dobras[p] += 1
    return cods


def montar_escala():
    """Devolve {setor: {pessoa: [códigos por dia]}} e a pontuação de cada setor."""
    escala, pontos = {}, {}
    from modelo import BAR, COZINHA, PIA, REFEITORIO, SALAO_EQUIPE, SUSHI

    for nome, pessoas in (("Bar", BAR), ("Sushi", SUSHI)):
        sts, pontos[nome] = resolver_setor(pessoas, custo_dia_dupla)
        escala[nome] = codigos_dupla(pessoas, sts)

    extras = {p: EXTRAS[(p.setor, p.nome)] for p in SALAO_EQUIPE if (p.setor, p.nome) in EXTRAS}
    sts, pontos["Salão"] = resolver_setor(SALAO_EQUIPE, custo_dia_salao, extras)
    escala["Salão"] = {p: codigos_basicos(sts[p]) for p in SALAO_EQUIPE}

    extras = {p: EXTRAS[(p.setor, p.nome)] for p in COZINHA if (p.setor, p.nome) in EXTRAS}
    sts_coz, pontos["Cozinha"] = resolver_setor(COZINHA, custo_dia_cozinha, extras, iteracoes=250000)
    escala["Cozinha"] = codigos_cozinha(COZINHA, sts_coz)

    sts, pontos["Pia"] = resolver_setor(PIA, custo_dia_pia)
    escala["Pia"] = codigos_pia(PIA, sts)

    rafael_coz = next(p for p in COZINHA if p.nome == "Rafael")
    joelma = REFEITORIO[0]
    sts, pontos["Refeitório"] = resolver_setor(
        REFEITORIO, custo_dia_nenhum, {joelma: extra_joelma(sts_coz[rafael_coz])})
    escala["Refeitório"] = {joelma: codigos_basicos(sts[joelma])}
    return escala, pontos
