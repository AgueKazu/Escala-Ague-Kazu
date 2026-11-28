"""Gera a planilha Excel: 01 Resumo geral, 02 a 07 setores, 08 Regras.

As cores das células vêm de formatação condicional pelo texto ("Folga",
"Dobra", "Fechado"): se alguém trocar uma célula na mão, a cor e os
totalizadores (fórmulas) acompanham.
"""

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

from conferencia import ORDEM, cobertura, indicadores
from modelo import (
    COLETIVA, DATAS_ESPECIAIS, DIAS, DOBRA, DOMINGO, FECHADO, HORAS, MANHA, NOITE,
    PERIODO, SALAO, TURNOS, dia_aberto, eh_domingo, horario_do_codigo, rotulo_data,
)

COR = {
    "cinza": "D9D9D9",
    "branco": "FFFFFF",
    "folga": "F28B82",
    "fechado": "A8D5A2",
    "dobra": "FDB863",
    "domingo": "F8C8DC",
    "domingo_claro": "FDEAF2",
    "titulo": "1F3864",
    "alerta": "FFC7CE",
    "total": "EDEDED",
}
LEGENDA = [
    ("cinza", "Datas e dias da semana"),
    ("branco", "Dia normal de trabalho"),
    ("folga", "Folga"),
    ("fechado", "Feriado / restaurante fechado"),
    ("dobra", f"Dobra ({DOBRA})"),
    ("domingo", f"Domingo ({DOMINGO})"),
]
TOTAIS = [
    "Total de folgas", "Total de dobras", "Domingos de folga", "Dias trabalhados",
    "Feriados (fechado)", "Horas trabalhadas", "Máx. dias consecutivos",
]
ABAS = {"Bar": "02 – Bar", "Sushi": "03 – Sushi", "Salão": "04 – Salão",
        "Cozinha": "05 – Cozinha", "Pia": "06 – Pia", "Refeitório": "07 – Refeitório"}

fino = Side(style="thin", color="A6A6A6")
grosso = Side(style="medium", color="404040")
BORDA = Border(left=fino, right=fino, top=fino, bottom=fino)
CENTRO = Alignment(horizontal="center", vertical="center", wrap_text=True)
ESQ = Alignment(horizontal="left", vertical="center", wrap_text=True)


def cor(nome):
    c = COR[nome]
    return PatternFill("solid", start_color=c, end_color=c)


def celula(ws, r, c, valor=None, negrito=False, fundo=None, alinhar=CENTRO, tam=10, borda=True, fmt=None):
    cel = ws.cell(row=r, column=c, value=valor)
    cel.font = Font(bold=negrito, size=tam)
    cel.alignment = alinhar
    if fundo:
        cel.fill = cor(fundo)
    if borda:
        cel.border = BORDA
    if fmt:
        cel.number_format = fmt
    return cel


def legenda(ws, linha, col_ini):
    for k, (c, txt) in enumerate(LEGENDA):
        celula(ws, linha, col_ini + 2 * k, "", fundo=c)
        celula(ws, linha, col_ini + 2 * k + 1, txt, alinhar=ESQ, tam=8, borda=False)


def observacao_do_dia(setor, pessoas, i):
    obs = []
    if i in FECHADO:
        obs.append("Restaurante fechado")
    elif i in COLETIVA:
        obs.append("Folga coletiva")
    if eh_domingo(i) and i == len(DIAS) - 1:
        obs.append("Domingo complementar")
    if setor == "Pia" and dia_aberto(i):
        cod = {p.nome: c[i] for p, c in pessoas.items()}
        if cod["Daniel"] == "M":
            obs.append("Daniel cobre a manhã (Ilma de folga)")
        elif cod["Claudia"] == "F" and not eh_domingo(i):
            obs.append("Daniel cobre a noite (Claudia de folga)")
    if setor == "Refeitório" and dia_aberto(i):
        if any(c[i] == "F" for c in pessoas.values()):
            obs.append("Folga da Joelma: definir responsável")
    if setor in ("Bar", "Sushi") and dia_aberto(i) and not eh_domingo(i):
        for p, c in pessoas.items():
            if c[i] == "B":
                obs.append(f"{p.nome} cobre os dois turnos")
    return " · ".join(obs)


