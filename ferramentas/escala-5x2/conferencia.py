"""Confere a escala pronta contra as regras e lista cada ocorrência.

Trabalha só com os códigos finais (T, F, X, B, D, M), sem depender do
otimizador, para servir de auditoria independente.

Tipos:
- "Exceção": regra obrigatória não atendida.
- "Atenção": preferência não atendida (ex.: folgas seguidas, sábado).
- "Aceita": situação prevista pelas próprias regras (ex.: Edna nos fins de semana).
"""

from itertools import combinations

from modelo import (
    COLETIVA, DIAS, DOMINGOS_POR_MES, FECHADO, JANELA_FIM_DE_ANO, META_COZINHA,
    MINIMO_SALAO, SEMANA_FIM_DE_ANO, SEMANAS, dia_aberto, eh_domingo,
)

TRABALHA = {"T", "B", "D", "M"}


def fmt(i):
    return DIAS[i].strftime("%d/%m")


def conferir(escala):
    oc = []

    def add(tipo, setor, pessoa, i, regra, detalhe):
        oc.append({"tipo": tipo, "setor": setor, "pessoa": pessoa,
                   "data": fmt(i) if i is not None else "", "regra": regra, "detalhe": detalhe})

    # Situações aceitas pela própria regra
    add("Aceita", "Todos", "Toda a equipe", None, "Folgas coletivas",
        "30/11, 31/12 e 02/01 são folgas de toda a equipe, sem cobertura operacional.")
    add("Aceita", "Cozinha / Bar / Sushi / Pia", "", None, "Horário da dobra",
        "A dobra começa às 11h45 e não cobre o início do turno da manhã (08h00).")
    add("Aceita", "Todos", "", None, "Domingos",
        "Domingo é turno único (10h30–19h54), sem dobra.")

    for setor, pessoas in escala.items():
        for p, cod in pessoas.items():
            nome = p.nome
            # Folgas por semana
            for s in SEMANAS:
                folgas = sum(1 for i in s if cod[i] == "F")
                if folgas == 2:
                    continue
                if s == SEMANA_FIM_DE_ANO and folgas == 3 and cod[s[-1]] == "F" and not p.dias_sem_trabalho:
                    add("Aceita", setor, nome, s[-1], "Folga extra de fim de ano",
                        "Folga no domingo 03/01, contada como domingo de folga de janeiro.")
                    continue
                if p.dias_sem_trabalho and folgas > 2:
                    add("Aceita", setor, nome, s[0], "Folgas na semana",
                        f"{folgas} dias sem trabalho na semana por causa dos dias fixos de ausência.")
                    continue
                add("Exceção", setor, nome, s[0], "Folgas na semana",
                    f"{folgas} folga(s) na semana de {fmt(s[0])} a {fmt(s[-1])} (o certo são 2).")
            # Dias seguidos
            seguidos = 0
            for i in range(len(DIAS)):
                seguidos = seguidos + 1 if cod[i] in TRABALHA else 0
                if seguidos == 6:
                    add("Exceção", setor, nome, i, "Máximo de 5 dias seguidos", "6º dia seguido de trabalho.")
            # Folgas seguidas
            for i in range(1, len(DIAS)):
                if cod[i] == "F" and cod[i - 1] == "F":
                    if i in JANELA_FIM_DE_ANO and i - 1 in JANELA_FIM_DE_ANO:
                        continue
                    fixo = {DIAS[i].weekday(), DIAS[i - 1].weekday()} <= p.dias_sem_trabalho
                    if fixo:
                        continue
                    add("Atenção", setor, nome, i, "Evitar folgas seguidas",
                        f"Folga em {fmt(i - 1)} e {fmt(i)}.")
            # Domingos
            if p.domingos_mes:
                for mes, idx in DOMINGOS_POR_MES.items():
                    folgas = [i for i in idx if cod[i] == "F"]
                    if len(folgas) != p.domingos_mes:
                        add("Exceção", setor, nome, None, f"Domingos de folga ({mes})",
                            f"{len(folgas)} domingo(s) de folga; o certo é {p.domingos_mes}.")
                    elif p.domingos_mes == 2 and folgas[1] - folgas[0] == 7:
                        add("Atenção", setor, nome, None, f"Domingos quinzenais ({mes})",
                            f"Domingos seguidos: {fmt(folgas[0])} e {fmt(folgas[1])}.")
            elif p.dias_sem_trabalho:
                add("Aceita", setor, nome, None, "Domingos",
                    "Não trabalha aos domingos: folga todos os domingos do mês.")
            for i in p.domingos_fixos:
                if cod[i] != "F":
                    add("Exceção", setor, nome, i, "Domingo fixo", "Deveria folgar neste domingo.")
            for i in p.folgas_fixas:
                if cod[i] != "F":
                    add("Exceção", setor, nome, i, "Folga obrigatória", "Deveria folgar neste dia.")
            for i in p.trabalho_fixo:
                if cod[i] not in TRABALHA:
                    add("Exceção", setor, nome, i, "Trabalho obrigatório", "Deveria trabalhar neste dia.")
            for i in range(len(DIAS)):
                if DIAS[i].weekday() in p.dias_sem_trabalho and cod[i] in TRABALHA:
                    add("Exceção", setor, nome, i, "Dia sem trabalho", "Escalado num dia em que não trabalha.")
                if cod[i] == "B" and (not p.pode_dobrar and setor == "Cozinha"):
                    add("Exceção", setor, nome, i, "Não faz dobra", "Escalado para dobra.")
                if cod[i] == "B" and DIAS[i].weekday() in p.sem_dobra_semana:
                    add("Exceção", setor, nome, i, "Sem dobra neste dia da semana", "Escalado para dobra.")

    # Miro: duas segundas de folga por mês
    miro = next(p for p in escala["Cozinha"] if p.nome == "Miro")
    for mes, rotulo in ((12, "Dez"), (1, "Jan")):
        seg = sum(1 for i in range(len(DIAS)) if DIAS[i].month == mes and DIAS[i].weekday() == 0
                  and dia_aberto(i) and escala["Cozinha"][miro][i] == "F")
        if seg != 2:
            add("Exceção", "Cozinha", "Miro", None, f"Duas segundas de folga ({rotulo})",
                f"{seg} segunda(s) de folga.")

    # Regras por setor, dia a dia
    for i in range(len(DIAS)):
        if not dia_aberto(i):
            continue
        for setor in ("Bar", "Sushi"):
            ps = list(escala[setor])
            if all(escala[setor][p][i] == "F" for p in ps):
                add("Exceção", setor, "", i, "Cobertura diária", "Os dois de folga no mesmo dia.")

        sal = escala["Salão"]
        por = {p.nome: p for p in sal}
        n = sum(1 for p in sal if p.turno == "salao" and sal[p][i] in TRABALHA)
        if n < MINIMO_SALAO:
            fim = DIAS[i].weekday() >= 4
            add("Exceção" if fim else "Atenção", "Salão", "", i, "Mínimo de 5 no salão",
                f"{n} no salão (sem contar Juliana)" + ("; sexta a domingo é prioridade." if fim else "; redução de seg a qui."))
        for a, b in (("Elaine", "Marcos"), ("Adriano", "Guilherme")):
            if sal[por[a]][i] == "F" and sal[por[b]][i] == "F":
                add("Exceção", "Salão", f"{a} e {b}", i, "Não folgar juntos", "Folga no mesmo dia.")
        if sal[por["Marcos"]][i] == "F" and DIAS[i].weekday() in (0, 1):
            add("Atenção", "Salão", "Marcos", i, "Evitar folga seg/ter", "Folga numa segunda ou terça.")

        coz = escala["Cozinha"]
        cp = {p.nome: p for p in coz}
        manha = [p for p in coz if p.turno == "manha"]
        noite = [p for p in coz if p.turno == "noite"]
        folga_m = sum(1 for p in manha if coz[p][i] == "F")
        if folga_m >= 3:
            add("Exceção", "Cozinha", "", i, "Máximo de 2 da manhã de folga", f"{folga_m} da manhã de folga.")
        for a, b in combinations(("Rafael", "Miro", "Chef"), 2):
            if coz[cp[a]][i] == "F" and coz[cp[b]][i] == "F":
                add("Atenção", "Cozinha", f"{a} e {b}", i, "Evitar folga junto (Rafael, Miro, Chef)",
                    "Folga no mesmo dia.")
        if not eh_domingo(i):
            em = sum(1 for p in manha if coz[p][i] in ("T", "B")) + sum(1 for p in noite if coz[p][i] == "B")
            en = sum(1 for p in noite if coz[p][i] in ("T", "B")) + sum(1 for p in manha if coz[p][i] == "B")
            if em < META_COZINHA["manha"]:
                add("Exceção", "Cozinha", "", i, "Meta da manhã (7)", f"{em} pessoas na manhã.")
            if en < META_COZINHA["noite"]:
                add("Exceção", "Cozinha", "", i, "Meta da noite (6)", f"{en} pessoas na noite.")

        pia = escala["Pia"]
        folgas = [p.nome for p in pia if pia[p][i] == "F"]
        if len(folgas) == 3 or (len(folgas) == 2 and not eh_domingo(i)):
            add("Exceção", "Pia", " e ".join(folgas), i, "Evitar folgas simultâneas",
                "Turno descoberto ou dobra necessária.")

        jo = next(iter(escala["Refeitório"].items()))
        if jo[1][i] == "F":
            if coz[cp["Rafael"]][i] == "F":
                add("Exceção", "Refeitório", "Joelma", i, "Não folgar junto com Rafael (cozinha)",
                    "Folga no mesmo dia.")
            if DIAS[i].weekday() == 5:
                add("Atenção", "Refeitório", "Joelma", i, "Evitar folga no sábado", "Folga num sábado.")
    return oc
