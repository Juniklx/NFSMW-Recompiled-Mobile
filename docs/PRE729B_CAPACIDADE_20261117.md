# PRE729B — correção da coleta de capacidade — 17/11/2026

## Evidência recebida e limites
- TXT: NFSMW_PRE729_CAPACIDADE_20261117_145322_27947.txt, 5571 bytes, SHA256 7a8fae9a1475b198f57b69fe6ca95fecbb87633a5c46f4e01821a428e240aa73.
- Cópia preservada: https://drive.google.com/file/d/1tdWViHU4XBOCaAZZU4wZtCuBic9rCmIS/view
- Confirmados UID 2000, pacote io.github.nfsmwrecomp e versionCode 51.
- SurfaceFlinger retornou três entradas da mesma SurfaceView: Background, contêiner e BLAST. A PRE729 exigia exatamente uma entrada bruta, registrou LATENCY_SKIPPED=NO_UNIQUE_GAME_SURFACE e não coletou tempos de quadros.
- Isso demonstra uma limitação da sonda; não demonstra falha do jogo, FPS, gargalo ou ganho.
- Perfetto --version e --query: saída vazia com retorno 0. Capacidade de captura permanece inconclusiva; não declarar disponível ou indisponível.
- atrace listou categorias, incluindo gfx, sched, freq e thermal. A listagem não comprova gravação funcional.
- Thermal Status 0 e IsStatusOverride false nas duas consultas. HAL corrente: AP 46,8 °C, BAT 33,3 °C e SKIN 34,7 °C. Valores em cache são diferentes e não devem ser confundidos. Estes instantâneos não provam ausência de limitação térmica durante toda a sessão.
- DEVICE_CAPTURE_VALIDATED=FALSE e demais flags do cabeçalho original são marcadores fixos de prudência, não resultados de testes executados.

## Correção e validação
PRE729B mantém o script anterior e adiciona:
- Normalização de RequestedLayerState{nome atributos} para o nome exato; preserva espaços e #id; exclui Background e !handle; deduplica nomes.
- Seleção da única camada BLAST do pacote exato. Sem BLAST, aceita somente uma SurfaceView. Ambiguidade ou falha de listagem impede a coleta.
- Três consultas --latency, sem limpar contadores; triplas numéricas são apenas candidatas, ainda não validadas quanto a identidade, relógio, atualização e sobreposição.
- Saída vazia é explicitamente inconclusiva. Registra caminho de Perfetto, estados traced/traced_probes e ajuda diagnóstica quando a consulta vem vazia.
- Nenhuma mudança de configurações, jogo, APK, limites, proteções térmicas ou credenciais.

Código: tools/diagnostics/nfsmw_pre729b_probe_capture.sh
5833 bytes; SHA256 95fd922e0e053866e8f88eb37cbeebbbe2b452ff4169d5b4bfd3e27a7cc2b9cb.
Entrega verificada por leitura de retorno idêntica:
https://drive.google.com/file/d/1QceNy9Zuu5zHgwIsqlxHMGLzx4O4Rt1D/view

Commit testado: 47734649b7a422241a87644a56cc566f4cb12294.
PR6: https://github.com/Juniklx/NFSMW-Recompiled-Mobile/pull/6 (rascunho, sem merge).
Actions: https://github.com/Juniklx/NFSMW-Recompiled-Mobile/actions/runs/44143544452
Job 134252433648 concluído com sucesso; logs confirmam PRE729_SHELL_MOCK_CASES=6_PASS e PRE729B_SHELL_MOCK_CASES=14_PASS, ambos DEVICE_TESTED=FALSE.
Localmente os mesmos testes passaram e um teste extra com as três linhas exatas do TXT selecionou d2f67fa SurfaceView[io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity]@0(BLAST)#11466. Resposta --latency simulada nesse teste; não é captura do aparelho.

Fundamento consultado: AOSP Android16 SurfaceFlinger.cpp, listLayers usa getDebugString e dumpStats compara getName:
https://android.googlesource.com/platform/frameworks/native/+/refs/heads/android16-release/services/surfaceflinger/SurfaceFlinger.cpp
Formato RequestedLayerState:
https://android.googlesource.com/platform/frameworks/native/+/a34de5209546e74a5ad6e4c348016d70271a6492/services/surfaceflinger/FrontEnd/RequestedLayerState.cpp
Perfetto CLI:
https://perfetto.dev/docs/reference/perfetto-cli
A implementação Samsung ainda requer teste real; AOSP não garante comportamento idêntico do fornecedor.

## Próximo passo dependente do aparelho
Baixar nfsmw_pre729b_probe_capture.sh em Download, executar no Shevery:
sh /sdcard/Download/nfsmw_pre729b_probe_capture.sh
Voltar ao jogo durante os 20 segundos e deixar o carro parado, com o jogo visível por mais 30 segundos. Enviar o TXT NFSMW_PRE729B_CAPACIDADE_*.txt gerado em Download. Se houver erro ou expiração de comando, preservar a saída.
Analisar o TXT antes de iniciar captura sincronizada, comparar desempenho ou alterar o runtime.

STATUS: PRE729_DEVICE_LOG_ANALYZED; PRE729B_14_MOCK_TESTS_PASS_LOCAL_AND_CI; PRE729B_DEVICE_TEST_PENDING; NO_FRAME_TIMINGS_FROM_PRE729; NO_FPS_GAIN.
Preservados V51, pacote io.github.nfsmwrecomp, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b, 1920x1080, meta120 FPS (cap efetivo anterior60/display120), gráficos/shaders/efeitos/física, controles, saves e proteções térmicas. Nenhum novo APK gerado nesta etapa.
