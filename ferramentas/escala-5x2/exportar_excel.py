"""Gera a planilha Excel da escala (calendários por setor e mês, resumo e conferência)."""

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from modelo import COLETIVA, DATAS_ESPECIAIS, DIAS, DOBRA, DOMINGO, FECHADO, NOMES_DIA

CORES = {
    "cinza": "D9D9D9",
    "F": "FF7B7B",  # folga semanal (vermelho)
    "X": "8FD18F",  # fechado (verde)
    "B": "FFB25B",  # dobra (laranja)
    "D": "F9C6DD",  # domingo (rosa)
    "M": "BDD7EE",  # cobertura da manhã por Daniel (azul claro)
    "T": "FFFFFF",
    "titulo": "1F3864",
    "alerta": "FFC7CE",
}

LEGENDA = [
    ("T", "Trabalho em horário normal"),
    ("F", "Folga semanal"),
    ("X", "Restaurante fechado (não conta como folga)"),
    ("B", f"Dobra ({DOBRA}, 2h de intervalo)"),
    ("D", f"Horário de domingo ({DOMINGO})"),
    ("M", "Daniel cobrindo o turno da manhã (Pia)"),
]

MESES = {
    "Dez": ("Dezembro/2026 (30/11 a 31/12)", [i for i, x in enumerate(DIAS) if x.month in (11, 12)]),
    "Jan": ("Janeiro/2027 (01/01 a 31/01)", [i for i, x in enumerate(DIAS) if x.month == 1]),
}

fino = Side(style="thin", color="BFBFBF")
BORDA = Border(left=fino, right=fino, top=fino, bottom=fino)
CENTRO = Alignment(horizontal="center", vertical="center")


def preencher(cor):
    return PatternFill("solid", start_color=cor, end_color=cor)


def nome_aba(setor, mes):
    return f"{setor} {mes}"


def turno_legivel(p):
    return {"manha": "Manhã", "noite": "Noite", "salao": "Salão", "cobertura": "Cobertura"}[p.turno]


def regras_de_cor(ws, intervalo):
    for cod in ("F", "X", "B", "D", "M"):
        ws.conditional_formatting.add(
            intervalo,
            CellIsRule(operator="equal", formula=[f'"{cod}"'], fill=preencher(CORES[cod]),
                       font=Font(bold=cod in ("F", "B"))),
        )


