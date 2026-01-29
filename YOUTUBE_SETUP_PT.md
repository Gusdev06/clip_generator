# Guia de Configuração - Upload para YouTube Shorts

Este guia mostra como configurar a integração com o YouTube para fazer upload automático dos seus clips para o YouTube Shorts.

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Configuração da API do YouTube](#configuração-da-api-do-youtube)
3. [Instalação das Dependências](#instalação-das-dependências)
4. [Autenticação](#autenticação)
5. [Como Usar](#como-usar)
6. [Exemplos](#exemplos)
7. [Solução de Problemas](#solução-de-problemas)

---

## Pré-requisitos

- Python 3.8 ou superior
- Conta do Google/YouTube
- Projeto no Google Cloud Console

---

## Configuração da API do YouTube

### Passo 1: Criar Projeto no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Clique em **"Criar Projeto"** ou selecione um projeto existente
3. Dê um nome ao projeto (ex: "YouTube Shorts Uploader")
4. Clique em **"Criar"**

### Passo 2: Ativar a YouTube Data API v3

1. No menu lateral, vá em **"APIs e Serviços" > "Biblioteca"**
2. Busque por **"YouTube Data API v3"**
3. Clique na API e depois em **"Ativar"**

### Passo 3: Criar Credenciais OAuth 2.0

1. No menu lateral, vá em **"APIs e Serviços" > "Credenciais"**
2. Clique em **"Criar Credenciais" > "ID do cliente OAuth"**
3. Se for a primeira vez:
   - Clique em **"Configurar tela de consentimento"**
   - Escolha **"Externo"** (a menos que tenha Google Workspace)
   - Preencha as informações básicas:
     - Nome do app: "YouTube Shorts Uploader"
     - Email de suporte: seu email
     - Domínios autorizados: pode deixar em branco
   - Clique em **"Salvar e continuar"**
   - Em **"Escopos"**, clique em **"Adicionar ou remover escopos"**
   - Busque e adicione: `https://www.googleapis.com/auth/youtube.upload`
   - Clique em **"Salvar e continuar"**
   - Em **"Usuários de teste"**, adicione seu email do YouTube
   - Clique em **"Salvar e continuar"**

4. Volte para **"Credenciais"** e clique em **"Criar Credenciais" > "ID do cliente OAuth"**
5. Tipo de aplicativo: **"App para computador"**
6. Nome: "YouTube Uploader Desktop"
7. Clique em **"Criar"**

### Passo 4: Baixar Credenciais

1. Após criar, aparecerá uma janela com as credenciais
2. Clique em **"Baixar JSON"**
3. **IMPORTANTE**: Renomeie o arquivo para `client_secrets.json`
4. Mova o arquivo para a pasta raiz do projeto `clips_generator/`

**Estrutura esperada:**
```
clips_generator/
├── client_secrets.json          ← Arquivo de credenciais OAuth2
├── youtube_uploader.py
├── run_upload_shorts.py
└── ...
```

---

## Instalação das Dependências

Se ainda não instalou, execute:

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

As seguintes bibliotecas serão instaladas:
- `google-api-python-client` - Cliente da API do YouTube
- `google-auth-httplib2` - Autenticação HTTP
- `google-auth-oauthlib` - Autenticação OAuth2

---

## Autenticação

### Primeira Autenticação

Na primeira vez que usar o uploader, você precisará fazer login:

```bash
python youtube_uploader.py
```

Isso vai:
1. Abrir automaticamente uma janela do navegador
2. Pedir para fazer login na sua conta do Google/YouTube
3. Mostrar uma tela de consentimento (pode aparecer aviso de "app não verificado")
4. Se aparecer aviso, clique em **"Avançado"** → **"Ir para YouTube Uploader (não seguro)"**
5. Conceder permissão para upload de vídeos
6. Após autorizar, as credenciais serão salvas em `youtube_credentials.pickle`

**Importante:** As credenciais ficam salvas localmente e não precisam ser renovadas toda vez.

### Arquivo de Credenciais

Após autenticação bem-sucedida, será criado:
```
clips_generator/
├── client_secrets.json          ← Credenciais OAuth2 (do Google Cloud)
├── youtube_credentials.pickle   ← Token de acesso (gerado após login)
└── ...
```

**⚠️ SEGURANÇA:**
- **NUNCA** compartilhe `client_secrets.json` ou `youtube_credentials.pickle`
- Adicione ao `.gitignore`:
  ```
  client_secrets.json
  youtube_credentials.pickle
  ```

---

## Como Usar

### 1. Upload de um Único Vídeo

```bash
python run_upload_shorts.py outputs/clips/meu_video.mp4
```

### 2. Upload de Todos os Clips de uma Pasta

```bash
python run_upload_shorts.py --directory outputs/clips
```

### 3. Upload com Título Personalizado

```bash
python run_upload_shorts.py video.mp4 --title "Meu Título Incrível"
```

### 4. Upload como Não Listado

```bash
python run_upload_shorts.py video.mp4 --privacy unlisted
```

### 5. Upload com Tags Personalizadas

```bash
python run_upload_shorts.py video.mp4 --tags "shorts,viral,comédia,brasil"
```

---

## Exemplos

### Exemplo 1: Upload Simples

```bash
# Gerar clips virais
python run_viral.py "https://youtube.com/watch?v=VIDEO_ID" --limit 3

# Fazer upload dos clips gerados
python run_upload_shorts.py --directory outputs/clips
```

### Exemplo 2: Upload com Metadados Automáticos

O sistema detecta automaticamente metadados dos arquivos JSON gerados:

```bash
# Gera clips + titles.json com títulos em português
python run_viral.py "URL_DO_VIDEO" --limit 5

# Upload usa automaticamente os títulos gerados
python run_upload_shorts.py --directory outputs/clips
```

Os títulos serão extraídos de `outputs/clips/titles.json` automaticamente!

### Exemplo 3: Upload Manual com Todos os Parâmetros

```bash
python run_upload_shorts.py meu_video.mp4 \
  --title "🔥 Momento Épico do Podcast!" \
  --description "Confira esse momento incrível! #Shorts" \
  --tags "podcast,viral,shorts,brasil" \
  --privacy public
```

### Exemplo 4: Upload em Lote como Privado (para Revisão)

```bash
# Upload como privado para revisar antes de publicar
python run_upload_shorts.py --directory outputs/clips --privacy private
```

---

## Opções do Script

```
python run_upload_shorts.py [VIDEO] [OPÇÕES]

Argumentos:
  video                  Caminho para o arquivo de vídeo

Opções:
  -d, --directory DIR    Upload de todos os MP4s de um diretório
  -p, --privacy STATUS   Status de privacidade: public, private, unlisted (padrão: public)
  -t, --title TITLE      Título personalizado (sobrescreve metadados)
  --description DESC     Descrição personalizada
  --tags TAGS            Tags separadas por vírgula
  --client-secrets PATH  Caminho para client_secrets.json (padrão: client_secrets.json)
  --credentials PATH     Caminho para arquivo de credenciais (padrão: youtube_credentials.pickle)
```

---

## Metadados Automáticos

O sistema carrega automaticamente metadados dos seguintes arquivos:

### 1. Arquivo JSON Individual (`video.json`)
```json
{
  "title": "Título do Vídeo",
  "tags": ["shorts", "viral"],
  "original_video": "URL do vídeo original"
}
```

### 2. Arquivo de Títulos Gerados (`titles.json`)
```json
{
  "clips": [
    {
      "clip_file": "clip_001.mp4",
      "titles": [
        "🔥 Título Principal",
        "Segunda Opção de Título",
        "Terceira Opção"
      ],
      "viral_clip": {
        "hook_type": "Question Hook",
        "viral_mechanics": ["Emotional Activation", "Humor"],
        "retention_prediction": 85
      }
    }
  ]
}
```

O uploader usa automaticamente:
- **Título**: Primeiro título da lista `titles`
- **Descrição**: Informações sobre o vídeo original, tipo de gancho, mecânicas virais
- **Tags**: Combina tags de metadados + mecânicas virais + tags padrão

---

## Solução de Problemas

### Erro: "client_secrets.json not found"

**Problema:** Arquivo de credenciais OAuth2 não encontrado.

**Solução:**
1. Certifique-se de ter baixado as credenciais do Google Cloud Console
2. Renomeie para `client_secrets.json`
3. Coloque na pasta raiz do projeto

---

### Erro: "Authentication failed"

**Problema:** Falha na autenticação OAuth2.

**Solução:**
1. Delete `youtube_credentials.pickle`
2. Execute novamente: `python youtube_uploader.py`
3. Refaça o processo de login
4. Se aparecer "app não verificado", clique em **Avançado** → **Ir para YouTube Uploader**

---

### Erro: "Quota exceeded"

**Problema:** Você excedeu a cota diária da API do YouTube.

**Detalhes:**
- Cota padrão: **10.000 unidades/dia**
- Upload de vídeo: **~1.600 unidades**
- Máximo: **~6 uploads/dia** (cota gratuita)

**Solução:**
1. Aguarde até o próximo dia (reinicia à meia-noite Pacific Time)
2. Ou solicite aumento de cota no Google Cloud Console (pode demorar dias)

**Dica:** Para testes, use `--privacy private` para não desperdiçar cota com vídeos de teste.

---

### Erro: "API not enabled"

**Problema:** YouTube Data API v3 não está ativada.

**Solução:**
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Vá em **APIs e Serviços > Biblioteca**
3. Busque **"YouTube Data API v3"**
4. Clique em **"Ativar"**

---

### Erro: "Access blocked: YouTube Uploader has not completed Google verification"

**Problema:** Aplicativo não verificado pelo Google.

**Solução (para uso pessoal):**
1. Na tela de consentimento, clique em **"Avançado"**
2. Clique em **"Ir para YouTube Uploader (não seguro)"**
3. Conceda permissão

**Nota:** Isso é normal para apps em desenvolvimento/uso pessoal.

---

### Vídeo não aparece como Short

**Problema:** Vídeo enviado, mas não aparece na seção Shorts.

**Requisitos para Shorts:**
- ✅ Duração: **máximo 60 segundos**
- ✅ Formato: **vertical 9:16** (1080x1920)
- ✅ Hashtag: **#Shorts** na descrição (adicionado automaticamente)

**Nota:** Pode levar algumas horas para o YouTube processar e categorizar como Short.

---

### Upload muito lento

**Problema:** Upload demorando muito tempo.

**Solução:**
- O upload usa chunks de 1MB
- Velocidade depende da sua conexão
- Você verá progresso: `Upload progress: 10%`, `20%`, etc.

---

### Erro: "Invalid video file"

**Problema:** Arquivo de vídeo inválido ou corrompido.

**Solução:**
1. Verifique se o arquivo é um MP4 válido
2. Teste o vídeo localmente antes de enviar
3. Certifique-se de que o processamento foi concluído com sucesso

---

## Limitações e Considerações

### Cotas da API

| Operação | Custo | Limite Diário (gratuito) |
|----------|-------|--------------------------|
| Upload de vídeo | ~1.600 | ~6 uploads/dia |
| Informações do vídeo | 1 | 10.000 consultas |

### Limites de Vídeo

- **Tamanho máximo**: 256 GB ou 12 horas
- **Shorts**: Máximo 60 segundos
- **Título**: Máximo 100 caracteres (Shorts) ou 100 caracteres (vídeos normais)
- **Descrição**: Máximo 5.000 caracteres
- **Tags**: Máximo 500 caracteres total, 15 tags

### Verificação de Conta

Para uploads > 15 minutos, você precisa:
1. Verificar sua conta do YouTube
2. Ir em YouTube Studio → Configurações → Canal → Status e recursos
3. Ativar "Vídeos mais longos"

---

## Próximos Passos

Depois de configurar com sucesso:

1. **Integração Completa**: Modifique `run_viral.py` para fazer upload automático após gerar clips
2. **Agendamento**: Use `cron` (Linux/Mac) ou Task Scheduler (Windows) para uploads automáticos
3. **Análise de Desempenho**: Use `uploader.get_video_info(video_id)` para obter estatísticas

---

## Recursos Adicionais

- [YouTube Data API v3 Documentation](https://developers.google.com/youtube/v3)
- [Google Cloud Console](https://console.cloud.google.com/)
- [YouTube Shorts Guidelines](https://support.google.com/youtube/answer/10059070)

---

## Suporte

Se encontrar problemas:

1. Verifique os logs de erro detalhados
2. Consulte a seção de **Solução de Problemas** acima
3. Revise as configurações no Google Cloud Console
4. Verifique se todas as dependências estão instaladas

---

**Desenvolvido para o projeto Clips Generator**
Última atualização: Janeiro 2025
