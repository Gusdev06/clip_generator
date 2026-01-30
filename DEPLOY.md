# 🚀 Deploy do Clips Generator na Hostinger

Este guia mostra como fazer deploy da API de geração de clips virais na Hostinger usando Docker.

## 📋 Pré-requisitos

1. **Conta na Hostinger** com VPS ou Cloud Hosting que suporte Docker
2. **Chaves de API:**
   - OpenAI API Key (para Whisper + GPT-4)
   - Supabase URL e Key
3. **Docker e Docker Compose** instalados no servidor

---

## 🔧 Configuração Inicial

### 1. Conectar ao servidor via SSH

```bash
ssh root@seu-servidor-hostinger.com
```

### 2. Instalar Docker (se não estiver instalado)

```bash
# Atualizar pacotes
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
apt install docker-compose -y

# Verificar instalação
docker --version
docker-compose --version
```

---

## 📦 Deploy da Aplicação

### 1. Clonar o repositório ou fazer upload dos arquivos

```bash
# Opção A: Clonar do Git
git clone https://github.com/seu-usuario/clips_generator.git
cd clips_generator

# Opção B: Upload via SCP (do seu computador local)
# scp -r . root@seu-servidor:/root/clips_generator
```

### 2. Criar arquivo de variáveis de ambiente

```bash
# Criar .env no servidor
nano .env
```

Adicione as seguintes variáveis:

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-seu-token-aqui

# Supabase Configuration
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon-aqui
```

Salve com `Ctrl+O`, Enter, `Ctrl+X`

### 3. Construir e iniciar os containers

```bash
# Build da imagem
docker-compose build

# Iniciar a aplicação
docker-compose up -d

# Verificar logs
docker-compose logs -f api
```

---

## 🌐 Configurar Domínio e HTTPS (Opcional)

### Usando Nginx como Reverse Proxy

1. **Instalar Nginx**

```bash
apt install nginx -y
```

2. **Criar configuração do site**

```bash
nano /etc/nginx/sites-available/clips-api
```

Adicione:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeout para processamento de vídeos longos
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

3. **Ativar site e instalar SSL**

```bash
# Ativar configuração
ln -s /etc/nginx/sites-available/clips-api /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# Instalar Certbot para SSL
apt install certbot python3-certbot-nginx -y
certbot --nginx -d seu-dominio.com
```

---

## 🔄 Comandos Úteis

### Gerenciar a aplicação

```bash
# Ver logs em tempo real
docker-compose logs -f api

# Reiniciar a aplicação
docker-compose restart api

# Parar a aplicação
docker-compose down

# Atualizar após mudanças no código
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Ver status dos containers
docker-compose ps

# Entrar no container (debug)
docker-compose exec api bash
```

### Limpeza de disco

```bash
# Remover imagens antigas do Docker
docker system prune -a

# Limpar volumes não usados
docker volume prune

# Ver uso de disco
df -h
du -sh /var/lib/docker
```

---

## 📊 Monitoramento

### Health Check

```bash
curl http://localhost:8000/health
# Resposta esperada: {"status":"ok"}
```

### Verificar uso de recursos

```bash
# CPU e memória dos containers
docker stats

# Uso de disco
df -h

# Processos
htop
```

---

## 🛡️ Segurança

### 1. Configurar Firewall

```bash
# Instalar UFW
apt install ufw -y

# Permitir SSH, HTTP e HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# Ativar firewall
ufw enable

# Ver status
ufw status
```

### 2. Limitar taxa de requisições (Nginx)

Adicione no bloco `http` do `/etc/nginx/nginx.conf`:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    # ... sua configuração

    location / {
        limit_req zone=api_limit burst=20 nodelay;
        # ... resto da config
    }
}
```

---

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs de erro
docker-compose logs api

# Verificar se a porta 8000 está em uso
netstat -tulpn | grep 8000

# Reconstruir imagem do zero
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Falta de espaço em disco

```bash
# Limpar arquivos gerados (a API já faz isso automaticamente)
docker-compose exec api rm -rf /app/downloads/* /app/outputs/*

# Limpar Docker
docker system prune -a --volumes
```

### Erros de permissão

```bash
# Ajustar permissões das pastas
chown -R 1000:1000 fonts/ models/
chmod -R 755 fonts/ models/
```

---

## 📈 Escalabilidade

### Aumentar recursos do container

Edite `docker-compose.yml`:

```yaml
services:
  api:
    # ... configuração existente
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Múltiplas instâncias (Load Balancing)

Use Docker Swarm ou Kubernetes para escalar horizontalmente.

---

## 🔗 Endpoints da API

Após o deploy, a API estará disponível em:

- **Health Check:** `http://seu-dominio.com/health`
- **Gerar Clips:** `POST http://seu-dominio.com/viral`
- **Status do Job:** `GET http://seu-dominio.com/status/{job_id}`
- **Listar Jobs:** `GET http://seu-dominio.com/jobs`
- **Buscar Clips por Job:** `GET http://seu-dominio.com/clips/{job_id}`

### Exemplo de uso:

```bash
# Iniciar processamento
curl -X POST http://seu-dominio.com/viral \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "limit": 3
  }'

# Resposta:
# {
#   "message": "Viral processing started",
#   "job_id": "abc-123-def-456",
#   "status_endpoint": "/status/abc-123-def-456"
# }

# Verificar status
curl http://seu-dominio.com/status/abc-123-def-456
```

---

## 📞 Suporte

Para problemas ou dúvidas:
- Verifique os logs: `docker-compose logs -f`
- Teste o health check: `curl localhost:8000/health`
- Monitore recursos: `docker stats`

**Bom deploy! 🚀**