def aba_calendario(wb, setor, mes, pessoas, totais):
    titulo, dias = MESES[mes]
    ws = wb.create_sheet(nome_aba(setor, mes))
    ws["A1"] = f"{setor} — {titulo}"
    ws["A1"].font = Font(bold=True, size=14, color=CORES["titulo"])
    ws["A2"] = "Escala 5×2 · Restaurante Kazu · códigos: T F X B D M (veja a aba Legenda)"
    ws["A2"].font = Font(italic=True, size=9, color="595959")

    col0 = 5  # coluna E
    linha_data, linha_dia, linha_obs = 4, 5, 3
    cab = ["Colaborador", "Turno", "Horário", "Intervalo"]
    for c, txt in enumerate(cab, start=1):
        cel = ws.cell(row=linha_data, column=c, value=txt)
        ws.merge_cells(start_row=linha_data, start_column=c, end_row=linha_dia, end_column=c)
        cel.font = Font(bold=True)
        cel.fill = preencher(CORES["cinza"])
        cel.alignment = CENTRO
        ws.cell(row=linha_dia, column=c).fill = preencher(CORES["cinza"])

    for k, i in enumerate(dias):
        c = col0 + k
        data = ws.cell(row=linha_data, column=c, value=DIAS[i])
        data.number_format = "dd/mm"
        dia = ws.cell(row=linha_dia, column=c, value=NOMES_DIA[DIAS[i].weekday()])
        cor = CORES["D"] if DIAS[i].weekday() == 6 else CORES["cinza"]
        for cel in (data, dia):
            cel.fill = preencher(cor)
            cel.font = Font(bold=True, size=9)
            cel.alignment = CENTRO
            cel.border = BORDA
        obs = "Fechado" if i in FECHADO else ("Coletiva" if i in COLETIVA else None)
        if obs:
            o = ws.cell(row=linha_obs, column=c, value=obs)
            o.font = Font(size=7, bold=True)
            o.alignment = Alignment(horizontal="center", shrink_to_fit=True)
            o.fill = preencher(CORES["X"] if i in FECHADO else CORES["F"])
        ws.column_dimensions[get_column_letter(c)].width = 4.6

    c_fim = col0 + len(dias) - 1
    L = get_column_letter
    tot_cols = ["Folgas", "Dobras", "Dom. folga", "Dias trab."]
    for k, txt in enumerate(tot_cols):
        c = c_fim + 1 + k
        cel = ws.cell(row=linha_data, column=c, value=txt)
        ws.merge_cells(start_row=linha_data, start_column=c, end_row=linha_dia, end_column=c)
        cel.font = Font(bold=True, size=9)
        cel.fill = preencher(CORES["cinza"])
        cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[L(c)].width = 8

    linha = linha_dia + 1
    linhas_turno = {}
    faixa_dias = f"${L(col0)}${linha_dia}:${L(c_fim)}${linha_dia}"
    for p, cod in pessoas.items():
        ws.cell(row=linha, column=1, value=p.nome).font = Font(bold=True)
        ws.cell(row=linha, column=2, value=turno_legivel(p))
        ws.cell(row=linha, column=3, value=p.horario)
        ws.cell(row=linha, column=4, value=p.intervalo)
        for c in range(1, 5):
            ws.cell(row=linha, column=c).border = BORDA
        for k, i in enumerate(dias):
            cel = ws.cell(row=linha, column=col0 + k, value=cod[i])
            cel.alignment = CENTRO
            cel.border = BORDA
        faixa = f"{L(col0)}{linha}:{L(c_fim)}{linha}"
        formulas = [
            f'=COUNTIF({faixa},"F")',
            f'=COUNTIF({faixa},"B")',
            f'=SUMPRODUCT(({faixa_dias}="Dom")*({faixa}="F"))',
            f'=SUMPRODUCT(({faixa}="T")+({faixa}="B")+({faixa}="D")+({faixa}="M"))',
        ]
        for k, f in enumerate(formulas):
            cel = ws.cell(row=linha, column=c_fim + 1 + k, value=f)
            cel.alignment = CENTRO
            cel.border = BORDA
        totais[(setor, p.nome, mes)] = {
            "folgas": f"'{ws.title}'!{L(c_fim + 1)}{linha}",
            "dobras": f"'{ws.title}'!{L(c_fim + 2)}{linha}",
            "domingos": f"'{ws.title}'!{L(c_fim + 3)}{linha}",
            "trabalho": f"'{ws.title}'!{L(c_fim + 4)}{linha}",
        }
        linhas_turno.setdefault(p.turno, []).append(linha)
        linha += 1
    primeira, ultima = linha_dia + 1, linha - 1
    regras_de_cor(ws, f"{L(col0)}{primeira}:{L(c_fim)}{ultima}")

    # Linhas de cobertura
    linha += 1

    def cobertura(rotulo, montar, minimo=None):
        nonlocal linha
        cel = ws.cell(row=linha, column=1, value=rotulo)
        cel.font = Font(bold=True, size=9)
        ws.merge_cells(start_row=linha, start_column=1, end_row=linha, end_column=4)
        for k in range(len(dias)):
            col = L(col0 + k)
            c = ws.cell(row=linha, column=col0 + k, value=montar(col))
            c.alignment = CENTRO
            c.font = Font(size=9, bold=True)
            c.fill = preencher("F2F2F2")
            c.border = BORDA
        if minimo:
            faixa = f"{L(col0)}{linha}:{L(c_fim)}{linha}"
            topo = f"{L(col0)}${linha_obs}"
            ws.conditional_formatting.add(
                faixa,
                FormulaRule(formula=[f'AND({topo}="",{L(col0)}{linha}<{minimo})'],
                            fill=preencher(CORES["alerta"]), font=Font(color="9C0006", bold=True)),
            )
        linha += 1

    todas = list(range(primeira, ultima + 1))
    if setor == "Cozinha":
        m, n = linhas_turno["manha"], linhas_turno["noite"]
        cobertura("Manhã (meta 7)",
                  lambda col: f'=SUMPRODUCT(({col}{m[0]}:{col}{m[-1]}="T")+({col}{m[0]}:{col}{m[-1]}="B")+({col}{m[0]}:{col}{m[-1]}="D"))'
                              f'+COUNTIF({col}{n[0]}:{col}{n[-1]},"B")', None)
        cobertura("Noite (meta 6)",
                  lambda col: f'=SUMPRODUCT(({col}{n[0]}:{col}{n[-1]}="T")+({col}{n[0]}:{col}{n[-1]}="B")+({col}{n[0]}:{col}{n[-1]}="D"))'
                              f'+COUNTIF({col}{m[0]}:{col}{m[-1]},"B")', None)
        cobertura("Manhã de folga (máx. 2)",
                  lambda col: f'=COUNTIF({col}{m[0]}:{col}{m[-1]},"F")', None)
    elif setor == "Salão":
        s = linhas_turno["salao"]
        cobertura("No salão, sem Juliana (mín. 5)",
                  lambda col: f'=SUMPRODUCT(({col}{s[0]}:{col}{s[-1]}="T")+({col}{s[0]}:{col}{s[-1]}="D"))', 5)
    else:
        cobertura("Trabalhando",
                  lambda col: f'=SUMPRODUCT(({col}{todas[0]}:{col}{todas[-1]}<>"F")*({col}{todas[0]}:{col}{todas[-1]}<>"X"))',
                  1)

    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 10
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 8
    ws.freeze_panes = ws.cell(row=linha_dia + 1, column=col0)
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{linha_data}:{linha_dia}"


