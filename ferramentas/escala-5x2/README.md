# Gerador da escala 5×2 (dez/2026 e jan/2027)

Monta a escala dos 29 colaboradores por setor e gera Excel, Word e PDF em
`escalas/2026-12_2027-01/`. Não faz parte do site: roda só no computador.

```bash
python3 ferramentas/escala-5x2/gerar.py
```

- `modelo.py`: equipe, horários, datas especiais e restrições de cada pessoa. **Para mudar uma regra, mexa aqui.**
- `otimizador.py`: escolhe as folgas (busca local) e distribui as dobras.
- `conferencia.py`: confere a escala pronta regra por regra (aba Conferência).
- `apresentacao.py`: códigos impressos (M, N, I, S, D, DS, F, H), cores, textos das regras e agrupamento das pendências.
- `exportar_excel.py` (14 abas: Regras, Pendências e 12 calendários) e `exportar_word.py` (13 páginas A4 deitado): montam os arquivos.

Precisa de Python 3 com `openpyxl` e `python-docx`. O PDF usa o LibreOffice.
