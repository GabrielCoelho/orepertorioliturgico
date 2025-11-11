#!/usr/bin/env python3
"""
Script para extrair nomes de canais/compositores do YouTube
e atualizar automaticamente o post litúrgico.

Versão 2.0 - Com diagnóstico integrado

Requisitos:
    pip install yt-dlp

Uso:
    python extrair_nomes_youtube_v2.py [arquivo.md]
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yt_dlp

    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    print("⚠️  yt-dlp não está instalado. Instale com: pip install yt-dlp")


def encontrar_arquivo_markdown() -> str:
    """
    Procura o arquivo markdown no diretório atual e subdiretórios.
    """
    # Nomes possíveis do arquivo
    nomes_possiveis = [
        "dedicacao-basilica-latrao-para-revisar.md",
        "dedicacao-basilica-latrao.md",
    ]

    # Procurar no diretório atual
    for nome in nomes_possiveis:
        arquivo = Path(nome)
        if arquivo.exists():
            return str(arquivo)

    # Procurar em subdiretórios comuns
    for subdir in ["outputs", "posts", "content"]:
        for nome in nomes_possiveis:
            arquivo = Path(subdir) / nome
            if arquivo.exists():
                return str(arquivo)

    return ""


def extrair_video_id(url: str) -> str:
    """
    Extrai o ID do vídeo de uma URL do YouTube.
    """
    patterns = [
        r"youtu\.be/([^?&]+)",
        r"youtube\.com/watch\?v=([^&]+)",
        r"youtube\.com/shorts/([^?&]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            # Remover timestamp se existir
            video_id = match.group(1)
            if "?" in video_id:
                video_id = video_id.split("?")[0]
            return video_id

    return ""


def obter_info_video(video_id: str) -> Dict:
    """
    Obtém informações do vídeo usando yt-dlp.
    """
    if not YT_DLP_AVAILABLE:
        return {}

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://youtu.be/{video_id}", download=False)

            return {
                "channel": info.get("channel", info.get("uploader", "")),
                "title": info.get("title", ""),
                "uploader": info.get("uploader", ""),
            }
    except Exception as e:
        print(f"      ❌ Erro: {str(e)[:50]}")
        return {}


def extrair_links_do_markdown(arquivo: str) -> List[Tuple[str, str]]:
    """
    Extrai todos os links do arquivo markdown.

    Retorna lista de tuplas (texto_link, url)
    """
    links = []

    with open(arquivo, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Padrão atualizado para capturar links com emoji
    pattern = r"\[🔍 VERIFICAR NOME\]\((https://[^\)]+)\)"
    matches = re.findall(pattern, conteudo)

    for url in matches:
        links.append(("🔍 VERIFICAR NOME", url))

    return links


def processar_links(links: List[Tuple[str, str]]) -> Dict[str, str]:
    """
    Processa todos os links e retorna dicionário {url: nome_canal}.
    """
    resultados = {}
    total = len(links)

    print(f"\n📊 Processando {total} links...\n")

    for i, (texto, url) in enumerate(links, 1):
        video_id = extrair_video_id(url)

        if not video_id:
            print(f"⚠️  [{i}/{total}] URL inválida: {url}")
            continue

        print(f"⏳ [{i}/{total}] {video_id}...", end=" ")

        info = obter_info_video(video_id)

        if info and info.get("channel"):
            nome = info["channel"]
            resultados[url] = nome
            print(f"✅ {nome}")
        else:
            print(f"❌ Falhou")
            resultados[url] = "🔍 VERIFICAR MANUALMENTE"

    return resultados


def atualizar_markdown(
    arquivo_entrada: str, arquivo_saida: str, mapeamento: Dict[str, str]
):
    """
    Atualiza o arquivo markdown substituindo os placeholders pelos nomes reais.
    """
    with open(arquivo_entrada, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Substituir cada URL
    total_substituicoes = 0
    for url, nome in mapeamento.items():
        # Escapar caracteres especiais na URL para regex
        url_escaped = re.escape(url)

        # Padrão: [🔍 VERIFICAR NOME](url)
        pattern = r"\[🔍 VERIFICAR NOME\]\(" + url_escaped + r"\)"
        replacement = f"[{nome}]({url})"

        # Contar substituições
        novo_conteudo = re.sub(pattern, replacement, conteudo)
        if novo_conteudo != conteudo:
            total_substituicoes += 1
        conteudo = novo_conteudo

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(conteudo)

    return total_substituicoes


def salvar_relatorio(resultados: Dict[str, str], arquivo: str):
    """
    Salva um relatório JSON com os resultados.
    """
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)


def main():
    """Função principal."""
    print("=" * 70)
    print("🎵 EXTRATOR DE NOMES DE CANAIS DO YOUTUBE - v2.0")
    print("   Para Posts Litúrgicos")
    print("=" * 70)

    # Determinar arquivo de entrada
    if len(sys.argv) > 1:
        arquivo_entrada = sys.argv[1]
    else:
        arquivo_entrada = encontrar_arquivo_markdown()

    if not arquivo_entrada:
        print("\n❌ Erro: Arquivo markdown não encontrado!")
        print("\n📁 Arquivos .md disponíveis no diretório atual:")
        for f in Path(".").glob("*.md"):
            print(f"   • {f.name}")
        print(
            "\n💡 Dica: Execute o script com: python extrair_nomes_youtube_v2.py ARQUIVO.md"
        )
        return

    if not Path(arquivo_entrada).exists():
        print(f"\n❌ Erro: Arquivo '{arquivo_entrada}' não encontrado!")
        return

    print(f"\n✅ Arquivo encontrado: {arquivo_entrada}")

    # Configurações
    arquivo_saida = arquivo_entrada.replace("-para-revisar", "-corrigido")
    arquivo_relatorio = "relatorio_extracao.json"

    if not YT_DLP_AVAILABLE:
        print("\n⚠️  Não é possível continuar sem yt-dlp instalado.")
        print("   Instale com: pip install yt-dlp\n")
        return

    # Extrair links
    print(f"\n📄 Analisando arquivo...")
    links = extrair_links_do_markdown(arquivo_entrada)

    if not links:
        print("\n⚠️  Nenhum link encontrado no arquivo!")
        print("    Verifique se o arquivo contém links com o formato:")
        print("    [🔍 VERIFICAR NOME](https://youtu.be/...)")
        return

    print(f"✅ Encontrados {len(links)} links para processar")

    # Processar links
    resultados = processar_links(links)

    # Estatísticas
    sucesso = sum(1 for v in resultados.values() if v != "🔍 VERIFICAR MANUALMENTE")
    falhas = len(resultados) - sucesso

    print(f"\n" + "=" * 70)
    print(f"📊 ESTATÍSTICAS:")
    print(f"   ✅ Sucessos: {sucesso}/{len(links)}")
    print(f"   ❌ Falhas: {falhas}/{len(links)}")
    if falhas > 0:
        taxa = (sucesso / len(links)) * 100
        print(f"   📈 Taxa de sucesso: {taxa:.1f}%")
    print("=" * 70)

    # Atualizar markdown
    print(f"\n📝 Atualizando arquivo markdown...")
    num_substituicoes = atualizar_markdown(arquivo_entrada, arquivo_saida, resultados)
    print(f"✅ Arquivo salvo: {arquivo_saida}")
    print(f"   Realizadas {num_substituicoes} substituições")

    # Salvar relatório
    print(f"\n💾 Salvando relatório...")
    salvar_relatorio(resultados, arquivo_relatorio)
    print(f"✅ Relatório salvo: {arquivo_relatorio}")

    # Mensagem final
    print(f"\n" + "=" * 70)
    print("✅ PROCESSO CONCLUÍDO!")
    print(f"\n📄 Arquivos gerados:")
    print(f"   • {arquivo_saida}")
    print(f"   • {arquivo_relatorio}")

    if falhas > 0:
        print(f"\n⚠️  {falhas} link(s) precisam de verificação manual.")
        print(f"   Procure por '🔍 VERIFICAR MANUALMENTE' no arquivo gerado.")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