def aba_legenda(wb, setores):
    ws = wb.active
    ws.title = "Legenda e regras"
    ws["A1"] = "Escala de trabalho 5×2 — Dezembro/2026 e Janeiro/2027"
    ws["A1"].font = Font(bold=True, size=16, color=CORES["titulo"])
    ws["A2"] = "Restaurante Kazu · planejamento por setor · período de 30/11/2026 a 31/01/2027"
    ws["A2"].font = Font(italic=True, color="595959")
    r = 4
    ws.cell(row=r, column=1, value="Legenda").font = Font(bold=True, size=12)
    r += 1
    for cod, txt in LEGENDA:
        c = ws.cell(row=r, column=1, value=cod)
        c.alignment = CENTRO
        c.font = Font(bold=True)
        c.fill = preencher(CORES[cod])
        c.border = BORDA
        ws.cell(row=r, column=2, value=txt)
        r += 1
    r += 1
    ws.cell(row=r, column=1, value="Datas especiais").font = Font(bold=True, size=12)
    r += 1
    for data, txt in DATAS_ESPECIAIS:
        c = ws.cell(row=r, column=1, value=data)
        c.number_format = "dd/mm/yyyy"
        ws.cell(row=r, column=2, value=f"{NOMES_DIA[data.weekday()]} — {txt}")
        r += 1
    r += 1
    ws.cell(row=r, column=1, value="Regras gerais").font = Font(bold=True, size=12)
    r += 1
    regras = [
        "Regime 5×2: duas folgas por semana (segunda a domingo).",
        "No máximo cinco dias seguidos de trabalho.",
        "Evitar duas folgas seguidas, exceto no fim de ano.",
        "Homens: um domingo de folga por mês. Mulheres: dois, de preferência quinzenais.",
        "Bar e Sushi: quando um folga, o outro faz dobra.",
        "Salão: mínimo de 5 no turno das 11h30 (Juliana conta só na manhã); prioridade sexta a domingo.",
        "Cozinha: meta de 7 na manhã e 6 na noite; as folgas são cobertas com dobras.",
        "Pia: Daniel cobre as folgas de Ilma (código M) e de Claudia (código T, turno da noite).",
        "Refeitório: Joelma não folga junto com Rafael da cozinha e evita sábados.",
        f"Domingo: turno único, {DOMINGO}, sem dobra.",
    ]
    for txt in regras:
        ws.cell(row=r, column=1, value="•").alignment = CENTRO
        ws.cell(row=r, column=2, value=txt)
        r += 1
    r += 1
    ws.cell(row=r, column=1, value="Equipe").font = Font(bold=True, size=12)
    r += 1
    for c, txt in enumerate(["Setor", "Colaborador", "Turno", "Horário", "Intervalo", "Restrição / observação"], 1):
        cel = ws.cell(row=r, column=c, value=txt)
        cel.font = Font(bold=True)
        cel.fill = preencher(CORES["cinza"])
        cel.border = BORDA
    r += 1
    for setor, pessoas in setores:
        for p in pessoas:
            for c, txt in enumerate([setor, p.nome, turno_legivel(p), p.horario, p.intervalo, p.observacao], 1):
                ws.cell(row=r, column=c, value=txt).border = BORDA
            r += 1
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 13
    ws.column_dimensions["E"].width = 10
    ws.column_dimensions["F"].width = 55


