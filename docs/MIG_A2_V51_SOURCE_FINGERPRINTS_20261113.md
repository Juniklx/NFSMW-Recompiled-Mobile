# MIG-A2 — comparação de fingerprints V51 vs fork v0.5.7

**Executado em:** 2026-11-13, somente GitHub Actions, sem Kaggle.  
**Status:** PASS_PINNED_HASH_COMPARISON; não é prova de equivalência binária, diff semântico, build ou ganho de FPS.

## Proveniência autenticada
- Artefato PRE696 da receita V51: ZIP SHA-256 `d06e06d4dda54d4b50924ec5a404ef396c91cef2166f7b9e055f4b5910154075`, CRC conferido; ID privado Google Drive `1JeOiiM0kei3dyLheQ2q5gNsNito5d4ku`.
- A PRE696 restaurou e verificou PRE99 e os estágios V50/V51, mas expressamente **não comprovou equivalência byte a byte com a libmain.so da APK V51 instalada**.
- Referência do fork: upstream público `victorgbd/NFSMW-Recompiled-Mobile` v0.5.7, originalmente SHA `3ac2fb698576d8889ade19660c38d0fd25f2c5a5`. A MIG-A1 integrou apenas infraestrutura GitHub Actions, sem código do jogo.
- Gate GitHub Actions MIG-A2: https://github.com/Juniklx/NFSMW-Recompiled-Mobile/actions/runs/43361469978 , concluído **success**; relatório original artifact ID `14008522077`, ZIP SHA-256 `d81a79a9a08e78bde8da5c6b8e4dad35f9cac947eb7e87c27c0c8f7bb4a035ff`, CRC aprovado.

## Resultado verificável

| Fonte | V51 bytes | Fork bytes | SHA-256 idêntico? |
|---|---:|---:|---|
| `nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp` | 169876 | 170510 | Não |
| `nativo/sdk/include/rex/ui/vulkan/presenter.h` | 26054 | 26304 | Não |
| `nativo/app/src/nfsmw_ajustes_graficos.cpp` | 25298 | 25298 | **Sim** |
| `nativo/app/src/nfsmw_nativo_sistema.cpp` | 250253 | 250214 | Não |
| `nativo/app/src/nfsmw_nativo_destinos.cpp` | 340248 | 351165 | Não |
| `android/app/src/main/java/io/github/nfsmwrecomp/MotorNativo.java` | 16956 | 17633 | Não |
| `android/app/src/main/java/io/github/nfsmwrecomp/Ajustes.java` | 40220 | 41138 | Não |

**1 idêntico, 6 diferentes, nenhum ausente.** Os SHA-256 completos esperados e encontrados estão no relatório JSON artifact e no manifesto `tools/ci/v51_pre696_pinned_manifest.json`. O job calculou hashes reais no checkout do fork. O workflow não tocou no PRE99 privado nem na APK, em assinatura, saves, recursos gráficos ou no dispositivo.

## Interpretação e próximo gate

Uma diferença de SHA-256 **não comprova ausência de patch**: pode representar mudanças posteriores do upstream, organização, comentários ou funcionalidade nova. A única identidade byte a byte demonstrada no recorte é `nfsmw_ajustes_graficos.cpp`. A comparação histórica PRE696 com um ZIP antigo encontrou cinco idênticos e dois diferentes, mas este ZIP **não era a árvore do fork v0.5.7**; não misturar os baselines.

**MIG-A3 recomendado:** reconstruir a receita V51 autenticada em runner GitHub Actions privado/ephemeral, confrontar os sete arquivos com as fontes públicas v0.5.7 usando diffs de hunks e contexto, sem imprimir trechos privados em logs. Classificar as diferenças como patch local a preservar, mudança upstream a manter ou conflito. Somente então portar patches não derivados de conteúdo do jogo por PRs pequenos. Não alterar ou republicar código gerado de XEX, ISO, `.p12`, credenciais, `.nfsp`, APK privada, saves.

**Política de build:** ainda bloquear uma release: `versionCode=16` e assinatura debug na base v0.5.7 não podem atualizar a V51 (`versionCode=51`, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`). Nenhuma V52, ARM64 completa ou FPS novo validado. Preservar 1920x1080, gráficos, efeitos, física, touch/iPega PG-9076, saves e proteção térmica.
