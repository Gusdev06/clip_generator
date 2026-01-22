"""
Title Generator - Gera títulos ultra chamativos em português
Utiliza OpenAI GPT para criar títulos otimizados para engajamento
"""
import json
from typing import List, Dict
from openai import OpenAI
import config


class TitleGenerator:
    def __init__(self, model="gpt-4o"):
        """
        Initialize the Title Generator

        Args:
            model: OpenAI model to use (default: gpt-4o)
        """
        self.api_key = config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

        # Prompt expert para geração de títulos virais em português
        self.system_prompt = """
Você é um especialista em criar títulos ultra chamativos e virais para vídeos curtos no TikTok, Reels e YouTube Shorts, especificamente para o público brasileiro.

**Sua missão:** Gerar 3 variações de títulos EXTREMAMENTE CHAMATIVOS em português brasileiro que maximizem:
- Taxa de clique (CTR)
- Tempo de retenção nos primeiros segundos
- Compartilhamentos

**REGRAS OBRIGATÓRIAS:**

1. **Gatilhos Mentais Poderosos:**
   - Curiosidade extrema ("O que NINGUÉM te conta sobre...")
   - FOMO (medo de ficar de fora)
   - Benefício claro e tangível
   - Números específicos ("3 formas SECRETAS...")
   - Palavras de poder: SEGREDO, DESCOBRI, CHOCANTE, NINGUÉM, REVELADO

2. **Estruturas Comprovadas:**
   - Pergunta impossível de ignorar
   - Promessa + Prova Social ("Como eu fiz X fazendo Y")
   - Contrarian ("Pare de fazer X, faça Y ao invés")
   - "Antes vs Depois" implícito
   - Lista com número ímpar (3, 5, 7)

3. **Emoções Alvo:**
   - Curiosidade intensa
   - Surpresa/Choque
   - Aspiração/Inveja positiva
   - Medo de estar errado/perdendo

4. **Tom e Linguagem:**
   - Informal, próximo, como amigo contando segredo
   - Use "você" para criar conexão
   - Emojis estratégicos (máx 1-2 por título)
   - Gírias leves quando apropriado
   - CAIXA ALTA estratégica para ênfase

5. **Tamanho:**
   - Mínimo: 40 caracteres
   - Máximo: 80 caracteres
   - Direto ao ponto, zero palavras desnecessárias

**EXEMPLOS DE TÍTULOS VIRAIS:**

❌ RUIM: "Dicas de produtividade para o dia a dia"
✅ BOM: "3 hacks que DOBRARAM minha produtividade (ninguém fala do 3º)"

❌ RUIM: "Como fazer uma receita fácil"
✅ BOM: "Esse truque de CHEF mudou minha vida na cozinha 🤯"

❌ RUIM: "Informações sobre finanças pessoais"
✅ BOM: "Por que 90% das pessoas NUNCA vão ficar ricas? (revelação)"

**FORMATO DE SAÍDA (JSON):**
{
  "titles": [
    "Título viral 1 aqui",
    "Título viral 2 aqui",
    "Título viral 3 aqui"
  ]
}

**IMPORTANTE:** Retorne APENAS o JSON válido, sem texto adicional.
"""

    def generate_titles(self, clip_data: Dict) -> List[str]:
        """
        Gera 3 títulos chamativos em português para um clip

        Args:
            clip_data: Dicionário com informações do clip:
                - title: Título original do clip
                - reasoning: Explicação do potencial viral
                - category: Categoria do clip
                - hook_type: Tipo de gancho
                - psychological_triggers: Gatilhos psicológicos
                - duration: Duração em segundos
                - viral_score: Score viral (0-10)

        Returns:
            Lista com 3 títulos em português
        """
        print("  Gerando títulos chamativos em português...")

        # Prepara o contexto do clip
        context = f"""
INFORMAÇÕES DO CLIP:
- Título Original: {clip_data.get('title', 'N/A')}
- Categoria: {clip_data.get('category', 'N/A')}
- Tipo de Gancho: {clip_data.get('hook_type', 'N/A')}
- Gatilhos Psicológicos: {', '.join(clip_data.get('psychological_triggers', []))}
- Explicação: {clip_data.get('reasoning', 'N/A')}
- Duração: {clip_data.get('duration', 0):.1f}s
- Score Viral: {clip_data.get('viral_score', 0)}/10

TAREFA: Gere 3 variações de títulos ULTRA CHAMATIVOS em português brasileiro que capturem a essência viral deste clip e maximizem cliques e compartilhamentos.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context}
                ],
                response_format={"type": "json_object"},
                temperature=0.9,  # Alta criatividade
                max_tokens=500
            )

            content = response.choices[0].message.content
            data = json.loads(content)
            titles = data.get("titles", [])

            if len(titles) != 3:
                print(f"  ⚠️  Aviso: Esperava 3 títulos, recebi {len(titles)}")

            print("  ✓ Títulos gerados com sucesso!")
            for i, title in enumerate(titles, 1):
                print(f"    {i}. {title}")

            return titles

        except Exception as e:
            print(f"  ❌ Erro ao gerar títulos: {e}")
            # Fallback: retorna títulos genéricos baseados no título original
            fallback_title = clip_data.get('title', 'Clip Viral')
            return [
                f"🔥 {fallback_title} - VOCÊ PRECISA VER ISSO!",
                f"O SEGREDO que ninguém conta sobre {fallback_title}",
                f"Como {fallback_title} pode MUDAR TUDO (chocante)"
            ]

    def create_metadata_json(self, clip_data: Dict, output_path: str) -> str:
        """
        Cria um JSON com score e títulos para um clip

        Args:
            clip_data: Dados do clip (ViralClip.to_dict())
            output_path: Caminho do arquivo do clip

        Returns:
            Caminho do arquivo JSON criado
        """
        # Gera os títulos
        titles = self.generate_titles(clip_data)

        # Cria o metadata
        metadata = {
            "clip_file": output_path,
            "viral_score": clip_data.get('viral_score', 0),
            "duration": clip_data.get('duration', 0),
            "category": clip_data.get('category', 'General'),
            "hook_type": clip_data.get('hook_type', 'N/A'),
            "psychological_triggers": clip_data.get('psychological_triggers', []),
            "stepps_score": clip_data.get('stepps_score', []),
            "estimated_retention": clip_data.get('estimated_retention', 0),
            "share_probability": clip_data.get('share_probability', 'N/A'),
            "reasoning": clip_data.get('reasoning', ''),
            "suggested_titles_pt": titles
        }

        # Salva o JSON ao lado do clip
        json_path = output_path.replace('.mp4', '_metadata.json')

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"  ✓ Metadata salvo em: {json_path}")
        return json_path


if __name__ == "__main__":
    # Teste do gerador
    generator = TitleGenerator()

    # Clip de exemplo
    sample_clip = {
        'title': 'The Secret Productivity Hack Nobody Talks About',
        'category': 'Contrarian Truth',
        'hook_type': 'Question Hook',
        'psychological_triggers': ['Curiosity', 'Practical Value', 'Social Currency'],
        'reasoning': 'Strong hook with open loop and practical payoff',
        'duration': 55.0,
        'viral_score': 9.2,
        'estimated_retention': 78,
        'share_probability': 'High'
    }

    titles = generator.generate_titles(sample_clip)
    print("\nTítulos gerados:")
    for i, title in enumerate(titles, 1):
        print(f"{i}. {title}")
