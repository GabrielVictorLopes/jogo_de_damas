"""Instalador do Jogo de Damas.

Baixa a última versão publicada no GitHub (aba Releases), instala em
%LOCALAPPDATA%\\JogoDeDamas, cria um atalho na área de trabalho e abre o jogo.
Usa só a biblioteca padrão do Python.
"""
import os
import shutil
import subprocess
import tempfile
import threading
import urllib.request
import zipfile

URL = "https://github.com/GabrielVictorLopes/jogo_de_damas/releases/latest/download/Damas.zip"
NOME_EXE = "Damas.exe"


def pasta_instalacao() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "JogoDeDamas")


def achar_exe(pasta: str):
    """Procura o Damas.exe dentro da pasta (aceita ZIP com ou sem subpasta)."""
    for raiz, _, arquivos in os.walk(pasta):
        if NOME_EXE in arquivos:
            return os.path.join(raiz, NOME_EXE)
    return None


def baixar(url: str, destino: str, progresso=lambda feito, total: None) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "InstaladorDamas"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(destino, "wb") as arq:
        total = int(resp.headers.get("Content-Length") or 0)
        feito = 0
        while True:
            bloco = resp.read(64 * 1024)
            if not bloco:
                break
            arq.write(bloco)
            feito += len(bloco)
            progresso(feito, total)


def instalar(url: str, pasta: str, progresso=lambda feito, total: None, status=lambda msg: None) -> str:
    """Baixa o ZIP, extrai e troca a versão antiga pela nova. Retorna o caminho do .exe."""
    os.makedirs(os.path.dirname(pasta), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        arquivo_zip = os.path.join(tmp, "Damas.zip")
        status("Baixando o jogo...")
        baixar(url, arquivo_zip, progresso)
        status("Instalando...")
        novo = os.path.join(tmp, "novo")
        with zipfile.ZipFile(arquivo_zip) as z:
            z.extractall(novo)
        if not achar_exe(novo):
            raise RuntimeError("O arquivo baixado não contém o Damas.exe.")
        if os.path.isdir(pasta):
            shutil.rmtree(pasta)  # só depois do download dar certo
        shutil.move(novo, pasta)
    return achar_exe(pasta)


def criar_atalho(exe: str) -> bool:
    """Cria 'Jogo de Damas.lnk' na área de trabalho (Windows). Falhar aqui não atrapalha a instalação."""
    alvo = exe.replace("'", "''")
    pasta = os.path.dirname(exe).replace("'", "''")
    script = ("$d=[Environment]::GetFolderPath('Desktop');"
              "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($d+'\\Jogo de Damas.lnk');"
              f"$s.TargetPath='{alvo}';$s.WorkingDirectory='{pasta}';$s.Save()")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True, timeout=30,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    except Exception:
        return False


def abrir(exe: str) -> None:
    subprocess.Popen([exe], cwd=os.path.dirname(exe))


def main() -> None:
    import tkinter as tk
    from tkinter import ttk

    janela = tk.Tk()
    janela.title("Instalar Jogo de Damas")
    janela.geometry("440x230")
    janela.resizable(False, False)

    estado = {"msg": "Pronto para baixar o jogo.", "feito": 0, "total": 0, "fim": None, "erro": None}
    rotulo = ttk.Label(janela, text=estado["msg"], font=("Segoe UI", 11), justify="center")
    rotulo.pack(pady=(22, 8))
    barra = ttk.Progressbar(janela, length=380, mode="determinate")
    barra.pack(pady=4)
    quer_atalho = tk.BooleanVar(value=True)
    ttk.Checkbutton(janela, text="Criar atalho na área de trabalho", variable=quer_atalho).pack(pady=10)
    botao = ttk.Button(janela, text="Instalar e jogar")
    botao.pack(pady=4)

    def progresso(feito, total):
        estado["feito"], estado["total"] = feito, total

    def status(msg):
        estado["msg"] = msg

    def trabalho():
        try:
            exe = instalar(URL, pasta_instalacao(), progresso, status)
            if quer_atalho.get():
                criar_atalho(exe)
            estado["fim"] = exe
        except Exception as erro:  # sem internet, release não publicado, zip inválido...
            estado["erro"] = erro

    def iniciar():
        botao.config(state="disabled")
        estado.update(msg="Conectando...", feito=0, total=0, fim=None, erro=None)
        threading.Thread(target=trabalho, daemon=True).start()
        atualizar()

    def atualizar():
        rotulo.config(text=estado["msg"])
        if estado["total"]:
            barra.config(maximum=estado["total"], value=estado["feito"])
        if estado["fim"]:
            exe = estado["fim"]
            rotulo.config(text="Instalado! Bom jogo.")
            botao.config(text="Jogar", state="normal", command=lambda: (abrir(exe), janela.destroy()))
        elif estado["erro"]:
            instalado = achar_exe(pasta_instalacao())
            rotulo.config(text="Não consegui baixar o jogo.\nConfira a internet e tente de novo.")
            if instalado:
                botao.config(text="Jogar a versão já instalada", state="normal",
                             command=lambda: (abrir(instalado), janela.destroy()))
            else:
                botao.config(text="Tentar de novo", state="normal", command=iniciar)
        else:
            janela.after(100, atualizar)

    botao.config(command=iniciar)
    janela.mainloop()


if __name__ == "__main__":
    main()
