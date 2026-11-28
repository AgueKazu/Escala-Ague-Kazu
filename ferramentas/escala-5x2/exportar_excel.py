"""Gera a planilha Excel da escala: Regras, Pendências e um calendário por setor e mês (14 abas)."""

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from apresentacao import (
    CORES, LEGENDA, MESES, PADRONIZACAO, PONTOS_DE_ATENCAO, REGRAS_GERAIS, SETORES_RESUMO,
    agrupar_pendencias, turno_legivel,
)
from modelo import COLETIVA, DATAS_ESPECIAIS, DIAS, FECHADO, NOMES_DIA

fino = Side(style="thin", color="BFBFBF")
BORDA = Border(left=fino, right=fino, top=fino, bottom=fino)
CENTRO = Alignment(horizontal="center", vertical="center")
QUEBRA = Alignment(vertical="top", wrap_text=True)
NOMES_DIA_LONGO = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def preencher(cor):
    return PatternFill("solid", start_color=cor, end_color=cor)


def cabecalho(ws, linha, textos, larguras=None):
    for c, txt in enumerate(textos, 1):
        cel = ws.cell(row=linha, column=c, value=txt)
        cel.font = Font(bold=True)
        cel.fill = preencher(CORES["cinza"])
        cel.border = BORDA
        cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if larguras:
        for c, w in enumerate(larguras, 1):
            ws.column_dimensions[get_column_letter(c)].width = w


def secao(ws, linha, texto):
    ws.cell(row=linha, column=1, value=texto).font = Font(bold=True, size=12, color=CORES["titulo"])
    return linha + 1


def regras_de_cor(ws, intervalo, primeira_celula):
    for cod in ("F", "H", "D", "DS"):
        ws.conditional_formatting.add(
            intervalo,
            CellIsRule(operator="equal", formula=[f'"{cod}"'], fill=preencher(CORES[cod]),
                       font=Font(bold=cod in ("F", "D", "DS"))))
    # Domingo trabalhado em rosa
    ws.conditional_formatting.add(
        intervalo,
        CellIsRule(operator="equal", formula=['"S"'], fill=preencher(CORES["S"])))


# ---------------------------------------------------------------------------
def aba_regras(wb, setores):
    ws = wb.active
    ws.title = "Regras"
    ws["A1"] = "Escala de trabalho 5x2 — Dezembro/2026 e Janeiro/2027"
    ws["A1"].font = Font(bold=True, size=16, color=CORES["titulo"])
    ws["A2"] = ("Organizada por setor, com controle individual de horários, folgas semanais, folgas "
                "dominicais, dobras e quantidade de colaboradores disponíveis para cada turno.")
    ws["A2"].font = Font(italic=True, color="595959")
    r = 4

    r = secao(ws, r, "1. Regras gerais da escala")
    for txt in REGRAS_GERAIS:
        ws.cell(row=r, column=1, value="•").alignment = CENTRO
        ws.cell(row=r, column=2, value=txt)
        r += 1
    r += 1

    r = secao(ws, r, "Datas especiais")
    cabecalho(ws, r, ["Data", "Dia da semana", "Consideração"])
    r += 1
    for data, txt in DATAS_ESPECIAIS:
        c = ws.cell(row=r, column=1, value=data)
        c.number_format = "dd/mm/yyyy"
        ws.cell(row=r, column=2, value=NOMES_DIA_LONGO[data.weekday()])
        ws.cell(row=r, column=3, value=txt)
        cor = CORES["H"] if "fechado" in txt else (CORES["F"] if "Folga" in txt else CORES["S"])
        for k in range(1, 4):
            ws.cell(row=r, column=k).border = BORDA
        ws.cell(row=r, column=1).fill = preencher(cor)
        r += 1
    r += 1

    r = secao(ws, r, "Padronização visual")
    for chave, cor, txt in PADRONIZACAO:
        c = ws.cell(row=r, column=1, value=cor)
        c.fill = preencher(CORES[chave])
        c.border = BORDA
        c.font = Font(bold=True)
        ws.cell(row=r, column=2, value=txt)
        r += 1
    r += 1

    r = secao(ws, r, "3. Organização dos setores")
    cabecalho(ws, r, ["Setor", "Colaboradores"])
    r += 1
    for nome, n in SETORES_RESUMO:
        ws.cell(row=r, column=1, value=nome).border = BORDA
        c = ws.cell(row=r, column=2, value=n)
        c.border = BORDA
        c.alignment = CENTRO
        r += 1
    ws.cell(row=r, column=1, value="Total").font = Font(bold=True)
    c = ws.cell(row=r, column=2, value=f"=SUM(B{r - len(SETORES_RESUMO)}:B{r - 1})")
    c.font = Font(bold=True)
    c.alignment = CENTRO
    r += 2

    r = secao(ws, r, "4. Legenda dos horários")
    cabecalho(ws, r, ["Código", "Descrição", "Horário", "Intervalo"])
    r += 1
    for cod, desc, hor, intv in LEGENDA:
        c = ws.cell(row=r, column=1, value=cod)
        c.font = Font(bold=True)
        c.alignment = CENTRO
        if cod in CORES:
            c.fill = preencher(CORES[cod])
        for k, v in enumerate((desc, hor, intv), 2):
            ws.cell(row=r, column=k, value=v).border = BORDA
        c.border = BORDA
        r += 1
    r += 1

    r = secao(ws, r, "5. Pontos de atenção antes da aprovação")
    for txt in PONTOS_DE_ATENCAO:
        ws.cell(row=r, column=1, value="•").alignment = Alignment(horizontal="center", vertical="top")
        c = ws.cell(row=r, column=2, value=txt)
        c.alignment = QUEBRA
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
        ws.row_dimensions[r].height = 30 if len(txt) > 100 else 16
        r += 1
    r += 1

    r = secao(ws, r, "Equipe e restrições individuais")
    cabecalho(ws, r, ["Setor", "Colaborador", "Turno", "Horário", "Intervalo", "Restrição / observação"])
    r += 1
    for setor, pessoas in setores:
        for p in pessoas:
            for c, txt in enumerate([setor, p.nome, turno_legivel(p), p.horario, p.intervalo,
                                     p.observacao], 1):
                ws.cell(row=r, column=c, value=txt).border = BORDA
            r += 1

    for col, w in zip("ABCDEF", (16, 22, 14, 14, 11, 60)):
        ws.column_dimensions[col].width = w
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