def aba_resumo(wb, setores, totais):
    ws = wb.create_sheet("Resumo", 1)
    ws["A1"] = "Resumo individual de folgas, dobras e domingos"
    ws["A1"].font = Font(bold=True, size=14, color=CORES["titulo"])
    ws["A2"] = "Os números vêm das abas de cada setor por fórmula: se mudar um código no calendário, o resumo acompanha."
    ws["A2"].font = Font(italic=True, size=9, color="595959")
    cab = ["Setor", "Colaborador", "Turno", "Folgas Dez", "Folgas Jan", "Dobras Dez", "Dobras Jan",
           "Dom. folga Dez", "Dom. folga Jan", "Total folgas", "Total dobras", "Dias trabalhados"]
    for c, txt in enumerate(cab, 1):
        cel = ws.cell(row=4, column=c, value=txt)
        cel.font = Font(bold=True)
        cel.fill = preencher(CORES["cinza"])
        cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cel.border = BORDA
    r = 5
    for setor, pessoas in setores:
        for p in pessoas:
            dz, jn = totais[(setor, p.nome, "Dez")], totais[(setor, p.nome, "Jan")]
            vals = [setor, p.nome, turno_legivel(p),
                    f"={dz['folgas']}", f"={jn['folgas']}", f"={dz['dobras']}", f"={jn['dobras']}",
                    f"={dz['domingos']}", f"={jn['domingos']}",
                    f"=D{r}+E{r}", f"=F{r}+G{r}", f"={dz['trabalho']}+{jn['trabalho']}"]
            for c, v in enumerate(vals, 1):
                cel = ws.cell(row=r, column=c, value=v)
                cel.border = BORDA
                if c > 3:
                    cel.alignment = CENTRO
            for c in (6, 7, 11):
                ws.cell(row=r, column=c).fill = preencher("FFF2E0")
            r += 1
    ws.cell(row=r, column=2, value="Total").font = Font(bold=True)
    for c in range(4, 13):
        col = get_column_letter(c)
        cel = ws.cell(row=r, column=c, value=f"=SUM({col}5:{col}{r - 1})")
        cel.font = Font(bold=True)
        cel.alignment = CENTRO
        cel.border = BORDA
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 11
    for c in range(4, 13):
        ws.column_dimensions[get_column_letter(c)].width = 10.5
    ws.row_dimensions[4].height = 32
    ws.freeze_panes = "D5"


def aba_conferencia(wb, ocorrencias):
    ws = wb.create_sheet("Conferência", 2)
    ws["A1"] = "Conferência das regras"
    ws["A1"].font = Font(bold=True, size=14, color=CORES["titulo"])
    ws["A2"] = ("Exceção = regra obrigatória não atendida · Atenção = preferência não atendida · "
                "Aceita = situação prevista pelas próprias regras")
    ws["A2"].font = Font(italic=True, size=9, color="595959")
    n = len(ocorrencias)
    ultima = 8 + n
    for k, tipo in enumerate(("Exceção", "Atenção", "Aceita")):
        ws.cell(row=3 + k, column=1, value=tipo).font = Font(bold=True)
        ws.cell(row=3 + k, column=2, value=f'=COUNTIF(A9:A{ultima},"{tipo}")').font = Font(bold=True)
    cores_tipo = {"Exceção": "FFC7CE", "Atenção": "FFEB9C", "Aceita": "E2EFDA"}
    cab = ["Tipo", "Setor", "Colaborador", "Data", "Regra", "Detalhe"]
    for c, txt in enumerate(cab, 1):
        cel = ws.cell(row=8, column=c, value=txt)
        cel.font = Font(bold=True)
        cel.fill = preencher(CORES["cinza"])
        cel.border = BORDA
    ordem = {"Exceção": 0, "Atenção": 1, "Aceita": 2}
    r = 9
    for o in sorted(ocorrencias, key=lambda o: ordem[o["tipo"]]):
        for c, k in enumerate(("tipo", "setor", "pessoa", "data", "regra", "detalhe"), 1):
            cel = ws.cell(row=r, column=c, value=o[k])
            cel.border = BORDA
        ws.cell(row=r, column=1).fill = preencher(cores_tipo[o["tipo"]])
        r += 1
    for col, w in zip("ABCDEF", (10, 14, 18, 8, 38, 70)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A9"
    ws.auto_filter.ref = f"A8:F{max(r - 1, 8)}"


def gerar_excel(caminho, escala, setores, ocorrencias):
    wb = Workbook()
    aba_legenda(wb, setores)
    totais = {}
    for setor, _ in setores:
        for mes in ("Dez", "Jan"):
            aba_calendario(wb, setor, mes, escala[setor], totais)
    aba_resumo(wb, setores, totais)
    aba_conferencia(wb, ocorrencias)
    wb.save(caminho)
    return len(wb.sheetnames)
