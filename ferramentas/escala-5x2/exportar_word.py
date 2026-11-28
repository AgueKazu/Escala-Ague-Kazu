"""Gera o Word da escala para impressão (A4 deitado): resumo, um calendário
por setor (só o calendário, sem as regras longas) e a conferência no final.
O PDF é convertido a partir deste arquivo pelo LibreOffice."""

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from conferencia import ORDEM, cobertura, indicadores
from exportar_excel import COR, LEGENDA, TOTAIS, observacao_do_dia
from modelo import DATAS_ESPECIAIS, DIAS, PERIODO, TURNOS, eh_domingo, horario_do_codigo, rotulo_data

CURTOS = ["Folgas", "Dobras", "Dom. folga", "Dias trab.", "Feriados", "Horas", "Máx. seguidos"]
LARGURA_UTIL = 28.1  # cm (A4 deitado com margens de 0,8 cm)


def sombrear(cel, cor):
    tcPr = cel._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), cor)
    tcPr.append(shd)


def preparar_tabela(tab, larguras_cm):
    tblPr = tab._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    mar = OxmlElement("w:tblCellMar")
    for lado in ("left", "right"):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:w"), "20")
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)
    for c, w in enumerate(larguras_cm):
        tab.columns[c].width = Cm(w)
        for cel in tab.columns[c].cells:
            cel.width = Cm(w)
    tab.alignment = WD_TABLE_ALIGNMENT.CENTER


def altura_linha(linha, cm):
    trPr = linha._tr.get_or_add_trPr()
    h = OxmlElement("w:trHeight")
    h.set(qn("w:val"), str(int(cm * 567)))
    h.set(qn("w:hRule"), "exact")
    trPr.append(h)


def escrever(cel, texto, tam=6.5, negrito=False, centro=True, cor_txt=None, fundo=None):
    cel.text = ""
    p = cel.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if centro else WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = pf.space_after = Pt(0)
    pf.line_spacing = 1.0
    run = p.add_run(str(texto))
    run.font.size = Pt(tam)
    run.bold = negrito
    if cor_txt:
        run.font.color.rgb = RGBColor.from_string(cor_txt)
    if fundo:
        sombrear(cel, fundo)
    cel.vertical_alignment = 1


def paragrafo(doc, texto, tam=9, negrito=False, cor=None, depois=2):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(depois)
    p.paragraph_format.space_before = Pt(0)
    r = p.add_run(texto)
    r.font.size = Pt(tam)
    r.bold = negrito
    if cor:
        r.font.color.rgb = RGBColor.from_string(cor)
    return p


def legenda(doc):
    tab = doc.add_table(rows=1, cols=len(LEGENDA) * 2)
    larg = []
    for k, (c, txt) in enumerate(LEGENDA):
        escrever(tab.cell(0, 2 * k), "", fundo=COR[c])
        escrever(tab.cell(0, 2 * k + 1), txt, tam=7, centro=False)
        larg += [0.5, 4.1]
    preparar_tabela(tab, larg)
    tab.style = "Table Grid"


