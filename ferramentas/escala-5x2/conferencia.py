"""Confere a escala pronta, regra por regra, só a partir dos códigos finais.

Tipos de ocorrência:
- "Exceção": regra obrigatória ou meta não atendida (com o motivo).
- "Atenção": preferência não atendida.
- "Aceita": situação prevista pelas próprias regras.
"""

from itertools import combinations

from modelo import (
    COLETIVA, DIAS, DOMINGO_EXTRA, HORAS, META_COZINHA, MINIMO_SALAO, SEMANA_FINAL,
    SEMANAS, TODOS_DOMINGOS, dia_aberto, eh_domingo, horario_do_codigo,
)

TRABALHA = {"T", "B", "D", "M"}
FIM_DE_SEMANA = (4, 5, 6)


def fmt(i):
    return f"{DIAS[i]:%d/%m}"


def indicadores(p, cod):
    """Totalizadores individuais do período."""
    seguidos = maximo = 0
    for c in cod:
        seguidos = seguidos + 1 if c in TRABALHA else 0
        maximo = max(maximo, seguidos)
    return {
        "folgas": cod.count("F"),
        "dobras": cod.count("B"),
        "domingos": sum(1 for i in TODOS_DOMINGOS if cod[i] == "F"),
        "trabalhados": sum(1 for c in cod if c in TRABALHA),
        "feriados": cod.count("X"),
        "horas": sum(HORAS[horario_do_codigo(p, c)] for c in cod if c in TRABALHA),
        "max_seguidos": maximo,
    }


def cobertura(setor, pessoas):
    """Quantidade por turno em cada dia: {dia: {rótulo: (quantidade, meta)}}."""
    res = {}
    for i in range(len(DIAS)):
        if not dia_aberto(i):
            res[i] = None
            continue
        if setor == "Cozinha":
            manha = [p for p in pessoas if p.turno == "manha"]
            noite = [p for p in pessoas if p.turno == "noite"]
            m = sum(pessoas[p][i] in TRABALHA for p in manha) + sum(pessoas[p][i] == "B" for p in noite)
            n = sum(pessoas[p][i] in TRABALHA for p in noite) + sum(pessoas[p][i] == "B" for p in manha)
            res[i] = {"Manhã": (m, META_COZINHA["manha"]), "Noite": (n, META_COZINHA["noite"])}
        elif setor == "Salão":
            alm = sum(pessoas[p][i] in TRABALHA for p in pessoas)
            jan = sum(pessoas[p][i] in TRABALHA for p in pessoas if p.turno == "salao")
            res[i] = {"Almoço": (alm, MINIMO_SALAO), "Jantar": (jan, MINIMO_SALAO)}
        elif setor == "Refeitório":
            alm = sum(pessoas[p][i] in TRABALHA for p in pessoas)
            res[i] = {"Manhã": (alm, 1)}
        else:
            alm = jan = 0
            for p in pessoas:
                c = pessoas[p][i]
                txt = horario_do_codigo(p, c)
                alm += c in ("B", "D", "M") or (c == "T" and txt.startswith("08"))
                jan += c in ("B", "D") or (c == "T" and txt.startswith("13"))
            res[i] = {"Manhã": (alm, 1), "Noite": (jan, 1)}
    return res


