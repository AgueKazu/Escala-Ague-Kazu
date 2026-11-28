"""Gera o documento Word da escala (A4 deitado, calendários coloridos para impressão)."""

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from apresentacao import (
    CORES, LEGENDA, MESES, PADRONIZACAO, PONTOS_DE_ATENCAO, REGRAS_GERAIS, SETORES_RESUMO,
    turno_legivel,
)
from modelo import COLETIVA, DATAS_ESPECIAIS, DIAS, FECHADO, NOMES_DIA

NOMES_DIA_LONGO = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

REGRAS_SETOR = {
    "Bar": [
        "Vinicius folga às segundas-feiras até 20/12/2026.",
        "Quando um folga, o outro faz a dobra (D, 11:45–23:00); no domingo, a cobertura é DS.",
        "Cobertura diária garantida, sem folgas simultâneas (exceto datas coletivas).",
    ],
    "Sushi": [
        "Quando um folga, o outro faz a dobra (D, 11:45–23:00); no domingo, a cobertura é DS.",
        "Folgas e dobras distribuídas de forma equilibrada.",
    ],
    "Salão": [
        "Mínimo de 5 no turno integral (I, 11h30); Juliana faz só a manhã (M). Prioridade sexta a domingo.",
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
        "Daniel cobre as folgas de Ilma (M, turno da manhã) e de Claudia (N, turno da noite); no domingo, DS.",
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
    titulo(doc, f"{setor} — {rotulo}", 1)
    for txt in REGRAS_SETOR[setor]:
        par = doc.add_paragraph(txt, style="List Bullet")
        par.paragraph_format.space_after = Pt(0)
        for r in par.runs:
            r.font.size = Pt(8)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    ncol = 2 + len(dias) + 3
    tab = doc.add_table(rows=2 + len(pessoas) + 1, cols=ncol)
    tab.style = "Table Grid"
    tab.alignment = WD_TABLE_ALIGNMENT.CENTER
    tab.autofit = False
    margens_celula(tab)
    larguras = [Cm(2.0), Cm(1.4)] + [Cm(0.66)] * len(dias) + [Cm(0.85)] * 3
    fixar_larguras(tab, larguras)

    cab0, cab1 = tab.rows[0].cells, tab.rows[1].cells
    escrever(cab0[0], "Colaborador", 7, True)
    escrever(cab0[1], "Turno", 7, True)
    escrever(cab1[0], "", 7)
    escrever(cab1[1], "", 7)
    for k, i in enumerate(dias):
        c = 2 + k
        cor = CORES["domingo"] if DIAS[i].weekday() == 6 else CORES["cinza"]
        escrever(cab0[c], DIAS[i].strftime("%d"), 7, True)
        escrever(cab1[c], NOMES_DIA[DIAS[i].weekday()][:3], 5.5, True)
        sombrear(cab0[c], cor)
        sombrear(cab1[c], cor)
    for k, txt in enumerate(("Folgas", "Dobras", "Dom. folga")):
        c = 2 + len(dias) + k
        escrever(cab0[c], txt, 5.5, True)
        escrever(cab1[c], "", 6)
        sombrear(cab0[c], CORES["cinza"])
        sombrear(cab1[c], CORES["cinza"])
    for c in (0, 1):
        sombrear(cab0[c], CORES["cinza"])
        sombrear(cab1[c], CORES["cinza"])

    soma = [0, 0, 0]
    for r, (p, cod) in enumerate(pessoas.items(), start=2):
        cel = tab.rows[r].cells
        escrever(cel[0], p.nome, 7, True, centro=False)
        escrever(cel[1], turno_legivel(p), 6, centro=False)
        for k, i in enumerate(dias):
            x = cod[i]
            escrever(cel[2 + k], x, 6.5 if len(x) > 1 else 7, x in ("F", "D", "DS"))
            if x in CORES:
                sombrear(cel[2 + k], CORES[x])
        folgas = sum(1 for i in dias if cod[i] == "F")
        dobras = sum(1 for i in dias if cod[i] in ("D", "DS"))
        doms = sum(1 for i in dias if cod[i] == "F" and DIAS[i].weekday() == 6)
        for k, v in enumerate((folgas, dobras, doms)):
            soma[k] += v
            escrever(cel[2 + len(dias) + k], v, 7, True)
    ult = tab.rows[-1].cells
    juntar = ult[0].merge(ult[1 + len(dias)])
    escrever(juntar, "Total do setor no mês", 7, True, centro=False)
    sombrear(juntar, CORES["cinza"])
    for k, v in enumerate(soma):
        escrever(ult[2 + len(dias) + k], v, 7, True)
        sombrear(ult[2 + len(dias) + k], CORES["cinza"])
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    run = p.add_run("M manhã 08:00–17:24 · N noite 13:30–22:48 · I integral 11:30–21:54 · "
                    "S domingo 10:30–19:54 · D dobra 11:45–23:00 · DS cobertura domingo 10:30–19:54 · "
                    "F folga · H restaurante fechado")
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


def sem_bordas(tabela):
    tblPr = tabela._tbl.tblPr
    bordas = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:val"), "nil")
        bordas.append(el)
    tblPr.append(bordas)


def subtitulo(celula, texto):
    par = celula.add_paragraph()
    par.paragraph_format.space_before = Pt(6)
    par.paragraph_format.space_after = Pt(2)
    run = par.add_run(texto)
    run.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor.from_string(CORES["titulo"])


def item(celula, texto, tamanho=8):
    par = celula.add_paragraph(style="List Bullet")
    par.paragraph_format.space_after = Pt(0)
    run = par.add_run(texto)
    run.font.size = Pt(tamanho)


def mini_tabela(celula, cabecalho, linhas, larguras, cores=None, tamanho=7.5):
    tab = celula.add_table(rows=1 + len(linhas), cols=len(cabecalho))
    tab.style = "Table Grid"
    tab.autofit = False
    for c, txt in enumerate(cabecalho):
        escrever(tab.rows[0].cells[c], txt, tamanho, True, centro=False)
        sombrear(tab.rows[0].cells[c], CORES["cinza"])
    for r, linha in enumerate(linhas, start=1):
        for c, txt in enumerate(linha):
            escrever(tab.rows[r].cells[c], txt, tamanho, c == 0, centro=False)
        if cores and cores[r - 1]:
            sombrear(tab.rows[r].cells[0], cores[r - 1])
    fixar_larguras(tab, [Cm(w) for w in larguras])
    return tab


def pagina_regras(doc):
    titulo(doc, "Escala de trabalho 5x2 — Dezembro/2026 e Janeiro/2027", 0)
    p = doc.add_paragraph("A escala está organizada por setor, com controle individual de horários, folgas "
                          "semanais, folgas dominicais, dobras e quantidade de colaboradores disponíveis "
                          "para cada turno. Período: 30/11/2026 a 31/01/2027 · 29 colaboradores.")
    p.runs[0].font.size = Pt(9)
    grade = doc.add_table(rows=1, cols=2)
    grade.autofit = False
    sem_bordas(grade)
    fixar_larguras(grade, [Cm(14.2), Cm(13.4)])
    esq, dir_ = grade.rows[0].cells
    esq.paragraphs[0].paragraph_format.space_after = Pt(0)
    dir_.paragraphs[0].paragraph_format.space_after = Pt(0)

    subtitulo(esq, "1. Regras gerais da escala")
    for txt in REGRAS_GERAIS:
        item(esq, txt)
    subtitulo(esq, "Datas especiais")
    cores = []
    for _, t in DATAS_ESPECIAIS:
        cores.append(CORES["H"] if "fechado" in t else (CORES["F"] if "Folga" in t else CORES["domingo"]))
    mini_tabela(esq, ["Data", "Dia da semana", "Consideração"],
                [(x.strftime("%d/%m/%Y"), NOMES_DIA_LONGO[x.weekday()], t) for x, t in DATAS_ESPECIAIS],
                [2.2, 2.4, 9.0], cores)
    subtitulo(esq, "5. Pontos de atenção antes da aprovação")
    for txt in PONTOS_DE_ATENCAO:
        item(esq, txt, 7.5)

    subtitulo(dir_, "4. Legenda dos horários")
    mini_tabela(dir_, ["Código", "Descrição", "Horário", "Intervalo"],
                [(c, d, h, i) for c, d, h, i in LEGENDA], [1.5, 3.8, 3.0, 2.2],
                [CORES.get(c) for c, *_ in LEGENDA])
    subtitulo(dir_, "3. Organização dos setores")
    linhas = [(s, str(n)) for s, n in SETORES_RESUMO] + [("Total", str(sum(n for _, n in SETORES_RESUMO)))]
    mini_tabela(dir_, ["Setor", "Colaboradores"], linhas, [4.5, 3.0])
    subtitulo(dir_, "Padronização visual")
    mini_tabela(dir_, ["Cor", "Uso"], [(cor, uso) for _, cor, uso in PADRONIZACAO], [2.5, 6.0],
                [CORES[k] for k, *_ in PADRONIZACAO])
    nota = dir_.add_paragraph()
    nota.paragraph_format.space_before = Pt(4)
    r = nota.add_run("Ao final de cada calendário mensal estão os totais individuais de folgas e dobras. "
                     "As pendências da proposta estão na aba Pendências do Excel.")
    r.font.size = Pt(7.5)
    r.italic = True


def gerar_word(caminho, escala, setores, ocorrencias):
    """escala já com os códigos impressos (apresentacao.traduzir)."""
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

    pagina_regras(doc)
    for setor, _ in setores:
        for mes in ("Dez", "Jan"):
            quebra(doc)
            calendario(doc, setor, mes, escala[setor])
    doc.save(caminho)