def aba_setor(wb, setor, pessoas, totais_ref):
    ws = wb.create_sheet(ABAS[setor])
    lista = list(pessoas)
    n = len(lista)
    c0 = 2  # primeira coluna de colaborador
    cob = cobertura(setor, pessoas)
    rotulos_cob = next(t for t in cob.values() if t).keys()
    c_cob = c0 + n
    col_obs = c_cob + len(rotulos_cob) + (len(rotulos_cob) if setor == "Cozinha" else 0)
    ultima_col = col_obs

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ultima_col)
    t = ws.cell(row=1, column=1, value=f"{setor.upper()} · Escala 5x2 · {PERIODO}")
    t.font = Font(bold=True, size=15, color=COR["titulo"])
    legenda(ws, 2, 1)

    r_grupo, r_nome, r_hor = 3, 4, 5
    primeira = r_hor + 1
    ultima = primeira + len(DIAS) - 1

    # Cabeçalho
    for r in (r_nome, r_hor):
        celula(ws, r, 1, "Data" if r == r_nome else "", negrito=True, fundo="cinza")
    if setor == "Cozinha":
        manha = [k for k, p in enumerate(lista) if p.turno == "manha"]
        noite = [k for k, p in enumerate(lista) if p.turno == "noite"]
        for nome_g, ks in (("Turno da manhã", manha), ("Turno da noite", noite)):
            ws.merge_cells(start_row=r_grupo, start_column=c0 + ks[0], end_row=r_grupo, end_column=c0 + ks[-1])
            celula(ws, r_grupo, c0 + ks[0], nome_g, negrito=True, fundo="cinza")
    for k, p in enumerate(lista):
        c = c0 + k
        celula(ws, r_nome, c, p.nome, negrito=True, fundo="cinza", tam=11)
        celula(ws, r_hor, c, f"{TURNOS[p.turno]}\n{p.horario}", fundo="cinza", tam=8)
        ws.column_dimensions[L(c)].width = 12.5

    cab_cob = []
    for rot in rotulos_cob:
        meta = next(t for t in cob.values() if t)[rot][1]
        cab_cob.append((rot, f"mín. {meta}" if setor != "Cozinha" else f"meta {meta}"))
    if setor == "Cozinha":
        cab_cob += [("Déficit manhã", ""), ("Déficit noite", "")]
    for k, (rot, sub) in enumerate(cab_cob):
        celula(ws, r_nome, c_cob + k, rot, negrito=True, fundo="cinza", tam=9)
        celula(ws, r_hor, c_cob + k, sub, fundo="cinza", tam=8)
        ws.column_dimensions[L(c_cob + k)].width = 9
    celula(ws, r_nome, col_obs, "Observação", negrito=True, fundo="cinza")
    celula(ws, r_hor, col_obs, "", fundo="cinza")
    ws.column_dimensions[L(col_obs)].width = 34
    ws.column_dimensions["A"].width = 16
    ws.row_dimensions[r_hor].height = 26

    # Dias
    faixa_m = faixa_n = None
    if setor == "Cozinha":
        faixa_m = (L(c0 + manha[0]), L(c0 + manha[-1]))
        faixa_n = (L(c0 + noite[0]), L(c0 + noite[-1]))
    for i in range(len(DIAS)):
        r = primeira + i
        dom = eh_domingo(i)
        celula(ws, r, 1, rotulo_data(i), negrito=True, fundo="domingo" if dom else "cinza", tam=9)
        for k, p in enumerate(lista):
            celula(ws, r, c0 + k, horario_do_codigo(p, pessoas[p][i]), tam=9,
                   fundo="domingo_claro" if dom else None)
        pc, uc = L(c0), L(c0 + n - 1)
        for k, (rot, _) in enumerate(cab_cob):
            c = c_cob + k
            if not dia_aberto(i):
                celula(ws, r, c, "—", tam=9, fundo="total")
                continue
            if setor == "Cozinha":
                fm = f"{faixa_m[0]}{r}:{faixa_m[1]}{r}"
                fn = f"{faixa_n[0]}{r}:{faixa_n[1]}{r}"
                if rot == "Manhã":
                    f = f'=SUMPRODUCT(({fm}<>"Folga")*({fm}<>"Fechado"))+COUNTIF({fn},"Dobra")'
                elif rot == "Noite":
                    f = f'=SUMPRODUCT(({fn}<>"Folga")*({fn}<>"Fechado"))+COUNTIF({fm},"Dobra")'
                elif rot == "Déficit manhã":
                    f = f"=MAX(0,7-{L(c_cob)}{r})"
                else:
                    f = f"=MAX(0,6-{L(c_cob + 1)}{r})"
            elif setor == "Salão":
                faixa = f"{pc}{r}:{uc}{r}" if rot == "Almoço" else f"{L(c0 + 1)}{r}:{uc}{r}"
                f = f'=SUMPRODUCT(({faixa}<>"Folga")*({faixa}<>"Fechado"))'
            else:
                faixa = f"{pc}{r}:{uc}{r}"
                turno = MANHA if rot == "Manhã" else NOITE
                f = (f'=COUNTIF({faixa},"{turno}")+COUNTIF({faixa},"Dobra")'
                     f'+COUNTIF({faixa},"{DOMINGO}")')
            celula(ws, r, c, f, negrito=True, tam=9, fundo="total")
        celula(ws, r, col_obs, observacao_do_dia(setor, pessoas, i), alinhar=ESQ, tam=8)
        if DIAS[i].weekday() == 0:  # linha mais grossa no início de cada semana
            for c in range(1, ultima_col + 1):
                b = ws.cell(row=r, column=c).border
                ws.cell(row=r, column=c).border = Border(left=b.left, right=b.right, top=grosso, bottom=b.bottom)

    # Cores condicionais (acompanham edição manual)
    area = f"{L(c0)}{primeira}:{L(c0 + n - 1)}{ultima}"
    for txt, c in (("Folga", "folga"), ("Dobra", "dobra"), ("Fechado", "fechado")):
        ws.conditional_formatting.add(area, CellIsRule(operator="equal", formula=[f'"{txt}"'],
                                                       fill=cor(c), font=Font(bold=True)))
    alerta = dict(fill=cor("alerta"), font=Font(bold=True, color="9C0006"))
    for k, (rot, _) in enumerate(cab_cob):
        col = L(c_cob + k)
        faixa = f"{col}{primeira}:{col}{ultima}"
        if rot.startswith("Déficit"):
            regra = f'AND(ISNUMBER({col}{primeira}),{col}{primeira}>0)'
        else:
            meta = next(t for t in cob.values() if t)[rot][1]
            regra = f'AND(ISNUMBER({col}{primeira}),{col}{primeira}<{meta})'
        ws.conditional_formatting.add(faixa, FormulaRule(formula=[regra], **alerta))

    # Colunas auxiliares (ocultas) para os dias consecutivos
    aux0 = ultima_col + 2
    for k in range(n):
        col_aux, col_esc = L(aux0 + k), L(c0 + k)
        for i in range(len(DIAS)):
            r = primeira + i
            ant = f"{col_aux}{r - 1}" if i else "0"
            ws.cell(row=r, column=aux0 + k,
                    value=f'=IF(OR({col_esc}{r}="Folga",{col_esc}{r}="Fechado",{col_esc}{r}=""),0,{ant}+1)')
        ws.column_dimensions[col_aux].hidden = True

    # Totalizadores
    r_tot = ultima + 2
    celula(ws, r_tot - 1, 1, "Totalizadores do período", negrito=True, alinhar=ESQ, borda=False)
    datas = f"$A${primeira}:$A${ultima}"
    for j, rot in enumerate(TOTAIS):
        r = r_tot + j
        celula(ws, r, 1, rot, negrito=True, fundo="cinza", tam=8, alinhar=ESQ)
        for k, p in enumerate(lista):
            col = L(c0 + k)
            faixa = f"{col}${primeira}:{col}${ultima}"
            formulas = [
                f'=COUNTIF({faixa},"Folga")',
                f'=COUNTIF({faixa},"Dobra")',
                f'=COUNTIFS({datas},"*DOM",{faixa},"Folga")',
                f'=ROWS({faixa})-COUNTIF({faixa},"Folga")-COUNTIF({faixa},"Fechado")',
                f'=COUNTIF({faixa},"Fechado")',
                "=(" + "+".join(f'COUNTIF({faixa},"{h}")*{v}' for h, v in HORAS.items()) + ")/24",
                f"=MAX({L(aux0 + k)}{primeira}:{L(aux0 + k)}{ultima})",
            ]
            celula(ws, r, c0 + k, formulas[j], negrito=True, fundo="total",
                   fmt="[h]:mm" if j == 5 else None)
            totais_ref[(setor, p.nome, j)] = f"='{ws.title}'!{col}{r}"
        ws.conditional_formatting.add(
            f"{L(c0)}{r_tot + 6}:{L(c0 + n - 1)}{r_tot + 6}",
            CellIsRule(operator="greaterThan", formula=["5"], **alerta))

    ws.freeze_panes = ws.cell(row=primeira, column=c0)
    ws.print_area = f"A1:{L(ultima_col)}{r_tot + len(TOTAIS) - 1}"
    ws.print_title_rows = f"{r_nome}:{r_hor}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins.left = ws.page_margins.right = 0.3
    ws.page_margins.top = ws.page_margins.bottom = 0.4
    ws.oddHeader.center.text = f"{setor} · Escala 5x2 · {PERIODO}"
    ws.oddFooter.right.text = "Página &P de &N"
    return ws


