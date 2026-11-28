# Gerador da escala 5×2 (30/11/2026 a 03/01/2027)

Monta a escala dos 29 colaboradores por setor e gera Excel, Word e PDF em
`escalas/2026-12_2027-01/`. Não faz parte do site: roda só no computador.

```bash
pip install ortools openpyxl python-docx
python3 ferramentas/escala-5x2/gerar.py
```

- `modelo.py`: equipe, horários, datas especiais e restrições de cada pessoa. **Para mudar uma regra, mexa aqui.**
- `otimizador.py`: escolhe folgas e dobras com o OR-Tools (CP-SAT). Regras obrigatórias são restrições;
  metas e preferências viram pontos de problema com pesos na ordem de prioridade do pedido.
- `conferencia.py`: confere a escala pronta regra por regra (lista no Resumo geral e no fim do Word/PDF).
- `exportar_excel.py` e `exportar_word.py`: montam os arquivos. O PDF é convertido do Word pelo LibreOffice.

Planilha: 01 Resumo geral · 02 Bar · 03 Sushi · 04 Salão · 05 Cozinha · 06 Pia · 07 Refeitório · 08 Regras.
As cores e os totalizadores usam fórmulas: trocar uma célula à mão atualiza tudo.
