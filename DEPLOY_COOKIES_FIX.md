# 🔧 Fix de Cookies em Produção

## 📋 Problema Identificado

O arquivo `cookies.txt` não estava sendo mapeado no Docker container, mesmo estando presente no host.

## ✅ Solução Aplicada

Atualizado `docker-compose.yml` para incluir:
- Mapeamento do volume `cookies.txt`
- Variável de ambiente `YT_COOKIES_FILE`

---

## 🚀 Deploy da Correção

### **1. Enviar arquivos atualizados para produção**

```bash
# No seu Mac, dentro da pasta do projeto
scp docker-compose.yml root@seu-servidor:/caminho/do/projeto/
scp cookies.txt root@seu-servidor:/caminho/do/projeto/
```

> **Substitua:**
> - `root@seu-servidor` pelo seu usuário e IP
> - `/caminho/do/projeto/` pelo caminho real (ex: `/root/clips_generator/`)

### **2. Conectar no servidor**

```bash
ssh root@seu-servidor
cd /caminho/do/projeto
```

### **3. Parar e remover containers antigos**

```bash
docker-compose down
```

### **4. Verificar arquivos**

```bash
# Confirmar que os arquivos estão corretos
ls -la cookies.txt docker-compose.yml

# Verificar se o cookies.txt tem conteúdo
wc -l cookies.txt  # Deve ter várias linhas
```

### **5. Subir novamente com as novas configurações**

```bash
docker-compose up -d --build
```

### **6. Verificar os logs**

```bash
docker-compose logs -f api
```

**Procure por esta linha nos logs quando fizer um download:**
```
✅ Using cookies from file: /app/cookies.txt
```

### **7. Testar**

Faça uma requisição de teste para ver se funciona:

```bash
curl -X POST http://localhost:8000/viral \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=SEU_VIDEO_ID"}'
```

---

## 🔍 Verificação Rápida

Se ainda der erro, verifique:

```bash
# 1. Container está rodando?
docker ps

# 2. Arquivo existe dentro do container?
docker exec clips_generator_api ls -la /app/cookies.txt

# 3. Conteúdo do arquivo dentro do container
docker exec clips_generator_api head -5 /app/cookies.txt

# 4. Variável de ambiente está configurada?
docker exec clips_generator_api env | grep YT_COOKIES
```

---

## 📝 Resultado Esperado

Antes (ERRO):
```
ERROR: [youtube] lXP_JM6dBuk: Sign in to confirm you're not a bot
```

Depois (SUCESSO):
```
  Using cookies from file: /app/cookies.txt
Download successful: /app/downloads/video.mp4
```

---

## 🆘 Troubleshooting

### **Se ainda der erro:**

1. **Cookies expiraram durante o upload**
   - Exporte novamente e repita o processo

2. **Arquivo não encontrado no container**
   ```bash
   # Verifique o mapeamento
   docker inspect clips_generator_api | grep cookies
   ```

3. **Permissões incorretas**
   ```bash
   # No host
   chmod 644 cookies.txt
   ```

4. **Container cacheado**
   ```bash
   # Force rebuild completo
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```