def conferir(escala):
    oc = []

    def add(tipo, setor, pessoa, i, regra, detalhe):
        oc.append({"tipo": tipo, "setor": setor, "pessoa": pessoa,
                   "data": fmt(i) if i is not None else "", "regra": regra, "detalhe": detalhe})

    add("Aceita", "Todos", "Toda a equipe", None, "Datas coletivas",
        "30/11, 31/12 e 02/01 são folga de todos e contam como folga semanal; 25/12 e 01/01 fechado.")
    add("Aceita", "Todos", "", None, "Domingo",
        "Domingo é turno único (10:30–19:54), sem dobra; intervalo considerado de 1h nas horas.")
    add("Aceita", "Bar / Sushi / Cozinha / Pia", "", None, "Descanso de 11h entre jornadas",
        "Quem fez dobra (saída 23:00) não entra às 08:00 no dia seguinte: folga, nova dobra ou domingo.")
    add("Aceita", "Cozinha", "", None, "Horário da dobra",
        "A dobra começa às 11:45: conta na manhã a partir do almoço, mas não cobre das 08:00 às 11:45.")

    for setor, pessoas in escala.items():
        for p, cod in pessoas.items():
            nome = p.nome
            for s in SEMANAS:
                folgas = sum(cod[i] == "F" for i in s)
                if folgas == 2:
                    continue
                if s == SEMANA_FINAL and cod[DOMINGO_EXTRA] == "F" and folgas == 3 and not p.dias_sem_trabalho:
                    add("Aceita", setor, nome, DOMINGO_EXTRA, "Domingo complementar (03/01)",
                        "Folga em 03/01 como domingo de folga: 3ª folga da semana (exceção prevista).")
                elif p.dias_sem_trabalho and folgas > 2:
                    add("Aceita", setor, nome, s[0], "Folgas na semana",
                        f"{folgas} dias sem trabalho na semana de {fmt(s[0])}: ausências fixas + datas coletivas.")
                else:
                    add("Exceção", setor, nome, s[0], "Duas folgas por semana",
                        f"{folgas} folga(s) na semana de {fmt(s[0])} a {fmt(s[-1])}.")
            seguidos = 0
            for i, c in enumerate(cod):
                seguidos = seguidos + 1 if c in TRABALHA else 0
                if seguidos == 6:
                    add("Exceção", setor, nome, i, "Máximo de 5 dias seguidos", "6º dia seguido.")
            for i in range(len(DIAS) - 1):
                if cod[i] == "F" and cod[i + 1] == "F":
                    fixo = {DIAS[i].weekday(), DIAS[i + 1].weekday()} <= p.dias_sem_trabalho
                    if fixo or (i in COLETIVA and i + 1 in COLETIVA):
                        continue
                    tipo = "Aceita" if i + 1 == DOMINGO_EXTRA else "Atenção"
                    add(tipo, setor, nome, i + 1, "Evitar folgas seguidas", f"Folga em {fmt(i)} e {fmt(i + 1)}.")
                # Descanso de 11h
                if cod[i] in ("B",) or (cod[i] == "T" and p.horario.startswith("13")):
                    entra_8 = cod[i + 1] == "M" or (cod[i + 1] == "T" and p.horario.startswith("08"))
                    if entra_8 and not eh_domingo(i + 1):
                        add("Exceção", setor, nome, i + 1, "Descanso de 11h", "Entrada às 08:00 após saída tarde.")
            q = p.domingos_de_folga
            folgas_dom = [i for i in TODOS_DOMINGOS if cod[i] == "F"]
            if q is None:
                add("Aceita", setor, nome, None, "Domingos", "Não trabalha aos domingos (ausência fixa).")
            elif len(folgas_dom) != q:
                motivo = ""
                if nome == "Moura":
                    motivo = " Já folga seg e ter fixo; um domingo daria 3 folgas na semana."
                add("Exceção", setor, nome, None, "Domingos de folga",
                    f"{len(folgas_dom)} domingo(s) de folga; o certo é {q}.{motivo}")
            elif q == 2 and folgas_dom[1] - folgas_dom[0] != 14:
                add("Atenção", setor, nome, None, "Domingos quinzenais",
                    f"Domingos {fmt(folgas_dom[0])} e {fmt(folgas_dom[1])} não são quinzenais.")
            for i in p.domingos_fixos + p.folgas_fixas:
                if cod[i] != "F":
                    add("Exceção", setor, nome, i, "Folga fixa/obrigatória", "Deveria folgar neste dia.")
            for i in p.evitar_folga:
                if cod[i] == "F":
                    add("Atenção", setor, nome, i, "Evitar folga nesta data", "Folga numa data a evitar.")
            for i, c in enumerate(cod):
                if not dia_aberto(i):
                    continue
                if c in TRABALHA and DIAS[i].weekday() in p.dias_sem_trabalho:
                    add("Exceção", setor, nome, i, "Dia sem trabalho", "Escalado num dia de ausência fixa.")
                if c == "B" and (not p.pode_dobrar or DIAS[i].weekday() in p.sem_dobra_semana):
                    add("Exceção", setor, nome, i, "Dobra não permitida", "Escalado para dobra.")
                if c == "F" and DIAS[i].weekday() in p.evitar_dias_semana:
                    add("Atenção", setor, nome, i, "Evitar folga neste dia da semana", "Folga num dia a evitar.")

    def juntos(setor, a, b, regra, tipo="Exceção"):
        pa = next(p for p in escala[setor[0]] if p.nome == a)
        pb = next(p for p in escala[setor[1]] if p.nome == b)
        for i in range(len(DIAS)):
            if dia_aberto(i) and escala[setor[0]][pa][i] == "F" and escala[setor[1]][pb][i] == "F":
                add(tipo, setor[0], f"{a} e {b}", i, regra, "Folga no mesmo dia.")

    juntos(("Bar", "Bar"), "Rafael", "Vinicius", "Bar sem cobertura")
    juntos(("Sushi", "Sushi"), "Diogo", "Allan", "Sushi sem cobertura")
    juntos(("Salão", "Salão"), "Elaine", "Marcos", "Não folgar juntos")
    juntos(("Salão", "Salão"), "Adriano", "Guilherme", "Não folgar juntos")
    for a, b in combinations(("Rafael", "Miro", "Chef"), 2):
        juntos(("Cozinha", "Cozinha"), a, b, "Responsáveis folgando juntos")
    juntos(("Cozinha", "Cozinha"), "Rafael", "Felix", "Não folgar juntos")
    juntos(("Refeitório", "Cozinha"), "Joelma", "Rafael", "Não folgar junto com Rafael (cozinha)")
    juntos(("Pia", "Pia"), "Ilma", "Claudia", "Evitar folga no mesmo dia", "Atenção")
    juntos(("Pia", "Pia"), "Daniel", "Ilma", "Daniel não folga com Ilma")
    juntos(("Pia", "Pia"), "Daniel", "Claudia", "Daniel não folga com Claudia")

    coz = escala["Cozinha"]
    miro = next(p for p in coz if p.nome == "Miro")
    seg = [i for i in range(len(DIAS)) if DIAS[i].weekday() == 0 and DIAS[i].month == 12 and dia_aberto(i)]
    n = sum(coz[miro][i] == "F" for i in seg)
    if n != 2:
        add("Exceção", "Cozinha", "Miro", None, "Duas segundas de folga", f"{n} segunda(s) de folga em dezembro.")

    manha = [p for p in coz if p.turno == "manha"]
    for i in range(len(DIAS)):
        if dia_aberto(i):
            k = sum(coz[p][i] == "F" for p in manha)
            if k >= 3:
                add("Exceção", "Cozinha", "Turno da manhã", i, "Máximo de 2 da manhã de folga",
                    f"{k} da manhã sem trabalhar (contando Edna/Moura). "
                    + ("Domingo: Edna nunca trabalha e 6 homens da manhã precisam de domingo."
                       if eh_domingo(i) else "Semana do Natal: 14 folgas da manhã para 6 dias abertos."))

    for setor, pessoas in escala.items():
        for i, turnos in cobertura(setor, pessoas).items():
            if not turnos:
                continue
            for rotulo, (qtd, meta) in turnos.items():
                if qtd >= meta:
                    continue
                fim = DIAS[i].weekday() in FIM_DE_SEMANA
                if setor == "Cozinha":
                    detalhe = f"{qtd} de {meta} (déficit de {meta - qtd})."
                    if eh_domingo(i):
                        detalhe += " Domingo é turno único, sem dobra."
                    add("Exceção", setor, rotulo, i, f"Meta da {rotulo.lower()}", detalhe)
                elif setor == "Salão":
                    detalhe = f"{qtd} no {rotulo.lower()} (mínimo {meta})."
                    if eh_domingo(i):
                        detalhe += " Domingos: 9 folgas de domingo no jantar para 4 domingos."
                    add("Exceção" if fim else "Atenção", setor, rotulo, i, "Mínimo de 5 no salão", detalhe)
                elif setor != "Refeitório":  # folgas da Joelma: responsável listado abaixo
                    add("Exceção", setor, rotulo, i, "Turno descoberto", "Ninguém no turno.")

    jo = next(iter(escala["Refeitório"]))
    folgas_jo = [fmt(i) for i in range(len(DIAS)) if dia_aberto(i) and escala["Refeitório"][jo][i] == "F"]
    add("Atenção", "Refeitório", "Joelma", None, "Responsável nas folgas da Joelma",
        "Definir quem cobre o refeitório em: " + ", ".join(folgas_jo) + ".")
    return oc


ORDEM = {"Exceção": 0, "Atenção": 1, "Aceita": 2}