def quebra(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def cor_da_celula(cod, domingo):
    if cod == "F":
        return COR["folga"]
    if cod == "B":
        return COR["dobra"]
    if cod == "X":
        return COR["fechado"]
    return COR["domingo_claro"] if domingo else None


def calendario(doc, setor, pessoas):
    lista = list(pessoas)
    cob = cobertura(setor, pessoas)
    rot_cob = list(next(t for t in cob.values() if t).keys())
    paragrafo(doc, f"{setor.upper()} · Escala 5x2 · {PERIODO}", tam=13, negrito=True, cor=COR["titulo"])
    legenda(doc)
    paragrafo(doc, "", tam=2, depois=0)

    n = len(lista)
    ncol = 1 + n + len(rot_cob) + 1
    tab = doc.add_table(rows=2 + len(DIAS) + len(TOTAIS), cols=ncol)
    tab.style = "Table Grid"
    l_data, l_cob = 1.75, 1.05
    resto = LARGURA_UTIL - l_data - l_cob * len(rot_cob)
    l_pessoa = min(3.0, (resto - 3.0) / n)
    l_obs = LARGURA_UTIL - l_data - l_cob * len(rot_cob) - l_pessoa * n
    if l_obs > 7:
        l_obs = 7
    larg = [l_data] + [l_pessoa] * n + [l_cob] * len(rot_cob) + [l_obs]

    cinza = COR["cinza"]
    escrever(tab.cell(0, 0), "Data", negrito=True, fundo=cinza, tam=7)
    escrever(tab.cell(1, 0), "", fundo=cinza)
    for k, p in enumerate(lista):
        escrever(tab.cell(0, 1 + k), p.nome, negrito=True, fundo=cinza, tam=7.5)
        escrever(tab.cell(1, 1 + k), f"{TURNOS[p.turno]} {p.horario}", fundo=cinza, tam=5.5)
    for k, rot in enumerate(rot_cob):
        meta = next(t for t in cob.values() if t)[rot][1]
        escrever(tab.cell(0, 1 + n + k), rot, negrito=True, fundo=cinza, tam=6.5)
        escrever(tab.cell(1, 1 + n + k), f"{'meta' if setor == 'Cozinha' else 'mín.'} {meta}", fundo=cinza, tam=5.5)
    escrever(tab.cell(0, ncol - 1), "Observação", negrito=True, fundo=cinza, tam=7)
    escrever(tab.cell(1, ncol - 1), "", fundo=cinza)

    for i in range(len(DIAS)):
        r = 2 + i
        dom = eh_domingo(i)
        escrever(tab.cell(r, 0), rotulo_data(i), negrito=True, fundo=COR["domingo"] if dom else cinza)
        for k, p in enumerate(lista):
            cod = pessoas[p][i]
            escrever(tab.cell(r, 1 + k), horario_do_codigo(p, cod), negrito=cod in "FBX",
                     fundo=cor_da_celula(cod, dom))
        for k, rot in enumerate(rot_cob):
            t = cob[i]
            if not t:
                escrever(tab.cell(r, 1 + n + k), "—", fundo=COR["total"])
                continue
            q, meta = t[rot]
            baixo = q < meta
            escrever(tab.cell(r, 1 + n + k), q, negrito=True,
                     fundo=COR["alerta"] if baixo else COR["total"], cor_txt="9C0006" if baixo else None)
        escrever(tab.cell(r, ncol - 1), observacao_do_dia(setor, pessoas, i), tam=5.5, centro=False)

    ind = {p: indicadores(p, pessoas[p]) for p in lista}
    chaves = ["folgas", "dobras", "domingos", "trabalhados", "feriados", "horas", "max_seguidos"]
    for j, rot in enumerate(TOTAIS):
        r = 2 + len(DIAS) + j
        escrever(tab.cell(r, 0), CURTOS[j], negrito=True, fundo=cinza, tam=6, centro=False)
        for k, p in enumerate(lista):
            v = ind[p][chaves[j]]
            if chaves[j] == "horas":
                h = round(v * 60)
                v = f"{h // 60}h{h % 60:02d}"
            alerta = chaves[j] == "max_seguidos" and v > 5
            escrever(tab.cell(r, 1 + k), v, negrito=True, fundo=COR["alerta"] if alerta else COR["total"])
        a, b = tab.cell(r, 1 + n), tab.cell(r, ncol - 1)
        a.merge(b)
    preparar_tabela(tab, larg)
    for r, linha in enumerate(tab.rows):
        altura_linha(linha, 0.36 if r >= 2 else (0.45 if r == 0 else 0.55))


def resumo(doc, escala):
    paragrafo(doc, "Escala de trabalho 5x2 · Dezembro/2026 e Janeiro/2027", tam=16, negrito=True, cor=COR["titulo"])
    paragrafo(doc, f"Período: {PERIODO} (cinco semanas, segunda a domingo) · calendário separado por setor",
              tam=9, cor="595959", depois=6)
    legenda(doc)
    paragrafo(doc, "", tam=4)
    paragrafo(doc, "Resumo por setor", tam=11, negrito=True)
    tab = doc.add_table(rows=1 + len(escala), cols=7)
    tab.style = "Table Grid"
    cab = ["Setor", "Colaboradores", "Folgas", "Dobras", "Horas previstas", "Máx. dias seguidos",
           "Dias com turno abaixo do mínimo"]
    for c, t in enumerate(cab):
        escrever(tab.cell(0, c), t, negrito=True, fundo=COR["cinza"], tam=8)
    for r, (setor, pessoas) in enumerate(escala.items(), 1):
        ind = [indicadores(p, c) for p, c in pessoas.items()]
        baixo = sum(1 for t in cobertura(setor, pessoas).values()
                    if t and any(q < m for q, m in t.values())) if setor != "Refeitório" else 0
        h = round(sum(x["horas"] for x in ind) * 60)
        vals = [setor, len(pessoas), sum(x["folgas"] for x in ind), sum(x["dobras"] for x in ind),
                f"{h // 60}h{h % 60:02d}", max(x["max_seguidos"] for x in ind), baixo]
        for c, v in enumerate(vals):
            escrever(tab.cell(r, c), v, tam=8, negrito=c == 0, centro=c != 0)
    preparar_tabela(tab, [4, 3, 3, 3, 4, 4, 7])
    paragrafo(doc, "", tam=4)
    paragrafo(doc, "Datas especiais", tam=11, negrito=True)
    for data, txt in DATAS_ESPECIAIS:
        paragrafo(doc, f"• {data:%d/%m/%Y} ({rotulo_data(DIAS.index(data))[6:]}): {txt}", tam=8.5, depois=0)
    paragrafo(doc, "", tam=4)
    paragrafo(doc, "Como ler", tam=11, negrito=True)
    for txt in (
        "Cada célula mostra o horário do dia. Folga em vermelho, dobra (11:45–23:00) em laranja, fechado em verde.",
        "Domingos com a data em rosa; aos domingos o horário é 10:30–19:54, sem dobra.",
        "As colunas à direita contam quantas pessoas há em cada turno; em vermelho quando abaixo do mínimo.",
        "Ninguém faz dobra (saída 23:00) e entra às 08:00 no dia seguinte: descanso legal de 11h.",
        "Horas consideram 1h de intervalo no domingo (a confirmar). Validar com o departamento pessoal antes de aplicar.",
    ):
        paragrafo(doc, f"• {txt}", tam=8.5, depois=0)


def conferencia_final(doc, ocorrencias):
    paragrafo(doc, "Conferência das regras", tam=13, negrito=True, cor=COR["titulo"])
    paragrafo(doc, "Exceção = regra ou meta não atendida (com o motivo) · Atenção = preferência não atendida "
                   "ou pendência · Aceita = situação prevista pelas regras", tam=8, cor="595959")
    lista = sorted(ocorrencias, key=lambda o: ORDEM[o["tipo"]])
    tab = doc.add_table(rows=1 + len(lista), cols=6)
    tab.style = "Table Grid"
    for c, t in enumerate(["Tipo", "Setor", "Quem / turno", "Data", "Regra", "Detalhe"]):
        escrever(tab.cell(0, c), t, negrito=True, fundo=COR["cinza"], tam=7.5)
    cores = {"Exceção": COR["alerta"], "Atenção": COR["dobra"], "Aceita": COR["fechado"]}
    for r, o in enumerate(lista, 1):
        for c, k in enumerate(("tipo", "setor", "pessoa", "data", "regra", "detalhe")):
            escrever(tab.cell(r, c), o[k], tam=6.5, centro=False, fundo=cores[o["tipo"]] if c == 0 else None)
    preparar_tabela(tab, [1.6, 2.6, 2.8, 1.2, 5.2, 14.7])


def gerar_word(caminho, escala, ocorrencias):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Arial"
    st.font.size = Pt(8)
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
    sec.left_margin = sec.right_margin = Cm(0.8)
    sec.top_margin = Cm(0.7)
    sec.bottom_margin = Cm(0.6)
    sec.header_distance = sec.footer_distance = Cm(0.3)
    rodape = sec.footer.paragraphs[0]
    rodape.text = f"Escala 5x2 · {PERIODO} · validar com o departamento pessoal antes de aplicar"
    rodape.runs[0].font.size = Pt(6.5)
    rodape.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    resumo(doc, escala)
    for setor, pessoas in escala.items():
        quebra(doc)
        calendario(doc, setor, pessoas)
    quebra(doc)
    conferencia_final(doc, ocorrencias)
    doc.save(caminho)

