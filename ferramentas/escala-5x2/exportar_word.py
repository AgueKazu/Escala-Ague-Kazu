"""Gera o documento Word da escala (A4 deitado, calendários coloridos para impressão)."""

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from exportar_excel import CORES, LEGENDA, MESES, turno_legivel
from modelo import COLETIVA, DATAS_ESPECIAIS, DIAS, DOMINGO, FECHADO, NOMES_DIA

REGRAS_SETOR = {
    "Bar": [
        "Vinicius folga às segundas-feiras até 20/12/2026.",
        "Quando um folga, o outro faz a dobra (11:45–23:00, 2h de intervalo).",
        "Cobertura diária garantida, sem folgas simultâneas (exceto datas coletivas).",
    ],
    "Sushi": [
        "Quando um folga, o outro faz a dobra (11:45–23:00, 2h de intervalo).",
        "Folgas e dobras distribuídas de forma equilibrada.",
    ],
    "Salão": [
        "Mínimo de 5 no turno das 11h30 (Juliana conta só na manhã); prioridade sexta a domingo.",
        "Elaine e Marcos não folgam juntos; Adriano e Guilherme não folgam juntos.",
        "Marcos trabalha em 13/12, folga em 26/12 e evita folgas às segundas e terças.",
        "Sivanilda folga em 19/12. Juliana, Elaine e Sivanilda: dois domingos por mês.",
    ],
    "Cozinha": [
        "Meta de 7 na manhã e 6 na noite; as folgas são cobertas com dobras do outro turno.",
        "Rony, Edna e Moura não fazem dobra; Rafael não dobra às terças e quartas.",
        "Rafael, Miro e Chef recebem mais dobras e evitam folgar no mesmo dia.",
        "No máximo 2 da manhã de folga no mesmo dia. Edna folga sábado e domingo; Moura, segunda e terça.",
    ],
    "Pia": [
        "Daniel cobre as folgas de Ilma (código M, turno da manhã) e de Claudia (turno da noite).",
        "Sem folgas simultâneas nos dias de semana. Ilma e Claudia: dois domingos por mês; Daniel: um.",
    ],
    "Refeitório": [
        "Duas folgas por semana; dois domingos por mês, de preferência quinzenais.",
        "Não folga no mesmo dia que Rafael da cozinha; evita sábados.",
    ],
}


def sombrear(celula, cor):
    tcPr = celula._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), cor)
    tcPr.append(shd)


def margens_celula(tabela, cm=0.03):
    tblPr = tabela._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for lado in ("left", "right"):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:w"), str(int(cm * 567)))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def fixar_larguras(tabela, larguras):
    """Larguras fixas que o Word e o LibreOffice respeitam."""
    tblPr = tabela._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    for c, w in enumerate(larguras):
        tabela.columns[c].width = w
        for celula in tabela.columns[c].cells:
            celula.width = w


def escrever(celula, texto, tamanho=7, negrito=False, centro=True, cor=None):
    celula.text = ""
    par = celula.paragraphs[0]
    par.paragraph_format.space_before = Pt(0)
    par.paragraph_format.space_after = Pt(0)
    if centro:
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = par.add_run(str(texto))
    run.font.size = Pt(tamanho)
    run.bold = negrito
    if cor:
        run.font.color.rgb = RGBColor.from_string(cor)


def titulo(doc, texto, nivel=1):
    h = doc.add_heading(texto, level=nivel)
    for r in h.runs:
        r.font.color.rgb = RGBColor.from_string(CORES["titulo"])
    return h


