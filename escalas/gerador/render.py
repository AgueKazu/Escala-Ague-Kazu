from grade import *
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
os.makedirs(OUT, exist_ok=True)
G = grade()
ORDEM = ['Bar', 'Sushi', 'Salão', 'Cozinha', 'Pia', 'Refeitório']
MESES = [('Dezembro/2026', range(1, 32)), ('Janeiro/2027', range(32, 63))]
SEM = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']
COR = {'cinza': 'D9D9D9', 'F': 'E53935', 'FEC': '43A047', 'D': 'FB8C00', 'DOM': 'F8BBD0', 'T': 'FFFFFF'}
TXT = {'T': '', 'F': 'F', 'FEC': 'FER', 'D': 'D', 'DOM': 'DOM'}
FONTE_BRANCA = {'F', 'FEC', 'D'}
NOMES_SETOR = {'Cozinha': 'Cozinha (manhã e noite)'}

def linhas(setor):
    """Lista de ('grupo', titulo) ou ('pessoa', nome)."""
    g = G[setor]
    if setor == 'Cozinha':
        out = [('grupo', 'Turno da manhã')] + [('pessoa', p.nome) for p in coz if p.turno == 'M']
        out += [('grupo', 'Turno da noite')] + [('pessoa', p.nome) for p in coz if p.turno == 'N']
        return out
    return [('pessoa', n) for n in g]

def contagem(setor, i):
    g = G[setor]
    if i in FECHADO: return None
    if setor == 'Cozinha':
        m = sum(1 for p in coz if (p.turno == 'M' and g[p.nome][i] in ('T', 'D', 'DOM')) or (p.turno == 'N' and g[p.nome][i] == 'D'))
        n = sum(1 for p in coz if (p.turno == 'N' and g[p.nome][i] in ('T', 'D', 'DOM')) or (p.turno == 'M' and g[p.nome][i] == 'D'))
        return m, n
    return sum(1 for r in g.values() if r[i] in ('T', 'D', 'DOM'))

LEGENDA = [('F', 'Folga'), ('FEC', 'Feriado / restaurante fechado (25/12 e 01/01) – não conta como folga'),
           ('D', 'Dobra 11:45–23:00 (2h de intervalo)'), ('DOM', 'Domingo trabalhado 10:30–19:54')]
OBS = ['30/11 (segunda) conta como folga de todos na semana de 30/11 a 06/12.',
       '31/12 e 02/01 são folga de todos e contam como as 2 folgas da semana. 03/01 é o 1º domingo de janeiro.',
       'Célula em branco = dia normal de trabalho no horário da pessoa.']
OBS_SETOR = {
 'Bar': ['Domingo fixo de folga: Rafael 4º domingo (27/12 e 24/01); Vinicius 3º domingo (20/12 e 17/01).',
         'Quando um folga, o outro faz dobra. Os dois nunca folgam no mesmo dia.'],
 'Sushi': ['Domingo fixo de folga: Diogo 3º domingo (20/12 e 17/01); Allan 4º domingo (27/12 e 24/01).',
           'Quando um folga, o outro faz dobra. Os dois nunca folgam no mesmo dia.'],
 'Salão': ['Mulheres com 2 domingos de folga por mês, a cada 15 dias; homens com 1.',
           'Elaine e Marcos nunca folgam juntos; Guilherme e Adriano nunca folgam juntos.',
           'Nos dias de folga da Juliana, ficam pelo menos 5 pessoas trabalhando. Sivanilda folga 19/12 e Marcos 26/12.'],
 'Cozinha': ['Manhã sempre com 7 e noite sempre com 6 (segunda a sábado): quem falta é coberto por dobra do outro turno.',
             'Rony, Edna e Moura não fazem dobra; Rafael não faz dobra às terças e quartas.',
             'Moura folga toda segunda e terça; Edna folga todo sábado e domingo; Miro folga 07/12, 21/12, 04/01 e 18/01 (segundas) e no 4º domingo.',
             'Rafael folga no 3º domingo. Miro, Rafael e Chef nunca folgam no mesmo dia. Domingos (10:30–19:54) sem dobra.'],
 'Pia': ['Daniel cobre as folgas da Ilma (com dobra) e da Claudia. Ilma e Claudia nunca folgam no mesmo dia.',
         'Mulheres com 2 domingos de folga por mês, a cada 15 dias; Daniel com 1.'],
 'Refeitório': ['Joelma nunca folga no mesmo dia que o Rafael da cozinha e não folga aos sábados (exceto 02/01, folga de todos).',
                '2 domingos de folga por mês, a cada 15 dias.'],
}

# ===================== EXCEL =====================
def fill(c): return PatternFill('solid', start_color=c, end_color=c)
fino = Side(style='thin', color='9E9E9E')
borda = Border(left=fino, right=fino, top=fino, bottom=fino)
centro = Alignment(horizontal='center', vertical='center', wrap_text=True)

