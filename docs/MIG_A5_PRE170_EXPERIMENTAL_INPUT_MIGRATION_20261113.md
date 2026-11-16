# MIG-A5 — migração experimental PRE170 (fila SDL no Android)

**13/11/2026.** Este documento acompanha **um PR em rascunho**, não uma release de Android.

## Evidência da fonte V51

- GitHub Actions-only: [reconstrução privada MIG-A5 #43451194001](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43451194001), completed/success. Restaurou PRE99 autenticada, reproduziu receita V51 e verificou os três patches de SDK/entrada (2/2/2 hunks V51; 0/0/7 hunks fork). Nenhum conflito textual nesses três arquivos.
- Pacote com código de SDK apenas no **Drive privado**: https://drive.google.com/file/d/1G-8AJwIyDvwZbOIGZcT83FE9juA5M0VO/view ; 18.451 bytes, SHA-256 `b209b369cbbcb92620457fe9e155f50dda8fac77ece4be5f5e7b76edf6558159`, CRC íntegro e readback autenticado. **Não espelhar este ZIP como artefato público do Actions**.
- No fork, `sdl_input_driver.h` ainda era idêntico ao PRE99; sua versão alterada possui o mesmo SHA-256 **6b532f228805dbd57aaaa3d4e19d6febf784506ebacd6b80216af254cae2f5ca** do SDK reconstruído V51.
- O bloco PRE170 de `SDLInputDriver::QueueControllerUpdate` tem SHA-256 **0831a7b2e99a702b3dc2d0a7b6f8f961059ca2b261ab0999ad1e4a92322d07d4** idêntico ao obtido da receita autenticada. As outras mudanças upstream do arquivo `.cpp` foram mantidas, não substituídas pela versão antiga.
- [Teste do fork #43452479081](https://github.com/Juniklx/NFSMW-Recompiled-Mobile/actions/runs/43452479081): `completed/success`. Confere hash do header, hash do bloco de função PRE170, persistência das chamadas `SDL_PumpEvents()` e `rex_sdl_set_touch_gamepad_state`, ausência da instrumentação PRE364 e compila/executa um **exemplo sintético C++20** do algoritmo atômico de 8 ms, incluindo chamadas concorrentes. Não compila o motor SDL/Android.

## O que foi alterado

1. `nativo/sdk/include/rex/input/sdl/sdl_input_driver.h`: importa `<cstdint>` e acrescenta `sdl_next_pump_ns_` atômico de 64 bits.
2. `nativo/sdk/src/input/sdl/sdl_input_driver.cpp`: importa `<chrono>`; no Android apenas, limita agendamentos de `SDL_PumpEvents()` a um por pelo menos **8 ms**, com `compare_exchange_weak` e relógio monotônico. O mecanismo original de fila SDL é preservado.
3. `tools/ci/mig_a5_pre170_source_guard.py` e workflow de CI: verificações estáticas/hash e algoritmo sintético; não baixam jogo nem assinam.
4. **Não foi portada PRE364** de `nativo/sdk/src/input/input_system.cpp`: era exclusivamente logging de transições digitais do XInput em até 256 eventos, um diagnóstico histórico que não deve ser promovido automaticamente a produção.

## Riscos e gates pendentes

- O limitador PRE170 pode **mudar latência de conexão, hotplug e tempo de atualização SDL**, mesmo sem mexer diretamente no estado touch/iPega. `SDL_PumpEvents()` permanece, mas isso não prova compatibilidade dinâmica.
- Teste C++ sintético **não** é compilação do SDK real/NDK ARM64, nem validação no Galaxy S24 FE.
- O projeto público no `main` ainda tem `versionCode=16` e assinatura debug para release em upstream; não usá-lo para atualizar a **V51 instalada**. Release futura exige certificado permanente já existente, mesmo package ID e `versionCode>51`, sem recriar ou expor credenciais.
- **Não mesclar este PR automaticamente** até validar build ARM64 real do código modificado, comportamento da ponte V3 iPega PG-9076/touch, latência/hotplug e regressão de fluidez. Os testes atuais não confirmam redução de wakeups ou aumento de FPS.
- Preservar resolução interna **1920×1080**, objetivo máximo 120 FPS, shaders/efeitos/texturas/sombras/física/saves e proteção térmica.

**Estado:** `MIG_A5_PRE170_SOURCE_PORTED_TO_DRAFT_BRANCH`; `HOST_SYNTHETIC_TEST_PASS`; `ARM64_BUILD_PENDING`; `PHONE_TEST_PENDING`; `NO_V52`; `NO_FPS_GAIN`.

Próximo passo: **MIG-A6** — auditar/validar integração completa do código de entrada com a ponte Java/iPega do fork e preparar compilação ARM64 sem APK/assinatura, antes de propor mesclagem.
