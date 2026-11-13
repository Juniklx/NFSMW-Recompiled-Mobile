# MIG-A4 — inventário autenticado de alterações V51 no escopo público do fork

**Data:** 2026-11-13.  
**Resultado final:** `PASS_AUTHENTICATED_SCOPED_INVENTORY`.  
**Execução aprovada:** https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43394929759 (job `131783448735`, completed/success).  
**Primeira tentativa:** https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43394591362 — falhou ao criar diretório temporário do comparador; corrigido e reexecutado. **Não é resultado aprovado.**

**Relatório sanitizado:** https://drive.google.com/file/d/1nVo6a_EBssQj4NOnbTny4q8HeuTsARQD/view ; artifact GitHub `14021674993`, ZIP **3.684 bytes**, SHA-256 `561d7e6fa633d7e4b08afda113091dafedfd65f7f9f5dd09022e2d7d744885a9`, CRC e readback Drive conferidos.

## Método e limitações

Fluxo exclusivo **GitHub Actions**, sem Kaggle. Restauração da PRE99 autenticada por SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`; replay das etapas PRE431/PRE638, auditoria PRE648/PRE652 e aplicação **somente em memória** do patch PRE648 no renderizador, cuja fonte reconstruída possui SHA-256 `9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2`. Comparação com **fork imutável** no commit `6cc6d679b9b844a2a798981f4f47095df381be17`.

A auditoria cobre apenas **795 arquivos de fonte rastreados publicamente** pelo fork sob os prefixos selecionados do Android Java, `nativo/app/src/nfsmw_*`, `nativo/app/include/nfsmw_*`, `nativo/sdk/src` e `nativo/sdk/include/rex`. Não cobre toda a árvore, arquivos do jogo recompilado, `app_usa`, arquivos não rastreados, assets, shaders compilados, ISO/XEX, saves, chaves e credenciais. **Nenhum código-fonte, diff textual, binário ou material secreto foi publicado no relatório**; só caminhos públicos, hashes, tamanhos, hunks e classificação.

A receita de código reconstruída é uma referência autenticada para a inspeção, **não prova de equivalência binária** com a `libmain.so` da APK V51 assinada.

## Resultado

- **795** caminhos-fonte públicos elegíveis.
- **10** desses arquivos alterados da PRE99 para a receita V51.
- **5** alterados na V51, enquanto o fork mantém exatamente a versão PRE99.
- **5** alterados tanto na V51 quanto no fork; requerem revisão semântica.
- **0** alterações integralmente idênticas à V51 no fork, entre esses dez arquivos.
- **2** arquivos com conflitos de mesclagem textual (`settings_overlay.cpp`: 5; `windowed_app_context_sdl.cpp`: 1). Total: **6 conflitos textuais**. Um merge limpo não comprova correção funcional.

| Caminho-fonte | Hunks PRE99→V51 | Hunks PRE99→fork | Estado |
|---|---:|---:|---|
| `nativo/app/src/nfsmw_nativo_dibujos.cpp` | 9 | 5 | Ambos modificados; sem conflito textual |
| `nativo/sdk/include/rex/input/sdl/sdl_input_driver.h` | 2 | 0 | Patch V51 exclusivo |
| `nativo/sdk/include/rex/ui/imgui_drawer.h` | 1 | 0 | Patch V51 exclusivo |
| `nativo/sdk/include/rex/ui/overlay/settings_overlay.h` | 1 | 0 | Patch V51 exclusivo |
| `nativo/sdk/src/input/input_system.cpp` | 2 | 0 | Patch V51 exclusivo |
| `nativo/sdk/src/input/sdl/sdl_input_driver.cpp` | 2 | 7 | Ambos modificados; sem conflito textual |
| `nativo/sdk/src/ui/imgui_drawer.cpp` | 2 | 0 | Patch V51 exclusivo |
| `nativo/sdk/src/ui/overlay/settings_overlay.cpp` | 20 | 12 | Ambos modificados; **5 conflitos** |
| `nativo/sdk/src/ui/presenter.cpp` | 2 | 7 | Ambos modificados; sem conflito textual |
| `nativo/sdk/src/ui/windowed_app_context_sdl.cpp` | 1 | 10 | Ambos modificados; **1 conflito** |

### Prioridades da MIG-A5

1. **Entrada iPega PG-9076 e touch:** inspecionar semanticamente `sdl_input_driver.h`, `input_system.cpp` e `sdl_input_driver.cpp`, mantendo a ponte V3 validada e o comportamento upstream mais recente. Não copiar arquivos inteiros sem analisar a compatibilidade da API e os testes.
2. **Renderização 1080p / shaders / física:** avaliar os 9 hunks V51 do `nfsmw_nativo_dibujos.cpp` contra os cinco do fork, incluindo patch PRE648 em memória. Não diminuir carga gráfica, qualidade, efeitos nem supor ganho FPS.
3. **Overlay/UI e SDL:** revisar juntos `imgui_drawer.{h,cpp}`, `settings_overlay.{h,cpp}`, `presenter.cpp`, `windowed_app_context_sdl.cpp`; resolver seis conflitos textuais com entendimento de chamadas e estruturas, não um `git merge` automático.

Próximo gate deve medir e comparar **funções e invariantes de comportamento**, com relatórios sanitizados e testes unitários/sintéticos para patches compatíveis; só depois propor alterações de código em PRs pequenos e revisáveis.

**Invariantes:** V51 instalada intocada, package `io.github.nfsmwrecomp`, `versionCode=51`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Não há APK V52, build ARM64 completa ou melhora de FPS comprovada. O fork base segue sem release assinável seguro para atualizar a V51; proibir assinatura debug e chaves novas.
