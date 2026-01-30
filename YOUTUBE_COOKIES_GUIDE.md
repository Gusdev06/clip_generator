# 🍪 Guia: Como Resolver "Sign in to confirm you're not a bot"

Este erro acontece quando o YouTube bloqueia requisições do yt-dlp em servidores. A solução é fornecer cookies de autenticação.

---

## 🚀 Solução Rápida (Recomendado)

### **Opção 1: Usar Cookies do Browser (Chrome)**

Melhor para ambientes Docker com acesso ao Chrome.

1. **Certifique-se que o Chrome está instalado no servidor**

2. **Adicione no `.env`:**
```env
YT_COOKIES_FROM_BROWSER=chrome
```

3. **Reinicie o container:**
```bash
docker-compose restart
```

**Nota:** Funciona também com `firefox`, `edge`, `safari`, etc.

---

### **Opção 2: Arquivo cookies.txt (Melhor para Produção)**

Use quando não há browser instalado no servidor.

#### **Passo 1: Instalar extensão no seu navegador local**

**Chrome/Edge:**
- Extensão: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)

**Firefox:**
- Extensão: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

#### **Passo 2: Exportar cookies do YouTube**

1. Abra o YouTube no navegador: https://www.youtube.com
2. **Faça login** na sua conta Google
3. Navegue para qualquer vídeo do YouTube
4. Clique no ícone da extensão
5. Clique em **"Export"** ou **"Download"**
6. Salve o arquivo como `youtube_cookies.txt`

#### **Passo 3: Fazer upload para o servidor**

**Opção A: Via SCP (do seu computador):**
```bash
scp youtube_cookies.txt root@seu-servidor:/root/clips_generator/youtube_cookies.txt
```

**Opção B: Criar manualmente no servidor:**
```bash
nano /root/clips_generator/youtube_cookies.txt
# Cole o conteúdo do arquivo
# Ctrl+O, Enter, Ctrl+X
```

#### **Passo 4: Configurar no `.env`**

```bash
nano .env
```

Adicione:
```env
YT_COOKIES_FILE=/app/youtube_cookies.txt
```

#### **Passo 5: Atualizar docker-compose.yml**

Adicione o arquivo de cookies como volume:

```yaml
services:
  api:
    # ... outras configurações
    volumes:
      - ./fonts:/app/fonts:ro
      - ./models:/app/models
      - ./youtube_cookies.txt:/app/youtube_cookies.txt:ro  # ← Adicione esta linha
      - clips_downloads:/app/downloads
      - clips_outputs:/app/outputs
```

#### **Passo 6: Reiniciar o serviço**

```bash
docker-compose down
docker-compose up -d
```

---

## 🔧 Verificar se Funcionou

Teste o download:

```bash
# Ver logs
docker-compose logs -f api

# Tentar fazer uma requisição
curl -X POST http://localhost:8000/viral \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "limit": 1}'
```

Você deve ver nos logs:
```
✅ Using cookies from file: /app/youtube_cookies.txt
```
ou
```
✅ Using cookies from browser: chrome
```

---

## ⚠️ Problemas Comuns

### **1. Cookies expiraram**

**Sintoma:** Mesmo com cookies, ainda dá erro de autenticação.

**Solução:** Cookies do YouTube expiram. Exporte novamente seguindo o Passo 2.

### **2. Arquivo de cookies não encontrado**

**Sintoma:** `FileNotFoundError: youtube_cookies.txt`

**Solução:**
- Verifique o caminho no `.env`
- Certifique-se que o volume está mapeado no `docker-compose.yml`

### **3. Formato de cookies inválido**

**Sintoma:** `ERROR: unable to open cookie file`

**Solução:** O arquivo deve estar no formato **Netscape**. Use as extensões recomendadas acima.

---

## 🔐 Segurança

⚠️ **IMPORTANTE:**
- **NÃO** commite o arquivo `youtube_cookies.txt` no Git
- Adicione ao `.gitignore`:
  ```
  youtube_cookies.txt
  ```
- Cookies contêm informações de autenticação da sua conta Google
- Renove os cookies periodicamente (a cada 1-2 meses)

---

## 📖 Referências

- [yt-dlp Cookie Guide](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)
- [YouTube Cookie Export Guide](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)

---

## 🆘 Ainda com Problemas?

Se ainda estiver com erros:

1. **Verifique os logs:**
   ```bash
   docker-compose logs -f api
   ```

2. **Teste yt-dlp manualmente no container:**
   ```bash
   docker-compose exec api bash
   yt-dlp --cookies /app/youtube_cookies.txt "https://www.youtube.com/watch?v=VIDEO_ID"
   ```

3. **Use a opção `--verbose` para debug:**
   Edite o `downloader.py` e mude:
   ```python
   'quiet': False,  # já está assim
   'verbose': True,  # adicione esta linha
   ```

Boa sorte! 🚀