wb = Workbook(); wb.remove(wb.active)
for setor in ORDEM:
    ws = wb.create_sheet(setor)
    ws.sheet_view.zoomScale = 90
    ws.column_dimensions['A'].width = 13
    ws.column_dimensions['B'].width = 20
    for c in range(3, 34): ws.column_dimensions[get_column_letter(c)].width = 5.2
    ws.column_dimensions[get_column_letter(34)].width = 8
    ws.column_dimensions[get_column_letter(35)].width = 8
    r = 1
    ws.cell(r, 1, f'Escala 5x2 – {NOMES_SETOR.get(setor, setor)}').font = Font(bold=True, size=14)
    r += 2
    for titulo, dias in MESES:
        dias = list(dias)
        ws.cell(r, 1, titulo).font = Font(bold=True, size=12); r += 1
        cab = ['Funcionário', 'Horário'] + [DATAS[i].strftime('%d/%m') for i in dias] + ['Folgas no mês', 'Dobras no mês']
        for j, v in enumerate(cab, 1):
            c = ws.cell(r, j, v); c.fill = fill(COR['cinza']); c.font = Font(bold=True, size=9); c.alignment = centro; c.border = borda
        ws.row_dimensions[r].height = 28
        r += 1
        for j, i in enumerate(dias, 3):
            c = ws.cell(r, j, SEM[i % 7]); c.fill = fill(COR['cinza']); c.font = Font(bold=True, size=8); c.alignment = centro; c.border = borda
        for j in (1, 2, 34, 35):
            c = ws.cell(r, j); c.fill = fill(COR['cinza']); c.border = borda
        r += 1
        for tipo, nome in linhas(setor):
            if tipo == 'grupo':
                ws.cell(r, 1, nome).font = Font(bold=True, italic=True)
                r += 1; continue
            row = G[setor][nome]
            ws.cell(r, 1, nome).font = Font(bold=True)
            ws.cell(r, 2, HOR[setor][nome]).font = Font(size=9)
            for j in (1, 2): ws.cell(r, j).border = borda; ws.cell(r, j).alignment = Alignment(vertical='center')
            for j, i in enumerate(dias, 3):
                st = row[i]
                c = ws.cell(r, j, TXT[st]); c.alignment = centro; c.border = borda
                cor = COR['DOM'] if (st == 'T' and i % 7 == 6) else COR[st]
                c.fill = fill(cor)
                c.font = Font(bold=True, size=9, color='FFFFFF' if st in FONTE_BRANCA else '000000')
            nf = sum(1 for i in dias if row[i] == 'F'); nd = sum(1 for i in dias if row[i] == 'D')
            for j, v in ((34, nf), (35, nd)):
                c = ws.cell(r, j, v); c.alignment = centro; c.border = borda; c.font = Font(bold=True)
            r += 1
        # linhas de contagem
        if setor == 'Cozinha':
            for k, rot in enumerate(['Manhã (meta 7)', 'Noite (meta 6)']):
                ws.cell(r, 1, rot).font = Font(italic=True, size=9)
                for j, i in enumerate(dias, 3):
                    v = contagem(setor, i)
                    c = ws.cell(r, j, '' if v is None else v[k]); c.alignment = centro; c.font = Font(size=8, italic=True)
                r += 1
        elif len(G[setor]) > 2:
            ws.cell(r, 1, 'Trabalhando').font = Font(italic=True, size=9)
            for j, i in enumerate(dias, 3):
                v = contagem(setor, i)
                c = ws.cell(r, j, '' if v is None else v); c.alignment = centro; c.font = Font(size=8, italic=True)
            r += 1
        r += 1
    ws.cell(r, 1, 'Legenda').font = Font(bold=True); r += 1
    for st, txt in LEGENDA:
        c = ws.cell(r, 1, TXT[st]); c.fill = fill(COR[st]); c.alignment = centro; c.border = borda
        c.font = Font(bold=True, color='FFFFFF' if st in FONTE_BRANCA else '000000')
        ws.cell(r, 2, txt); r += 1
    c = ws.cell(r, 1, 'dd/mm'); c.fill = fill(COR['cinza']); c.alignment = centro; c.border = borda
    ws.cell(r, 2, 'Datas'); r += 2
    ws.cell(r, 1, 'Observações').font = Font(bold=True); r += 1
    for o in OBS_SETOR[setor] + OBS:
        ws.cell(r, 1, '• ' + o); r += 1
    ws.freeze_panes = 'C1'
    ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
wb.save(f'{OUT}/escala-dez2026-jan2027.xlsx')

# ===================== WORD =====================
def sombrear(cell, cor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), cor)
    tcPr.append(shd)
def margens_cel(tabela, v=20):
    tblPr = tabela._tbl.tblPr
    m = OxmlElement('w:tblCellMar')
    for lado in ('top', 'left', 'bottom', 'right'):
        e = OxmlElement(f'w:{lado}'); e.set(qn('w:w'), str(v)); e.set(qn('w:type'), 'dxa'); m.append(e)
    tblPr.append(m)
