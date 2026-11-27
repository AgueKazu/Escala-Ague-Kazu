import json,datetime as dt,sys
from openpyxl import Workbook
from openpyxl.styles import PatternFill,Font,Alignment,Border,Side
from openpyxl.utils import get_column_letter as L
o=json.load(open("escala.json"));D=[dt.date.fromisoformat(x) for x in o["dias"]]
COR={"data":"D9D9D9","folga":"FF6B6B","fechado":"7FD17F","dobra":"FFB347","domingo":"F8BBD9","normal":"FFFFFF","cab":"404040"}
fill=lambda c:PatternFill("solid",start_color=c,end_color=c)
fina=Side(style="thin",color="999999");borda=Border(left=fina,right=fina,top=fina,bottom=fina)
SEM=["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]
MES={11:"NOVEMBRO 2026",12:"DEZEMBRO 2026",1:"JANEIRO 2027"}
setores=["Bar","Sushi","Salão","Cozinha","Pia","Refeitório"]
wb=Workbook();wb.remove(wb.active)
F=lambda **k:Font(name="Arial",**k)
c_=Alignment(horizontal="center",vertical="center",wrap_text=True)
for st in setores:
    ps=[p for p in o["pessoas"] if p["setor"]==st]
    ws=wb.create_sheet(st)
    cozinha = st=="Cozinha"
    ncol=2+len(ps)+(2 if cozinha else 0)
    ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=ncol)
    ws["A1"]=f"ESCALA 5x2 · {st.upper()} · DEZEMBRO/2026 E JANEIRO/2027";ws["A1"].font=F(bold=True,size=14);ws["A1"].alignment=c_
    ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=ncol)
    ws["A2"]="Legenda: cinza = data · vermelho = folga · verde = feriado/fechado · laranja = dobra (11:45–23:00, 2h de intervalo) · rosa = domingo (10:30–19:54)"
    ws["A2"].font=F(size=9,italic=True);ws["A2"].alignment=c_
    r=4
    if cozinha:
        ws.cell(r-1,3,"TURNO DA MANHÃ");ws.merge_cells(start_row=r-1,start_column=3,end_row=r-1,end_column=9)
        ws.cell(r-1,10,"TURNO DA NOITE");ws.merge_cells(start_row=r-1,start_column=10,end_row=r-1,end_column=15)
        ws.cell(r-1,16,"COBERTURA");ws.merge_cells(start_row=r-1,start_column=16,end_row=r-1,end_column=17)
        for cc in (3,10,16): ws.cell(r-1,cc).font=F(bold=True,color="FFFFFF");ws.cell(r-1,cc).fill=fill("7F7F7F");ws.cell(r-1,cc).alignment=c_
    cab=["Data","Dia"]+[f"{p['nome']}\n{p['h']}" for p in ps]+(["Manhã\n(meta 7)","Noite\n(meta 6)"] if cozinha else [])
    for j,t in enumerate(cab,1):
        x=ws.cell(r,j,t);x.font=F(bold=True,color="FFFFFF",size=10);x.fill=fill(COR["cab"]);x.alignment=c_;x.border=borda
    ws.row_dimensions[r].height=32
    r+=1;linhas={12:[],1:[]};mes_ant=None
    for i,d in enumerate(D):
        mk=12 if d.month in(11,12) else 1
        if d.month!=mes_ant and d.month!=12:
            if d.month==1:
                ws.cell(r,1,MES[1]);ws.merge_cells(start_row=r,start_column=1,end_row=r,end_column=ncol)
                ws.cell(r,1).font=F(bold=True,color="FFFFFF");ws.cell(r,1).fill=fill("7F7F7F");ws.cell(r,1).alignment=c_;r+=1
        mes_ant=d.month
        a=ws.cell(r,1,d);a.number_format="DD/MM/YYYY"
        b=ws.cell(r,2,SEM[d.weekday()])
        for x in (a,b): x.fill=fill(COR["data"]);x.font=F(bold=d.weekday()==6,size=10);x.alignment=c_;x.border=borda
        for j,p in enumerate(ps,3):
            t,k=o["celulas"][p["id"]][i]
            x=ws.cell(r,j,t);x.fill=fill(COR[k]);x.font=F(size=10,bold=k in("folga","fechado"));x.alignment=c_;x.border=borda
        if cozinha:
            m1,m2,n1,n2=L(3),L(9),L(10),L(15)
            fm=f'=IF(OR(B{r}="Dom",C{r}="FECHADO",C{r}="FOLGA"),"",COUNTIFS({m1}{r}:{m2}{r},"<>FOLGA")+COUNTIF({n1}{r}:{n2}{r},"DOBRA*"))'
            fn=f'=IF(OR(B{r}="Dom",C{r}="FECHADO",C{r}="FOLGA"),"",COUNTIFS({n1}{r}:{n2}{r},"<>FOLGA")+COUNTIF({m1}{r}:{m2}{r},"DOBRA*"))'
            for jj,f in ((16,fm),(17,fn)):
                x=ws.cell(r,jj,f);x.alignment=c_;x.border=borda;x.font=F(size=10,bold=True)
        linhas[mk].append(r);r+=1
    # resumo
    r+=1
    ws.cell(r,1,"RESUMO (calculado pela planilha)").font=F(bold=True,size=11);r+=1
    itens=[("Folgas dez (30/11–31/12)",12,'"FOLGA"'),("Folgas jan",1,'"FOLGA"'),("Dobras dez",12,'"DOBRA*"'),("Dobras jan",1,'"DOBRA*"')]
    for nome,mk,crit in itens:
        ws.cell(r,1,nome).font=F(bold=True,size=10);ws.merge_cells(start_row=r,start_column=1,end_row=r,end_column=2)
        a,b=linhas[mk][0],linhas[mk][-1]
        for j,p in enumerate(ps,3):
            x=ws.cell(r,j,f"=COUNTIF({L(j)}{a}:{L(j)}{b},{crit})");x.alignment=c_;x.border=borda;x.font=F(size=10)
        r+=1
    for nome,mk in (("Domingos de folga dez",12),("Domingos de folga jan",1)):
        ws.cell(r,1,nome).font=F(bold=True,size=10);ws.merge_cells(start_row=r,start_column=1,end_row=r,end_column=2)
        a,b=linhas[mk][0],linhas[mk][-1]
        for j,p in enumerate(ps,3):
            x=ws.cell(r,j,f'=COUNTIFS($B{a}:$B{b},"Dom",{L(j)}{a}:{L(j)}{b},"FOLGA")');x.alignment=c_;x.border=borda;x.font=F(size=10)
        r+=1
    ws.column_dimensions["A"].width=12;ws.column_dimensions["B"].width=6
    for j in range(3,ncol+1): ws.column_dimensions[L(j)].width=13 if not cozinha else 11.5
    ws.freeze_panes="C5"
    ws.page_setup.orientation="landscape";ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
    ws.sheet_properties.pageSetUpPr.fitToPage=True;ws.print_title_rows="4:4"
wb.save(sys.argv[1])
