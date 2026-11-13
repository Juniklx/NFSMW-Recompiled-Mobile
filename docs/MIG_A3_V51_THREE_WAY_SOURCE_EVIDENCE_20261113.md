# MIG-A3 — comparação autenticada PRE99 × V51 × fork v0.5.7

**Data:** 13/11/2026. **Status verificado:** `PASS_THREE_WAY_SOURCE_ONLY`.  
**Run independente no GitHub Actions:** https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43362701434 (completed/success, job `131679714249`).  
**Relatório:** https://drive.google.com/file/d/1Ab0uboQDlFpa2EiYh58xWQucoWpRvLDN/view (artifact GitHub `14009380825`, 2.562 bytes, SHA-256 `f86f53009b26bd139d76f87f6d5785b53de15c4559a7715050b48ef2360394d5`, CRC aprovado e Drive readback verificado).

## O que foi realmente executado

Runner descartável GitHub Actions, sem Kaggle, leu PRE99 do Google Drive e validou o SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39` antes de restaurar. Reproduziu as etapas PRE431/PRE638/PRE648/PRE652 usadas e autenticadas na PRE696. Capturou sete arquivos do PRE99 **antes** do replay e comparou bytes, SHA-256 e hunks com a fonte V51 após o replay e com o fork público no commit imutável `13373b70642a19adf232cd9ba39fc7ecb2275dc8`.

O código bruto das fontes, resultados de merge, APK, game assets, XEX e material de assinatura **não foram publicados**. O artefato contém somente hashes, tamanhos, contagens de hunks e classificação textual. O merge do Git é somente análise, `git merge-file -p`, e nenhum patch foi aplicado à fonte ativa.

## Resultado por arquivo

| Arquivo | Hunk PRE99→V51 | Hunks PRE99→fork | Classificação |
|---|---:|---:|---|
| `nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp` | 0 | 6 | Só fork alterado |
| `nativo/sdk/include/rex/ui/vulkan/presenter.h` | 0 | 3 | Só fork alterado |
| `nativo/app/src/nfsmw_ajustes_graficos.cpp` | 0 | 0 | Três versões idênticas |
| `nativo/app/src/nfsmw_nativo_sistema.cpp` | 0 | 3 | Só fork alterado |
| `nativo/app/src/nfsmw_nativo_destinos.cpp` | 0 | 26 | Só fork alterado |
| `android/app/src/main/java/io/github/nfsmwrecomp/MotorNativo.java` | 0 | 1 | Só fork alterado |
| `android/app/src/main/java/io/github/nfsmwrecomp/Ajustes.java` | 0 | 3 | Só fork alterado |

**Totais:** 7 arquivos, 0 alterados pela receita V51 desde PRE99, 6 alterados no fork, 1 idêntico em todas as versões, 0 arquivos com conflito textual de merge (7 merges limpos). Os hunk counts não são contagem de recursos ou correções; um hunk pode conter múltiplas linhas. Um merge textual limpo tampouco comprova equivalência funcional, ausência de regressão ou compilação.

### Decisão

**Preservar integralmente as versões atuais desses sete arquivos no fork**. Não há patch exclusivo da receita V51 a portar **dentro desse recorte**. Substituí-los pela cópia antiga da PRE99/V51 apagaria mudanças do fork sem benefício autenticado.

Essa conclusão **não cobre** arquivos efetivamente modificados nos stages PRE431/PRE638/PRE648/PRE652 (por exemplo o renderizador `nativo/app/src/nfsmw_nativo_dibujos.cpp`), Java/Android de controle e outras fontes que não estão entre os sete. Não é prova de equivalência byte a byte entre a receita V51 reconstruída e `libmain.so` assinada.

## Próximo gate MIG-A4

Inventariar **todos os arquivos de fonte** modificados na receita PRE99→V51 em runner descartável; identificar fontes antigas que não existem no fork, transformações já incorporadas pelo upstream e trechos exclusivos da V51. Excluir fontes geradas do jogo e conteúdo proprietário, chaves/credenciais, APKs, arquivos de save, ROM/ISO e shaders pré-compilados da publicação. Priorizar reconciliação do controle touch/iPega PG-9076 e do renderizador e correções de estabilidade comprovadas, antes de qualquer V52.

## Invariantes

A V51 instalada permanece intocada: pacote `io.github.nfsmwrecomp`, `versionCode=51`, certificado SHA-256 permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. O fork base v0.5.7 ainda não foi convertido em atualização assinável da V51. **Sem APK nova, sem build ARM64 completa, sem jogo executado neste gate e sem ganho de FPS demonstrado.** Preservar resolução 1920×1080, alvo 120 FPS, shaders/efeitos/física, saves, touch, controle iPega e proteções térmicas.
