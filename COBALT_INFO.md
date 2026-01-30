# 🚀 Cobalt API - YouTube Download sem Cookies

## O que é Cobalt?

**Cobalt.tools** é uma API gratuita e open-source para download de vídeos de YouTube, TikTok, Instagram e outras plataformas.

### ✅ **Vantagens:**
- **Sem cookies necessários** - funciona direto em servidores
- **Grátis** - API pública sem limites rígidos
- **Confiável** - menos bloqueios que yt-dlp
- **Rápido** - download direto via CDN
- **Open Source** - https://github.com/imputnet/cobalt

---

## 🔧 Como Funciona

O sistema agora usa **Cobalt como método primário** e **yt-dlp como fallback**:

1. **Tenta Cobalt primeiro** (sem cookies, sem bloqueios)
2. **Se Cobalt falhar**, usa yt-dlp (com cookies se configurado)

---

## ⚙️ Configuração

### **Padrão (Recomendado):**

Cobalt já está **ativado por padrão**. Não precisa configurar nada!

```env
# .env (já habilitado por padrão)
USE_COBALT_API=true
```

### **Desabilitar Cobalt (usar só yt-dlp):**

Se você preferir usar apenas yt-dlp:

```env
USE_COBALT_API=false
```

### **Usar sua própria instância Cobalt:**

Se você hospedar sua própria instância do Cobalt:

```env
USE_COBALT_API=true
COBALT_API_URL=https://sua-instancia.com
```

---

## 📊 Logs de Download

Quando funciona com Cobalt, você verá:

```
Downloading audio from: https://www.youtube.com/watch?v=...
  Attempting download via Cobalt API...
  Downloading from Cobalt...
  ✅ Downloaded via Cobalt: /app/downloads/video.mp3
```

Se Cobalt falhar e usar yt-dlp:

```
Downloading audio from: https://www.youtube.com/watch?v=...
  Attempting download via Cobalt API...
  ⚠️  Cobalt API error: Video not available
  Cobalt failed, falling back to yt-dlp...
Downloading audio via yt-dlp from: https://www.youtube.com/watch?v=...
  Using cookies from file: /app/youtube_cookies.txt
```

---

## 🐛 Troubleshooting

### **1. Cobalt retorna erro**

**Sintoma:**
```
⚠️  Cobalt API error: Video is private
```

**Solução:** Cobalt não suporta vídeos privados. O sistema automaticamente vai tentar yt-dlp como fallback.

### **2. Cobalt API timeout**

**Sintoma:**
```
⚠️  Cobalt API timeout
```

**Solução:** API oficial pode estar lenta. Considere hospedar sua própria instância.

### **3. Ambos falharam (Cobalt + yt-dlp)**

**Sintoma:**
```
ERROR: [youtube] lXP_JM6dBuk: ...
```

**Solução:**
1. Verifique se o vídeo existe e é público
2. Configure cookies do YouTube para yt-dlp (veja [YOUTUBE_COOKIES_GUIDE.md](YOUTUBE_COOKIES_GUIDE.md))

---

## 🏗️ Hospedar sua Própria Instância Cobalt

Se você quiser mais controle, pode hospedar o Cobalt:

### **Docker:**

```bash
docker run -d \
  --name cobalt-api \
  -p 9000:9000 \
  ghcr.io/imputnet/cobalt:latest
```

### **Configurar no projeto:**

```env
COBALT_API_URL=http://localhost:9000
```

---

## 📖 Referências

- **Cobalt GitHub:** https://github.com/imputnet/cobalt
- **Documentação API:** https://github.com/imputnet/cobalt/blob/current/docs/api.md
- **Instância Oficial:** https://cobalt.tools

---

## 💡 Quando Usar Cada Um?

| Situação | Recomendação |
|----------|--------------|
| Servidor em produção | **Cobalt** (padrão) |
| Vídeos privados/restritos | **yt-dlp** (com cookies) |
| Vídeos de idade restrita | **yt-dlp** (com cookies) |
| Download em massa | **Cobalt** (sem rate limits pesados) |
| Máxima qualidade | **Ambos** (Cobalt tenta primeiro) |

---

**Por padrão, o sistema já usa Cobalt. Você não precisa fazer nada! 🎉**
