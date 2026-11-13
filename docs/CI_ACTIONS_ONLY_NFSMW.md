# NFSMW Android — fluxo GitHub Actions sem Kaggle

**Status (13/11/2026):** migração inicial de infraestrutura no fork. Esta etapa não migra o código da V51 e não constrói APK.

## Origem e baseline

O branch principal de Juniklx/NFSMW-Recompiled-Mobile ainda era idêntico ao upstream victorgbd/NFSMW-Recompiled-Mobile, commit 3ac2fb698576d8889ade19660c38d0fd25f2c5a5 (v0.5.7), no início desta migração. O fork **não** inclui automaticamente nossos patches da APK V51.

A referência instalada é io.github.nfsmwrecomp, versionCode 51, certificado SHA-256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. A receita de código V51 ainda não foi demonstrada byte a byte equivalente à libmain.so assinada. Nunca copiar patches sem identificar e autenticar a árvore de origem.

No upstream, android/app/build.gradle.kts atualmente informa versionCode 16 e usa assinatura debug no build type release. Portanto, uma APK produzida diretamente desse fork **não atualizaria com segurança a V51**. Este gate não modifica esses campos, não cria chaves e não tenta assinar.

## Etapas do novo fluxo

1. **Código:** manter fork como fonte principal para novas alterações, em branches e pull requests revisáveis; comparar upstream, a receita da V51 e backups por hash antes de transportar correções. Não disparar mais tarefas Kaggle.
2. **CI somente fonte:** .github/workflows/nfsmw-actions-only-preflight.yml verifica sintaxe Python, sintaxe shell, configuração Android ARM64, identificação do pacote e ausência de material do jogo ou chaves privadas rastreadas no Git. O script tools/ci/actions_only_preflight.py produz relatório JSON SOURCE_ONLY. Esse CI não gera APK nem demonstra FPS.
3. **Compilação ARM64 futura:** somente após fonte/base V51 autenticadas, adicionar workflow manual separado com SDK/NDK/CMake, preparação de fontes e shaders, verificações SHA256, limites de tempo/disco e política explícita de destino de artefatos. Nenhum executável derivado de conteúdo do jogo deve ser publicado no GitHub público.
4. **Assinatura de release futura:** exigir pacote io.github.nfsmwrecomp, versionCode maior que 51 e certificado idêntico à V51, com validação apksigner. Não commitar chave .p12, senha, arquivos de credenciais, ISO, XEX, bibliotecas privadas ou logs confidenciais. Nunca recriar chave e nunca assinar release com chave debug.
5. **Validação física:** depois de um APK novo ser gerado e instalado, verificar 1920×1080 internos, limite até 120 FPS, todos os gráficos/shaders/efeitos/física, controle touch + iPega PG-9076, saves e proteções térmicas. O runner GitHub não testa desempenho real do Galaxy S24 FE.

## Limites reais de GitHub Actions

Em repositórios públicos, runner Ubuntu padrão possui 4 CPUs, 16 GB RAM e 14 GB de SSD (GitHub Docs consultados em 13/11/2026), com seis horas de execução por job. A ISO USA (~7,8 GB) e o ZIP PAL (~5,6 GB) somados ao NDK, CMake e aos objetos compilados podem ultrapassar o disco disponível. Antes de configurar uma build completa é preciso medir espaço, dimensionar artefatos intermediários e optar por entrada privada menor ou runner com mais armazenamento. GitHub Actions é suficiente para automação de código e CI, mas a compilação integral precisa ser comprovada, não presumida.

## Ativar o workflow no fork

No repositório Juniklx/NFSMW-Recompiled-Mobile, entrar na aba **Actions** e habilitar os workflows se aparecer o aviso de fork desativado. O primeiro workflow NÃO precisa de secrets. Não disponibilizar secrets para PRs externos.

O histórico de Juniklx/nfsmw-actions-teste e os arquivos do Google Drive permanecem preservados; esta mudança **não apaga notebooks ou commits antigos**, apenas introduz um fluxo novo sem Kaggle. A política operacional deixa de usar Kaggle para tarefas futuras após validar o novo runner.

**Status:** ACTIONS_ONLY_PREFLIGHT_STAGED; FULL_ARM64_BUILD_NOT_VERIFIED; V51_SOURCE_NOT_MERGED; NO_APK; NO_FPS_GAIN. O próximo gate é comparar a receita V51 com a fonte v0.5.7 e provar um run do novo workflow.