# ---------------------------------------------------------------------------
def aba_pendencias(wb, ocorrencias):
    ws = wb.create_sheet("Pendências", 1)
    pend = agrupar_pendencias(ocorrencias)
    ws["A1"] = f"Pendências da escala proposta ({len(pend)})"
    ws["A1"].font = Font(bold=True, size=14, color=CORES["titulo"])
    ws["A2"] = ("Pendência obrigatória = regra que não pôde ser cumprida por conflito entre as próprias "
                "regras · Preferência não atendida = algo pedido como 'sempre que possível'.")
    ws["A2"].font = Font(italic=True, size=9, color="595959")
    cabecalho(ws, 4, ["Nº", "Tipo", "Setor", "Regra", "Colaboradores", "Datas", "Detalhe", "Decisão"],
              [5, 16, 10, 28, 22, 22, 80, 22])
    cores_tipo = {"Pendência obrigatória": "FFC7CE", "Preferência não atendida": "FFEB9C"}
    r = 5
    for n, o in enumerate(pend, 1):
        vals = [n, o["tipo"], o["setor"], o["regra"], o["pessoas"], o["datas"], o["detalhe"], ""]
        for c, v in enumerate(vals, 1):
            cel = ws.cell(row=r, column=c, value=v)
            cel.border = BORDA
            cel.alignment = QUEBRA
        ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="top")
        ws.cell(row=r, column=2).fill = preencher(cores_tipo[o["tipo"]])
        linhas = max(len(o["detalhe"]) // 90 + 1, len(o["datas"]) // 24 + 1, len(o["regra"]) // 30 + 1)
        ws.row_dimensions[r].height = 15 * min(linhas, 8)
        r += 1
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:H{max(r - 1, 4)}"

    r += 1
    ws.cell(row=r, column=1, value="Situações já previstas pelas próprias regras (não são pendências)").font = \
        Font(bold=True, size=12, color=CORES["titulo"])
    r += 1
    cabecalho(ws, r, ["", "Setor", "Colaborador", "Regra", "Data", "", "Detalhe"])
    r += 1
    for o in (o for o in ocorrencias if o["tipo"] == "Aceita"):
        for c, v in ((2, o["setor"]), (3, o["pessoa"]), (4, o["regra"]), (5, o["data"]), (7, o["detalhe"])):
            cel = ws.cell(row=r, column=c, value=v)
            cel.border = BORDA
            cel.alignment = QUEBRA
        ws.cell(row=r, column=1).fill = preencher("E2EFDA")
        r += 1
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    return len(pend)


# ---------------------------------------------------------------------------
def aba_calendario(wb, setor, mes, pessoas):
    titulo, dias = MESES[mes]
    ws = wb.create_sheet(f"{setor} {mes}")
    ws["A1"] = f"{setor} — {titulo}"
    ws["A1"].font = Font(bold=True, size=14, color=CORES["titulo"])
    ws["A2"] = ("M manhã · N noite · I integral · S domingo · D dobra · DS cobertura domingo · "
                "F folga · H fechado (horários na aba Regras)")
    ws["A2"].font = Font(italic=True, size=9, color="595959")

    L = get_column_letter
    col0 = 5  # coluna E
    linha_obs, linha_data, linha_dia = 3, 4, 5
    for c, txt in enumerate(["Colaborador", "Turno", "Horário", "Intervalo"], 1):
        cel = ws.cell(row=linha_data, column=c, value=txt)
        ws.merge_cells(start_row=linha_data, start_column=c, end_row=linha_dia, end_column=c)
        cel.font = Font(bold=True)
        cel.fill = preencher(CORES["cinza"])
        cel.alignment = CENTRO

    for k, i in enumerate(dias):
        c = col0 + k
        data = ws.cell(row=linha_data, column=c, value=DIAS[i])
        data.number_format = "dd/mm"
        dia = ws.cell(row=linha_dia, column=c, value=NOMES_DIA[DIAS[i].weekday()])
        cor = CORES["domingo"] if DIAS[i].weekday() == 6 else CORES["cinza"]
        for cel in (data, dia):
            cel.fill = preencher(cor)
            cel.font = Font(bold=True, size=9)
            cel.alignment = CENTRO
            cel.border = BORDA
        obs = "Fechado" if i in FECHADO else ("Folga geral" if i in COLETIVA else None)
        if obs:
            o = ws.cell(row=linha_obs, column=c, value=obs)
            o.font = Font(size=7, bold=True)
            o.alignment = Alignment(horizontal="center", shrink_to_fit=True)
            o.fill = preencher(CORES["H"] if i in FECHADO else CORES["F"])
        ws.column_dimensions[L(c)].width = 4.6

    c_fim = col0 + len(dias) - 1
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
            f'=COUNTIF({faixa},"D")+COUNTIF({faixa},"DS")',
            f'=SUMPRODUCT(({faixa_dias}="Dom")*({faixa}="F"))',
            f'=COUNTA({faixa})-COUNTIF({faixa},"F")-COUNTIF({faixa},"H")',
        ]
        for k, f in enumerate(formulas):
            cel = ws.cell(row=linha, column=c_fim + 1 + k, value=f)
            cel.alignment = CENTRO
            cel.border = BORDA
            cel.font = Font(bold=True)
        linhas_turno.setdefault(p.turno, []).append(linha)
        linha += 1
    primeira, ultima = linha_dia + 1, linha - 1
    regras_de_cor(ws, f"{L(col0)}{primeira}:{L(c_fim)}{ultima}", f"{L(col0)}{primeira}")

    # Totais do mês
    ws.cell(row=linha, column=1, value="Total do setor").font = Font(bold=True)
    ws.merge_cells(start_row=linha, start_column=1, end_row=linha, end_column=4)
    for k in range(4):
        col = L(c_fim + 1 + k)
        cel = ws.cell(row=linha, column=c_fim + 1 + k, value=f"=SUM({col}{primeira}:{col}{ultima})")
        cel.font = Font(bold=True)
        cel.alignment = CENTRO
        cel.fill = preencher(CORES["cinza"])
        cel.border = BORDA
    linha += 2

    def trabalhando(col, a, b):
        faixa = f"{col}{a}:{col}{b}"
        return f'(COUNTA({faixa})-COUNTIF({faixa},"F")-COUNTIF({faixa},"H"))'

    def cobertura(rotulo, montar, minimo=None, maximo=None):
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
        faixa = f"{L(col0)}{linha}:{L(c_fim)}{linha}"
        topo = f"{L(col0)}${linha_obs}"
        cond = None
        if minimo:
            cond = f'AND({topo}="",{L(col0)}{linha}<{minimo})'
        if maximo:
            cond = f'AND({topo}="",{L(col0)}{linha}>{maximo})'
        if cond:
            ws.conditional_formatting.add(
                faixa, FormulaRule(formula=[cond], fill=preencher(CORES["alerta"]),
                                   font=Font(color="9C0006", bold=True)))
        linha += 1

    if setor == "Cozinha":
        m, n = linhas_turno["manha"], linhas_turno["noite"]
        cobertura("Manhã (meta 7)",
                  lambda col: f'={trabalhando(col, m[0], m[-1])}+COUNTIF({col}{n[0]}:{col}{n[-1]},"D")')
        cobertura("Noite (meta 6)",
                  lambda col: f'={trabalhando(col, n[0], n[-1])}+COUNTIF({col}{m[0]}:{col}{m[-1]},"D")')
        cobertura("Manhã de folga (máx. 2)",
                  lambda col: f'=COUNTIF({col}{m[0]}:{col}{m[-1]},"F")', maximo=2)
    elif setor == "Salão":
        s = linhas_turno["salao"]
        cobertura("No salão às 11h30, sem Juliana (mín. 5)",
                  lambda col: f'={trabalhando(col, s[0], s[-1])}', minimo=5)
    else:
        cobertura("Trabalhando", lambda col: f'={trabalhando(col, primeira, ultima)}', minimo=1)

    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 10
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 9
    ws.freeze_panes = ws.cell(row=linha_dia + 1, column=col0)
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{linha_data}:{linha_dia}"


def gerar_excel(caminho, escala, setores, ocorrencias):
    """escala já com os códigos impressos (apresentacao.traduzir)."""
    wb = Workbook()
    aba_regras(wb, setores)
    for setor, _ in setores:
        for mes in ("Dez", "Jan"):
            aba_calendario(wb, setor, mes, escala[setor])
    n_pend = aba_pendencias(wb, ocorrencias)
    wb.save(caminho)
    return len(wb.sheetnames), n_pend