def aba_resumo(wb, escala, totais_ref, ocorrencias):
    ws = wb.create_sheet("01 – Resumo geral", 0)
    ws.merge_cells("A1:K1")
    ws["A1"] = f"Resumo geral · Escala 5x2 · {PERIODO}"
    ws["A1"].font = Font(bold=True, size=15, color=COR["titulo"])
    ws["A2"] = ("Os números individuais vêm das abas de cada setor por fórmula. "
                "Valores em horas consideram 1h de intervalo no domingo (ainda a definir).")
    ws["A2"].font = Font(italic=True, size=9, color="595959")

    # Indicadores por setor
    r = 4
    cab = ["Setor", "Colaboradores", "Folgas", "Dobras", "Horas previstas", "Dias com turno abaixo do mínimo"]
    for c, txt in enumerate(cab, 1):
        celula(ws, r, c, txt, negrito=True, fundo="cinza")
    r += 1
    for setor, pessoas in escala.items():
        ind = [indicadores(p, c) for p, c in pessoas.items()]
        dias_baixo = sum(1 for t in cobertura(setor, pessoas).values()
                         if t and any(q < m for q, m in t.values())) if setor != "Refeitório" else 0
        vals = [setor, len(pessoas), sum(x["folgas"] for x in ind), sum(x["dobras"] for x in ind),
                round(sum(x["horas"] for x in ind), 1), dias_baixo]
        for c, v in enumerate(vals, 1):
            celula(ws, r, c, v, negrito=c == 1, alinhar=ESQ if c == 1 else CENTRO)
        r += 1
    celula(ws, r, 1, "Total", negrito=True, fundo="total", alinhar=ESQ)
    for c in range(2, 7):
        celula(ws, r, c, f"=SUM({L(c)}5:{L(c)}{r - 1})", negrito=True, fundo="total")
    r += 2

    # Indicadores individuais
    celula(ws, r, 1, "Indicadores individuais", negrito=True, alinhar=ESQ, borda=False, tam=12)
    r += 1
    cab = ["Setor", "Colaborador", "Turno"] + TOTAIS
    for c, txt in enumerate(cab, 1):
        celula(ws, r, c, txt, negrito=True, fundo="cinza", tam=9)
    ws.row_dimensions[r].height = 30
    r += 1
    ini = r
    for setor, pessoas in escala.items():
        for p in pessoas:
            celula(ws, r, 1, setor, alinhar=ESQ)
            celula(ws, r, 2, p.nome, negrito=True, alinhar=ESQ)
            celula(ws, r, 3, TURNOS[p.turno])
            for j in range(len(TOTAIS)):
                celula(ws, r, 4 + j, totais_ref[(setor, p.nome, j)], fmt="[h]:mm" if j == 5 else None,
                       fundo="dobra" if j == 1 else None)
            r += 1
    ws.conditional_formatting.add(f"J{ini}:J{r - 1}", CellIsRule(
        operator="greaterThan", formula=["5"], fill=cor("alerta"), font=Font(bold=True, color="9C0006")))
    r += 1

    # Pontos de atenção
    celula(ws, r, 1, "Conferência das regras (exceções e pontos de atenção)", negrito=True,
           alinhar=ESQ, borda=False, tam=12)
    r += 1
    for c, txt in enumerate(["Tipo", "Setor", "Colaborador / turno", "Data", "Regra", "Detalhe"], 1):
        celula(ws, r, c, txt, negrito=True, fundo="cinza")
    ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=11)
    r += 1
    cores_tipo = {"Exceção": "alerta", "Atenção": "dobra", "Aceita": "fechado"}
    for o in sorted(ocorrencias, key=lambda o: ORDEM[o["tipo"]]):
        for c, k in enumerate(("tipo", "setor", "pessoa", "data", "regra", "detalhe"), 1):
            celula(ws, r, c, o[k], alinhar=ESQ, tam=9, fundo=cores_tipo[o["tipo"]] if c == 1 else None)
        ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=11)
        ws.row_dimensions[r].height = 26 if len(o["detalhe"]) > 70 else 15
        r += 1
    for col, w in zip("ABCDEFGHIJK", (12, 14, 14, 10, 24, 12, 12, 12, 11, 11, 12)):
        ws.column_dimensions[col].width = w
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def aba_regras(wb, escala):
    ws = wb.create_sheet("08 – Regras")
    ws["A1"] = f"Regras da escala 5x2 · {PERIODO}"
    ws["A1"].font = Font(bold=True, size=15, color=COR["titulo"])
    r = 3

    def titulo(txt):
        nonlocal r
        celula(ws, r, 1, txt, negrito=True, alinhar=ESQ, borda=False, tam=12)
        r += 1

    def item(txt):
        nonlocal r
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
        celula(ws, r, 1, f"• {txt}", alinhar=ESQ, borda=False)
        ws.row_dimensions[r].height = 15 if len(txt) < 120 else 28
        r += 1

    titulo("Legenda de cores")
    legenda(ws, r, 1)
    r += 2
    titulo("Regras gerais")
    for txt in (
        "Regime 5x2: duas folgas por semana (segunda a domingo).",
        "No máximo cinco dias seguidos de trabalho, inclusive na virada de semana.",
        "Evitar duas folgas seguidas; distribuir as folgas ao longo da semana.",
        "Homens: um domingo de folga no período. Mulheres: dois, quinzenais (06 e 20/12, 13 e 27/12 ou 20/12 e 03/01).",
        "A folga de domingo conta como uma das duas folgas da semana.",
        "Domingo 03/01 (complementar): todos trabalham; folga ali só como exceção (3ª folga da semana).",
        "Descanso legal de 11h entre jornadas: depois de dobra (saída 23:00) a pessoa não entra às 08:00.",
        f"Horários: manhã {MANHA} (1h), noite {NOITE} (1h), salão {SALAO} (2h), dobra {DOBRA} (2h), domingo {DOMINGO}.",
        "Horas efetivas: manhã 8h24, noite 8h18, salão 8h24, dobra 9h15, domingo 8h24 (intervalo de 1h a confirmar).",
        "Dobras cobrem a falta de colegas; domingo é turno único e não tem dobra.",
    ):
        item(txt)
    r += 1
    titulo("Datas especiais")
    for data, txt in DATAS_ESPECIAIS:
        item(f"{data:%d/%m/%Y} ({rotulo_data(DIAS.index(data))[6:]}): {txt}")
    r += 1
    titulo("Regras por setor")
    for txt in (
        "Bar e Sushi: os dois nunca folgam no mesmo dia; quem fica faz dobra (11:45–23:00).",
        "Salão: mínimo de 5 por turno; Juliana conta só no almoço; redução só de segunda a quinta.",
        "Salão: Elaine e Marcos não folgam juntos; Adriano e Guilherme não folgam juntos.",
        "Cozinha: meta de 7 na manhã e 6 na noite; dobras da noite cobrem a manhã e vice-versa.",
        "Cozinha: no máximo 2 da manhã sem trabalhar por dia (contando Edna e Moura).",
        "Cozinha: Rafael, Miro e Chef folgam em dias diferentes; Rafael e Felix não folgam juntos.",
        "Cozinha: dobras com prioridade para Rafael, Miro e Chef (até 3 por semana); demais até 2 por semana.",
        "Cozinha: Rony, Edna e Moura não fazem dobra; Rafael não faz dobra às terças e quartas.",
        "Pia: Daniel cobre a manhã quando Ilma folga e a noite quando Claudia folga; não folga com elas.",
        "Refeitório: Joelma não folga junto com Rafael da cozinha; evitar sábado; definir quem cobre as folgas.",
    ):
        item(txt)
    r += 1
    titulo("Ordem de prioridade em caso de conflito")
    for k, txt in enumerate((
        "Descansos e limites legais", "Datas coletivas e fechamento", "Máximo de 5 dias seguidos",
        "Folgas e restrições individuais obrigatórias", "Duas folgas semanais", "Domingos de folga",
        "Mínimo de colaboradores por turno", "Folgas simultâneas", "Equilíbrio das dobras",
        "Evitar folgas seguidas", "Preferências de dia de folga"), 1):
        item(f"{k}. {txt}")
    r += 1
    titulo("Equipe e restrições individuais")
    for c, txt in enumerate(["Setor", "Colaborador", "Turno", "Horário", "Intervalo", "Restrição"], 1):
        celula(ws, r, c, txt, negrito=True, fundo="cinza")
    r += 1
    for setor, pessoas in escala.items():
        for p in pessoas:
            for c, v in enumerate([setor, p.nome, TURNOS[p.turno], p.horario, p.intervalo, p.restricao], 1):
                celula(ws, r, c, v, alinhar=ESQ, tam=9)
            r += 1
    for col, w in zip("ABCDEF", (12, 14, 11, 13, 9, 80)):
        ws.column_dimensions[col].width = w
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def gerar_excel(caminho, escala, ocorrencias):
    wb = Workbook()
    wb.remove(wb.active)
    totais_ref = {}
    for setor, pessoas in escala.items():
        aba_setor(wb, setor, pessoas, totais_ref)
    aba_resumo(wb, escala, totais_ref, ocorrencias)
    aba_regras(wb, escala)
    wb.active = 0
    wb.save(caminho)
    return wb.sheetnames
