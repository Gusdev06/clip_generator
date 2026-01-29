# Smart Crop - Guia de Uso

## Sistema Completo Implementado ✅

Sistema profissional de corte inteligente para criar clips virais para TikTok/Instagram Reels.

```
┌─────────────────────────────────────┐
│  1. Face Detection (MediaPipe)      │ → 468 landmarks faciais precisos
│  2. Speaker Diarization (pyannote)  │ → identifica quem fala quando
│  3. Lip Sync Detection              │ → correlaciona boca + áudio
│  4. Dynamic Crop + Smooth Tracking  │ → crop suave seguindo speaker
└─────────────────────────────────────┘
```

## Instalação

### 1. Instalar dependências

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Instalar novas dependências
pip install -r requirements.txt
```

**Nota**: A instalação pode demorar alguns minutos pois inclui PyTorch e pyannote.audio.

### 2. Obter Token do HuggingFace (Opcional, mas recomendado)

Para usar Speaker Diarization (identificar múltiplos speakers):

1. Criar conta em: https://huggingface.co/
2. Gerar token em: https://huggingface.co/settings/tokens
3. Aceitar licença do modelo: https://huggingface.co/pyannote/speaker-diarization

## Modos de Uso

### Modo Básico (Sem Speaker Diarization)

Usa apenas face tracking + lip sync + audio analysis:

```bash
./run.sh "https://youtube.com/..." --smart
```

ou

```bash
source venv/bin/activate
python main.py "https://youtube.com/..." --smart
```

### Modo Completo (Com Speaker Diarization)

Identifica múltiplos speakers + tudo do modo básico:

```bash
```

### Modo Debug

Gera vídeo extra com visualização de detecção:

```bash
python main.py "video.mp4" --smart --debug
```

Isso cria dois arquivos:
- `video_smart.mp4` - Clip final vertical
- `video_smart_debug.mp4` - Vídeo com overlays de debug

### Processar Arquivo Local

```bash
python main.py -f /path/to/video.mp4 --smart
```

## Comparação de Modos

| Feature | Modo Básico | Modo Smart (Sem HF Token) | Modo Smart (Com HF Token) |
|---------|-------------|---------------------------|---------------------------|
| Face Detection | Haar Cascade | MediaPipe (468 landmarks) | MediaPipe (468 landmarks) |
| Tracking | Básico | Smooth com landmarks | Smooth com landmarks |
| Audio Analysis | ❌ | ✅ Voice Activity Detection | ✅ Voice Activity Detection |
| Lip Sync | ❌ | ✅ Correlação boca-áudio | ✅ Correlação boca-áudio |
| Speaker Diarization | ❌ | ❌ | ✅ Multi-speaker |
| Dynamic Crop | ❌ | ✅ Segue speaker ativo | ✅ Segue speaker ativo |
| Ideal para | Vídeos simples | 1 pessoa falando | Múltiplas pessoas |

## Exemplos de Uso

### 1. Podcast com 2 pessoas
```bash
python main.py "podcast.mp4" --smart --hf-token YOUR_TOKEN
```
O sistema vai automaticamente seguir quem está falando.

### 2. Entrevista
```bash
python main.py "interview.mp4" --smart --hf-token YOUR_TOKEN --debug
```
Crop dinâmico entre entrevistador e entrevistado + vídeo debug.

### 3. Vídeo educacional (1 pessoa)
```bash
python main.py "aula.mp4" --smart
```
Enquadramento inteligente mesmo sem HF token.

### 4. Live/Stream
```bash
python main.py "https://youtube.com/watch?v=..." --smart --hf-token YOUR_TOKEN
```

## Como Funciona

### Pipeline Completo

1. **Pré-processamento de Áudio**
   ```
   Extrai áudio → Detecta voz ativa → Identifica speakers → Calcula energia
   ```

2. **Análise Frame-a-Frame**
   ```
   Detecta rostos → Extrai 468 landmarks → Mede abertura da boca
   ```

3. **Correlação Lip-Sync**
   ```
   Movimento da boca ↔ Energia do áudio → Identifica quem está falando
   ```

4. **Crop Dinâmico**
   ```
   Foca no speaker ativo → Transição suave → Enquadramento profissional
   ```

### Configurações Avançadas

Edite `config.py` para ajustar:

```python
# Posição vertical do rosto (0.35 = terço superior)
FACE_VERTICAL_POSITION = 0.35

# Smoothing (15-30 frames recomendado)
SMOOTHING_WINDOW = 20

# Margens ao redor do rosto
HORIZONTAL_MARGIN = 1.5
VERTICAL_MARGIN = 2.0
```

## Troubleshooting

### Erro: "pyannote.audio not available"
```bash
pip install pyannote.audio torch torchaudio
```

### Erro: "Speaker diarization not available"
- Sem HF token: Sistema funciona sem diarization
- Com HF token: Verifique se aceitou a licença do modelo

### Face não detectada
- Ajuste `MIN_DETECTION_CONFIDENCE` no config.py (menor = mais sensível)
- Certifique-se que o rosto está visível e bem iluminado

### Crop muito tremido
- Aumente `SMOOTHING_WINDOW` no config.py
- Valores recomendados: 15-30 frames

### Processamento muito lento
- Modo Smart é mais lento que básico (análise de áudio + landmarks)
- Para vídeos longos: considere cortar antes de processar
- GPU acelera significativamente (PyTorch com CUDA)

## Performance

**Tempos aproximados** (vídeo 1920x1080, 60s):

- Modo básico: ~30 segundos
- Smart crop (sem HF): ~2-3 minutos
- Smart crop (com HF): ~5-7 minutos (primeira vez, depois usa cache)

**GPU vs CPU**:
- Com GPU NVIDIA: 3-4x mais rápido
- CPU é suficiente para vídeos curtos (<5 min)

## Próximos Passos

Possíveis melhorias futuras:

- [ ] Legendas automáticas (Whisper)
- [ ] Detecção de momentos virais (picos de energia/emoção)
- [ ] Cortes automáticos em silêncios
- [ ] Exportação direta para redes sociais
- [ ] Multi-clip generation (vários clips de um vídeo longo)
- [ ] Zoom dinâmico baseado em ênfase vocal

## Suporte

- Issues: https://github.com/your-repo/issues
- Documentação MediaPipe: https://google.github.io/mediapipe/
- Documentação pyannote: https://github.com/pyannote/pyannote-audio

---

**Desenvolvido para criar clips profissionais para TikTok, Instagram Reels e YouTube Shorts**