def quebra(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def calendario(doc, setor, mes, pessoas):
    rotulo, dias = MESES[mes]
    titulo(doc, f"{setor} — {rotulo}", 2)
    ncol = 2 + len(dias) + 3
    tab = doc.add_table(rows=2 + len(pessoas), cols=ncol)
    tab.style = "Table Grid"
    tab.alignment = WD_TABLE_ALIGNMENT.CENTER
    tab.autofit = False
    margens_celula(tab)
    larguras = [Cm(2.1), Cm(1.4)] + [Cm(0.62)] * len(dias) + [Cm(0.8)] * 3
    fixar_larguras(tab, larguras)

    cab0, cab1 = tab.rows[0].cells, tab.rows[1].cells
    escrever(cab0[0], "Colaborador", 7, True)
    escrever(cab0[1], "Turno", 7, True)
    escrever(cab1[0], "", 7)
    escrever(cab1[1], "", 7)
    for k, i in enumerate(dias):
        c = 2 + k
        cor = CORES["D"] if DIAS[i].weekday() == 6 else CORES["cinza"]
        if i in FECHADO:
            cor = CORES["X"]
        elif i in COLETIVA:
            cor = CORES["F"]
        escrever(cab0[c], DIAS[i].strftime("%d"), 7, True)
        escrever(cab1[c], NOMES_DIA[DIAS[i].weekday()][:2], 6, True)
        sombrear(cab0[c], cor)
        sombrear(cab1[c], cor)
    for k, txt in enumerate(("F", "B", "Dom")):
        c = 2 + len(dias) + k
        escrever(cab0[c], txt, 7, True)
        escrever(cab1[c], "", 6)
        sombrear(cab0[c], CORES["cinza"])
        sombrear(cab1[c], CORES["cinza"])
    for c in (0, 1):
        sombrear(cab0[c], CORES["cinza"])
        sombrear(cab1[c], CORES["cinza"])

    for r, (p, cod) in enumerate(pessoas.items(), start=2):
        cel = tab.rows[r].cells
        escrever(cel[0], p.nome, 7, True, centro=False)
        escrever(cel[1], turno_legivel(p), 6, centro=False)
        for k, i in enumerate(dias):
            x = cod[i]
            escrever(cel[2 + k], x, 7, x in ("F", "B"))
            if x != "T":
                sombrear(cel[2 + k], CORES[x])
        folgas = sum(1 for i in dias if cod[i] == "F")
        dobras = sum(1 for i in dias if cod[i] == "B")
        doms = sum(1 for i in dias if cod[i] == "F" and DIAS[i].weekday() == 6)
        for k, v in enumerate((folgas, dobras, doms)):
            escrever(cel[2 + len(dias) + k], v, 7, True)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    run = p.add_run("T trabalho · F folga · X fechado · B dobra 11:45–23:00 · D domingo 10:30–19:54 · "
                    "M Daniel na manhã · colunas finais: folgas, dobras e domingos de folga no mês")
    run.font.size = Pt(7)
    run.italic = True


def tabela_simples(doc, cabecalho, linhas, larguras, tamanho=8):
    tab = doc.add_table(rows=1 + len(linhas), cols=len(cabecalho))
    tab.style = "Table Grid"
    tab.autofit = False
    for c, txt in enumerate(cabecalho):
        escrever(tab.rows[0].cells[c], txt, tamanho, True, centro=False)
        sombrear(tab.rows[0].cells[c], CORES["cinza"])
    for r, linha in enumerate(linhas, start=1):
        for c, txt in enumerate(linha):
            escrever(tab.rows[r].cells[c], txt, tamanho, centro=False)
    fixar_larguras(tab, [Cm(w) for w in larguras])
    return tab


def gerar_word(caminho, escala, setores, ocorrencias):
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
    for lado in ("left_margin", "right_margin"):
        setattr(sec, lado, Cm(1.0))
    sec.top_margin = sec.bottom_margin = Cm(1.0)
    estilo = doc.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(10)

    # Página 1: apresentação
    titulo(doc, "Escala de trabalho 5×2 — Dezembro/2026 e Janeiro/2027", 0)
    doc.add_paragraph("Planejamento de escala de funcionários por setor — Restaurante Kazu · "
                      "período de 30/11/2026 a 31/01/2027 · 29 colaboradores em 6 setores.")
    titulo(doc, "Regras gerais", 2)
    for txt in (
        "Regime 5×2, com duas folgas por semana (semana de segunda a domingo).",
        "No máximo cinco dias seguidos de trabalho; evitar duas folgas seguidas, exceto no fim de ano.",
        "Homens: um domingo de folga por mês. Mulheres: dois, de preferência com intervalo quinzenal.",
        "Folgas e dobras distribuídas de forma equilibrada, priorizando os horários de maior movimento.",
        f"Domingo: turno único, das {DOMINGO.replace('–', ' às ')}, sem dobra.",
    ):
        doc.add_paragraph(txt, style="List Bullet")
    titulo(doc, "Datas especiais", 2)
    tabela_simples(doc, ["Data", "Dia", "Consideração"],
                   [(x.strftime("%d/%m/%Y"), NOMES_DIA[x.weekday()], t) for x, t in DATAS_ESPECIAIS],
                   [3, 2, 14])
    titulo(doc, "Legenda", 2)
    tab = doc.add_table(rows=len(LEGENDA), cols=2)
    tab.style = "Table Grid"
    tab.autofit = False
    fixar_larguras(tab, [Cm(1.2), Cm(12)])
    for r, (cod, txt) in enumerate(LEGENDA):
        escrever(tab.rows[r].cells[0], cod, 9, True)
        sombrear(tab.rows[r].cells[0], CORES[cod])
        escrever(tab.rows[r].cells[1], txt, 9, centro=False)

    # Uma página por setor e mês
    for setor, pessoas in setores:
        quebra(doc)
        titulo(doc, f"Setor: {setor}", 1)
        for txt in REGRAS_SETOR[setor]:
            par = doc.add_paragraph(txt, style="List Bullet")
            par.paragraph_format.space_after = Pt(0)
            for r in par.runs:
                r.font.size = Pt(9)
        calendario(doc, setor, "Dez", escala[setor])
        quebra(doc)
        calendario(doc, setor, "Jan", escala[setor])

    # Resumo
    quebra(doc)
    titulo(doc, "Resumo individual", 1)
    linhas = []
    for setor, pessoas in setores:
        for p in pessoas:
            cod = escala[setor][p]
            dz, jn = MESES["Dez"][1], MESES["Jan"][1]
            f = lambda dias, x: sum(1 for i in dias if cod[i] == x)
            dom = lambda dias: sum(1 for i in dias if cod[i] == "F" and DIAS[i].weekday() == 6)
            linhas.append((setor, p.nome, turno_legivel(p), f(dz, "F"), f(jn, "F"), f(dz, "B"), f(jn, "B"),
                           dom(dz), dom(jn)))
    tabela_simples(doc, ["Setor", "Colaborador", "Turno", "Folgas Dez", "Folgas Jan", "Dobras Dez",
                         "Dobras Jan", "Dom. Dez", "Dom. Jan"], linhas,
                   [2.6, 2.8, 2.2, 2, 2, 2, 2, 2, 2], 7)

    # Pontos de atenção
    quebra(doc)
    titulo(doc, "Pontos que precisam de atenção", 1)
    conta = {t: sum(1 for o in ocorrencias if o["tipo"] == t) for t in ("Exceção", "Atenção", "Aceita")}
    doc.add_paragraph(
        f"A proposta contempla os 29 colaboradores. A conferência automática encontrou "
        f"{conta['Exceção']} exceção(ões) a regras obrigatórias, {conta['Atenção']} preferência(s) não "
        f"atendida(s) e {conta['Aceita']} situação(ões) já previstas pelas próprias regras. "
        "A lista completa, com filtro, está na aba Conferência do Excel.")
    for tipo in ("Exceção", "Atenção", "Aceita"):
        itens = [o for o in ocorrencias if o["tipo"] == tipo]
        if not itens:
            continue
        titulo(doc, {"Exceção": "Exceções (regras obrigatórias)", "Atenção": "Preferências não atendidas",
                     "Aceita": "Situações aceitas pelas regras"}[tipo], 2)
        tabela_simples(doc, ["Setor", "Colaborador", "Data", "Regra", "Detalhe"],
                       [(o["setor"], o["pessoa"], o["data"], o["regra"], o["detalhe"]) for o in itens],
                       [2.8, 3.2, 1.6, 6.5, 13.5], 7)
    doc.save(caminho)
