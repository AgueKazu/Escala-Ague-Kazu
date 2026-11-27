const fs=require('fs');const d=require('docx');
const o=JSON.parse(fs.readFileSync('escala.json','utf8'));
const COR={data:"D9D9D9",folga:"FF6B6B",fechado:"7FD17F",dobra:"FFB347",domingo:"F8BBD9",normal:"FFFFFF",cab:"404040"};
const SEM=["Dom","Seg","Ter","Qua","Qui","Sex","Sáb"];
const setores=["Bar","Sushi","Salão","Cozinha","Pia","Refeitório"];
const W=15398-2*567; // A4 paisagem, margem 1cm
const b={style:d.BorderStyle.SINGLE,size:2,color:"999999"};const borders={top:b,bottom:b,left:b,right:b};
function cel(txt,cor,w,sz,bold,branco){return new d.TableCell({width:{size:w,type:d.WidthType.DXA},borders,
  shading:{fill:cor,type:d.ShadingType.CLEAR,color:"auto"},margins:{top:20,bottom:20,left:30,right:30},verticalAlign:d.VerticalAlign.CENTER,
  children:String(txt).split("\n").map(t=>new d.Paragraph({alignment:d.AlignmentType.CENTER,spacing:{before:0,after:0},children:[new d.TextRun({text:t,font:"Arial",size:sz,bold,color:branco?"FFFFFF":"000000"})]}))});}
const filhos=[];let primeiro=true;
for(const st of setores){
  const ps=o.pessoas.filter(p=>p.setor==st);
  for(const [mes,titulo] of [[12,"DEZEMBRO/2026 (inclui 30/11)"],[1,"JANEIRO/2027"]]){
    const idx=o.dias.map((x,i)=>i).filter(i=>{const m=+o.dias[i].slice(5,7);return mes==12?m!=1:m==1;});
    const wd=1000,wdia=600,wp=Math.floor((W-wd-wdia)/ps.length);const tot=wd+wdia+wp*ps.length;
    const sz=ps.length>8?13:16;
    const linhas=[new d.TableRow({tableHeader:true,children:[cel("Data",COR.cab,wd,sz,true,true),cel("Dia",COR.cab,wdia,sz,true,true),...ps.map(p=>cel((st=="Cozinha"?(p.grupo=="Manhã"?"☀ ":"☾ "):"")+p.nome+"\n"+p.h,COR.cab,wp,sz,true,true))]})];
    for(const i of idx){const [y,m,dd]=o.dias[i].split("-");const dow=new Date(o.dias[i]+"T12:00:00").getDay();
      linhas.push(new d.TableRow({cantSplit:true,children:[cel(`${dd}/${m}/${y}`,COR.data,wd,sz,dow==0),cel(SEM[dow],COR.data,wdia,sz,dow==0),
        ...ps.map(p=>{const [t,k]=o.celulas[p.id][i];return cel(t.replace("DOBRA ","DOBRA\n"),COR[k],wp,sz,k=="folga"||k=="fechado");})]}));}
    filhos.push(new d.Paragraph({pageBreakBefore:!primeiro,spacing:{after:60},children:[new d.TextRun({text:`ESCALA 5x2 · ${st.toUpperCase()} · ${titulo}`,font:"Arial",size:26,bold:true})]}));
    primeiro=false;
    filhos.push(new d.Paragraph({spacing:{after:100},children:[
      ...[["Data","D9D9D9"],["Folga","FF6B6B"],["Feriado/fechado","7FD17F"],["Dobra 11:45–23:00 (2h intervalo)","FFB347"],["Domingo 10:30–19:54","F8BBD9"]].flatMap(([t,c])=>[
        new d.TextRun({text:"  "+t+"  ",font:"Arial",size:16,shading:{fill:c,type:d.ShadingType.CLEAR,color:"auto"}}),new d.TextRun({text:"   ",size:16})]),
      ...(st=="Cozinha"?[new d.TextRun({text:"  ☀ manhã  ☾ noite",font:"Arial",size:16})]:[])]}));
    filhos.push(new d.Table({width:{size:tot,type:d.WidthType.DXA},columnWidths:[wd,wdia,...ps.map(()=>wp)],rows:linhas}));
  }
}
const doc=new d.Document({sections:[{properties:{page:{size:{width:11906,height:16838,orientation:d.PageOrientation.LANDSCAPE},margin:{top:567,bottom:567,left:567,right:567}}},children:filhos}]});
d.Packer.toBuffer(doc).then(buf=>fs.writeFileSync(process.argv[2],buf));
