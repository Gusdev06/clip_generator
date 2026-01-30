# 🍪 Guia de Cookies do YouTube para Hostinger/Docker

Este guia explica como configurar os cookies do YouTube para evitar detecção de bot ao baixar vídeos.

## ⚠️ Por que preciso de cookies?

Quando o servidor baixa vídeos do YouTube usando yt-dlp, o YouTube detecta como bot e bloqueia o download. Os cookies do navegador autenticam a requisição como se fosse um usuário real.

## 📋 Como configurar (primeira vez)

### 1. Exportar cookies do navegador

#### Opção A: Chrome/Edge (Recomendado)
1. Instale a extensão: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Faça login no YouTube (youtube.com)
3. Clique no ícone da extensão
4. Clique em "Export" → escolha "Netscape format"
5. Salve como `cookies.txt`

#### Opção B: Firefox
1. Instale a extensão: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. Faça login no YouTube (youtube.com)
3. Clique no ícone da extensão
4. Escolha "youtube.com" e clique em "Export"
5. Salve como `cookies.txt`

### 2. Colocar o arquivo no projeto

```bash
# Copie o cookies.txt para a raiz do projeto
cp ~/Downloads/cookies.txt /caminho/do/projeto/clips_generator/
```

### 3. Configurar variável de ambiente

No arquivo `.env`:
```bash
YT_COOKIES_FILE=/app/cookies.txt
```

✅ **IMPORTANTE**: Use `/app/cookies.txt` (caminho dentro do container), NÃO o caminho local!

### 4. Rebuild e restart do Docker

```bash
# Pare o container
docker-compose down

# Rebuild incluindo o novo cookies.txt
docker-compose build --no-cache

# Inicie novamente
docker-compose up -d
```

## 🔄 Atualizando cookies (quando expirarem)

Os cookies do YouTube expiram periodicamente. Quando começar a dar erro de bot novamente:

1. **Exporte novos cookies** (repita passo 1 acima)
2. **Substitua** o arquivo `cookies.txt` no projeto
3. **Rebuild** o container Docker:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## 🐛 Debug e Troubleshooting

### Verificar se os cookies estão funcionando

```bash
# Executar script de debug dentro do container
docker exec -it <container_name> python debug_cookies.py
```

O script irá mostrar:
- ✅ Se o arquivo cookies.txt existe
- ✅ Quantos cookies foram carregados
- ✅ Se o formato está correto (Netscape)
- ✅ Se o Deno (JavaScript runtime) está instalado
- ✅ Se consegue acessar o YouTube

### Problemas comuns

#### ❌ Erro: "Sign in to confirm you're not a bot"
**Causa**: Cookies expirados ou inválidos
**Solução**: Exporte novos cookies do navegador e faça rebuild

#### ❌ Erro: "No supported JavaScript runtime could be found"
**Causa**: Deno não instalado no container
**Solução**: Faça rebuild do container (o Dockerfile já instala o Deno)

#### ❌ Erro: "Using cookies from file: /app/cookies.txt" mas ainda dá erro
**Causa**: Arquivo cookies.txt não foi copiado para o container
**Solução**:
1. Verifique se o arquivo está na raiz do projeto
2. Faça rebuild com `--no-cache`
3. Verifique logs do build: `docker-compose build --no-cache 2>&1 | grep cookies`

#### ❌ Container buildo mas cookies.txt não aparece
**Causa**: Arquivo pode estar no .dockerignore
**Solução**: Verifique se `cookies.txt` NÃO está listado em `.dockerignore`

## 📝 Formato correto dos cookies

O arquivo `cookies.txt` deve começar assim:

```
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1801112322	__Secure-YENID	...
.youtube.com	TRUE	/	FALSE	1776978380	_gcl_au	...
```

**Características**:
- Primeira linha: `# Netscape HTTP Cookie File`
- Domínio: `.youtube.com`
- Formato: separado por TABs (não espaços)
- Timestamp de expiração (Unix timestamp)

## 🔒 Segurança

⚠️ **NUNCA compartilhe seu arquivo cookies.txt!**
Ele contém suas credenciais de autenticação do YouTube.

✅ O arquivo `.gitignore` já ignora o arquivo `.env` (que contém o caminho)
✅ **Mas não ignore o `cookies.txt`** - ele precisa ser copiado para o container

## 📦 Deploy na Hostinger

### Via Git (Recomendado)
```bash
# Adicione cookies.txt ao repositório (use repositório PRIVADO!)
git add cookies.txt
git commit -m "Add YouTube cookies"
git push

# No servidor Hostinger
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Via SCP/FTP
```bash
# Copie o cookies.txt via SCP
scp cookies.txt user@hostinger:/path/to/project/

# SSH no servidor e rebuild
ssh user@hostinger
cd /path/to/project
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## ✅ Checklist de verificação

Antes de fazer deploy, confirme:

- [ ] Arquivo `cookies.txt` está na raiz do projeto
- [ ] Arquivo tem formato Netscape (primeira linha começa com `# Netscape`)
- [ ] Variável `YT_COOKIES_FILE=/app/cookies.txt` está no `.env`
- [ ] Fez rebuild do container (`docker-compose build --no-cache`)
- [ ] Rodou o script de debug: `docker exec -it <container> python debug_cookies.py`

## 📞 Suporte

Se continuar com problemas:
1. Execute `docker logs <container_name>` e procure por linhas com "cookies"
2. Execute o script de debug: `python debug_cookies.py`
3. Verifique se os cookies foram exportados recentemente (menos de 30 dias)