def escrever(cell, txt, tam=6, neg=False, branco=False, ital=False, alin=WD_ALIGN_PARAGRAPH.CENTER):
    p = cell.paragraphs[0]; p.alignment = alin
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
    run = p.add_run(str(txt)); run.font.size = Pt(tam); run.bold = neg; run.italic = ital
    if branco: run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

doc = Document()
st = doc.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(8)
sec = doc.sections[0]
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
for a in ('left_margin', 'right_margin'): setattr(sec, a, Cm(0.8))
for a in ('top_margin', 'bottom_margin'): setattr(sec, a, Cm(0.8))
LARG = [Cm(1.9), Cm(2.9)] + [Cm(0.67)] * 31 + [Cm(0.9), Cm(0.9)]

for k, setor in enumerate(ORDEM):
    if k: doc.add_page_break()
    h = doc.add_paragraph(); r_ = h.add_run(f'Escala 5x2 – {NOMES_SETOR.get(setor, setor)}'); r_.bold = True; r_.font.size = Pt(14)
    h.paragraph_format.space_after = Pt(2)
    for mi, (titulo, dias) in enumerate(MESES):
        dias = list(dias)
        if setor == 'Cozinha' and mi == 1: doc.add_page_break()
        p = doc.add_paragraph(); rr = p.add_run(titulo); rr.bold = True; rr.font.size = Pt(10)
        p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(2)
        ls = linhas(setor)
        extra = 2 if setor == 'Cozinha' else (1 if len(G[setor]) > 2 else 0)
        t = doc.add_table(rows=2 + len(ls) + extra, cols=35)
        t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
        margens_cel(t)
        for j, w in enumerate(LARG):
            for row in t.rows: row.cells[j].width = w
        lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); t._tbl.tblPr.append(lay)
        for gc, w in zip(t._tbl.tblGrid.findall(qn('w:gridCol')), LARG): gc.set(qn('w:w'), str(int(w.twips)))
        cab = ['Funcionário', 'Horário'] + [DATAS[i].strftime('%d/%m') for i in dias] + ['Folgas', 'Dobras']
        for j, v in enumerate(cab):
            c = t.cell(0, j); sombrear(c, COR['cinza']); escrever(c, v, 5.5 if 2 <= j < 33 else 6.5, True)
        for j in range(35):
            c = t.cell(1, j); sombrear(c, COR['cinza'])
            if 2 <= j < 33: escrever(c, SEM[dias[j-2] % 7], 5.5, True)
        ri = 2
        for tipo, nome in ls:
            if tipo == 'grupo':
                c = t.cell(ri, 0).merge(t.cell(ri, 34)); escrever(c, nome, 7, True, ital=True, alin=WD_ALIGN_PARAGRAPH.LEFT)
                ri += 1; continue
            row = G[setor][nome]
            escrever(t.cell(ri, 0), nome, 7, True, alin=WD_ALIGN_PARAGRAPH.LEFT)
            escrever(t.cell(ri, 1), HOR[setor][nome].replace(' int.', ''), 5.5, alin=WD_ALIGN_PARAGRAPH.LEFT)
            for j, i in enumerate(dias, 2):
                s = row[i]; c = t.cell(ri, j)
                cor = COR['DOM'] if (s == 'T' and i % 7 == 6) else COR[s]
                if cor != 'FFFFFF': sombrear(c, cor)
                escrever(c, TXT[s], 5.5, True, branco=s in FONTE_BRANCA)
            escrever(t.cell(ri, 33), sum(1 for i in dias if row[i] == 'F'), 7, True)
            escrever(t.cell(ri, 34), sum(1 for i in dias if row[i] == 'D'), 7, True)
            ri += 1
        rots = ['Manhã (7)', 'Noite (6)'] if setor == 'Cozinha' else (['Trabalhando'] if extra else [])
        for kk, rot in enumerate(rots):
            c = t.cell(ri, 0).merge(t.cell(ri, 1)); escrever(c, rot, 6, ital=True, alin=WD_ALIGN_PARAGRAPH.LEFT)
            for j, i in enumerate(dias, 2):
                v = contagem(setor, i)
                if v is not None: escrever(t.cell(ri, j), v[kk] if setor == 'Cozinha' else v, 5.5, ital=True)
            ri += 1
    # legenda
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(0)
    itens = LEGENDA + [('cinza', 'Datas')]
    for s_, txt in itens:
        rn = p.add_run(f' {TXT.get(s_, "dd/mm")} '); rn.bold = True; rn.font.size = Pt(7)
        if s_ in FONTE_BRANCA: rn.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), COR[s_])
        rn._r.get_or_add_rPr().append(shd)
        rt = p.add_run(f' {txt}     '); rt.font.size = Pt(7)
    for o in OBS_SETOR[setor] + OBS:
        q = doc.add_paragraph('• ' + o); q.paragraph_format.space_after = Pt(0)
        for rn in q.runs: rn.font.size = Pt(7)
doc.save(f'{OUT}/escala-dez2026-jan2027.docx')
print('ok')
