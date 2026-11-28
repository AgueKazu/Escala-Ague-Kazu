"""Gera a escala 5x2 (30/11/2026 a 31/01/2027) em Excel, Word e PDF.

Uso (na raiz do projeto):
    python3 ferramentas/escala-5x2/gerar.py

Os arquivos saem em escalas/2026-12_2027-01/.
Precisa de Python 3 com openpyxl e python-docx; o PDF usa o LibreOffice (soffice).
"""

import collections
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from apresentacao import traduzir  # noqa: E402
from conferencia import conferir  # noqa: E402
from exportar_excel import gerar_excel  # noqa: E402
from exportar_word import gerar_word  # noqa: E402
from modelo import SETORES  # noqa: E402
from otimizador import montar_escala  # noqa: E402

PASTA = os.path.join(AQUI, "..", "..", "escalas", "2026-12_2027-01")
NOME = "escala-5x2-dez2026-jan2027"

# Por que cada exceção restante não tem solução (conflito entre as próprias regras)
MOTIVOS = {
    ("Cozinha", "Máximo de 2 da manhã de folga"):
        "Conflito entre regras: Edna folga todo sábado e domingo e Moura toda segunda e terça; "
        "na semana do Natal (25/12 fechado) sobram 6 dias para 14 folgas da manhã, e todo domingo "
        "só cabe mais 1 da manhã de folga além da Edna.",
    ("Cozinha", "Domingos de folga (Dez)"):
        "Moura já folga segunda e terça (folgas fixas); um domingo de folga daria 3 folgas na semana.",
    ("Cozinha", "Domingos de folga (Jan)"):
        "Edna folga todos os domingos e o limite é 2 da manhã de folga por dia: sobra 1 vaga por "
        "domingo para 6 homens da manhã.",
    ("Salão", "Mínimo de 5 no salão"):
        "Em dezembro há 4 domingos para 9 folgas de domingo no salão (Elaine e Sivanilda 2 cada, "
        "os 5 homens 1 cada): pelo menos um domingo fica com 4.",
}


def main():
    os.makedirs(PASTA, exist_ok=True)
    print("Montando a escala (leva cerca de 2 minutos)...")
    escala, pontos = montar_escala()
    print("Pontuação de problemas por setor:", pontos)

    ocorrencias = conferir(escala)
    for o in ocorrencias:
        motivo = MOTIVOS.get((o["setor"], o["regra"]))
        if o["tipo"] == "Exceção" and motivo:
            o["detalhe"] = f"{o['detalhe']} {motivo}"
    resumo = collections.Counter(o["tipo"] for o in ocorrencias)
    print("Conferência:", dict(resumo))

    setores = [(s, list(escala[s].keys())) for s, _ in SETORES]
    xlsx = os.path.join(PASTA, NOME + ".xlsx")
    docx = os.path.join(PASTA, NOME + ".docx")
    impressa = traduzir(escala)
    abas, pendencias = gerar_excel(xlsx, impressa, setores, ocorrencias)
    gerar_word(docx, impressa, setores, ocorrencias)
    print(f"Excel: {abas} abas, {pendencias} pendências · Word gerado")

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", PASTA, docx],
                       check=True, capture_output=True)
        print("PDF gerado")
    else:
        print("LibreOffice não encontrado: PDF não gerado")


if __name__ == "__main__":
    main()
