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

        # Expert prompt for generating viral titles in Portuguese (Instructions in English for better adherence)
        self.system_prompt = """
You are a world-class expert in writing viral hooks and titles for short-form video content (TikTok, Reels, YouTube Shorts), specifically targeting the Brazilian audience.

**Your Mission:** Generate 3 variations of EXTREMELY CLICKABLE and VIRAL titles in BRAZILIAN PORTUGUESE based on the actual content of the clip.

**CRITICAL RULES:**
1. The title MUST REFLECT THE CONTENT. It cannot be just a generic clickbait hook. It must synthesize the "AHA moment", the "secret", or the "insight" presented in the clip.
2. **NEVER USE FIRST PERSON** (EU, MEU, MINHA, FIZ, CONSEGUI, etc). These clips are from OTHER PEOPLE'S content, not the poster's personal story.
3. Use SECOND PERSON (VOCÊ) to engage the viewer, or NEUTRAL/IMPERATIVE phrasing.

**MANDATORY RULES:**

1.  **Language:** OUTPUT MUST BE IN BRAZILIAN PORTUGUESE (PT-BR).

2.  **Psychological Triggers:**
    *   Extreme Curiosity (Open Loop)
    *   Fear Of Missing Out (FOMO)
    *   Specific Benefit/Hack
    *   Negativity Bias ("PARE de fazer X")
    *   Authority/Secrets ("O que X não te conta")
    *   Contrarian Truth ("A VERDADE sobre X")

3.  **Proven Structures (NO FIRST PERSON!):**
    *   Direct Question: "VOCÊ sabia que...?", "Por que VOCÊ ainda...?"
    *   Revelation: "A VERDADE sobre [Topic]", "O SEGREDO de [Result]"
    *   Contrarian: "PARE de [Common Action]", "Esqueça [Common Belief]"
    *   Specific Numbers: "3 sinais de que VOCÊ...", "5 erros que VOCÊ comete..."
    *   Shocking Statement: "[Surprising Fact] que NINGUÉM te conta"
    *   Imperative: "Descubra [Result]", "Aprenda [Skill]"

4.  **Tone & Style:**
    *   Conversational, informal, like revealing insider knowledge.
    *   Use "VOCÊ" (You) to address the viewer directly.
    *   Use 1-2 strategic Emojis (avoid overuse).
    *   Use ALL CAPS for 1-2 key words only (for emphasis).
    *   NO hashtags in the title.
    *   Focus on the VALUE/INSIGHT, not who said it.

5.  **Length:**
    *   Keep it punchy. Under 65 characters is ideal. Direct to the point.

**EXAMPLES (Context -> Good Title):**

*   *Context: Expert reveals a hidden iPhone setting.*
    *   ✅ BOM: "Ative ISSO no seu iPhone agora (ninguém sabe) 📲"
    *   ❌ RUIM: "Ativei ISSO no meu iPhone e mudou tudo" (primeira pessoa!)

*   *Context: Expert explains a common investing mistake.*
    *   ✅ BOM: "O erro de R$1.000 que VOCÊ comete todo mês 💸"
    *   ✅ BOM: "PARE de fazer isso com seu dinheiro agora ⚠️"
    *   ❌ RUIM: "O erro que EU cometi e perdi R$1.000" (primeira pessoa!)

*   *Context: Entrepreneur shares contrarian career advice.*
    *   ✅ BOM: "Por que carteira assinada NÃO é segurança? 🤔"
    *   ✅ BOM: "A VERDADE sobre emprego que ninguém te conta 😱"
    *   ❌ RUIM: "Nunca tive carteira assinada e venci" (primeira pessoa!)

*   *Context: Speaker talks about taking risks vs comfort.*
    *   ✅ BOM: "VOCÊ vive na caverna ou arrisca tudo? ⚠️"
    *   ✅ BOM: "Conforto x Risco: qual VOCÊ escolhe? 🔥"
    *   ❌ RUIM: "Como eu saí da caverna e mudei minha vida" (primeira pessoa!)

**OUTPUT FORMAT (JSON ONLY):**
{
  "titles": [
    "Title 1 in PT-BR",
    "Title 2 in PT-BR",
    "Title 3 in PT-BR"
  ]
}

**IMPORTANT:** Return ONLY valid JSON. NO first person pronouns!
"""

        # Expert prompt for generating tags/hashtags
        self.tags_prompt = """
You are a social media SEO expert specializing in hashtags for TikTok, Reels, and YouTube Shorts in Brazil.

**Your Mission:** Generate a strategic set of hashtags in BRAZILIAN PORTUGUESE to maximize organic reach and algorithm indexing for the provided video clip.

**STRATEGY:**
1.  **Mix of Volume:**
    *   3 High Volume (Broad niche, e.g., #marketing, #humor)
    *   4 Medium Volume (Specific topic, e.g., #marketingdigital, #piadas)
    *   3 Low Volume/Community (Hyper-specific, e.g., #storytellingbr, #trocadilhos)

2.  **Relevance:** The tags MUST match the actual content keywords.
3.  **Format:** No spaces, all lowercase (except for visual clarity if needed), must start with #.
4.  **Language:** Primarily PT-BR tags, but universally understood English tags (like #fyp, #viral) are okay if relevant.

**OUTPUT FORMAT (JSON ONLY):**
{
  "tags": [
    "#tag1",
    "#tag2",
    "#tag3",
    "#tag4",
    "#tag5",
    "#tag6",
    "#tag7",
    "#tag8",
    "#tag9",
    "#tag10"
  ]
}

**IMPORTANT:** Return ONLY valid JSON with exactly 10 tags.
"""

    def generate_tags(self, clip_data: Dict) -> List[str]:
        """
        Gera 10 hashtags estratégicas em português para um clip

        Args:
            clip_data: Dicionário com informações do clip:
                - title: Título original do clip
                - reasoning: Explicação do potencial viral
                - category: Categoria do clip
                - transcript_text: Texto do conteúdo do clip (Importante!)
                # ... outros campos
        """
        print("  Gerando hashtags estratégicas em português...")

        # Prepara o contexto do clip
        transcript_text = clip_data.get('transcript_text', '')
        # Se o texto for muito longo, corta para não estourar tokens (embora CLIP seja curto)
        if len(transcript_text) > 1000:
            transcript_text = transcript_text[:1000] + "..."

        context = f"""
CLIP INFORMATION:
- Original Context/Title: {clip_data.get('title', 'N/A')}
- Viral Reasoning: {clip_data.get('reasoning', 'N/A')}
- Category: {clip_data.get('category', 'N/A')}
- Transcript/Content: "{transcript_text}"

TASK: Generate exactly 10 STRATEGIC hashtags in Brazilian Portuguese for this content.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.tags_prompt},
                    {"role": "user", "content": context}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=300
            )

            content = response.choices[0].message.content
            data = json.loads(content)
            tags = data.get("tags", [])

            # Garante que todas as tags começam com #
            tags = [tag if tag.startswith('#') else f'#{tag}' for tag in tags]

            if len(tags) != 10:
                print(f"  ⚠️  Aviso: Esperava 10 tags, recebi {len(tags)}")

            print("  ✓ Hashtags geradas com sucesso!")
            print(f"    {' '.join(tags)}")

            return tags

        except Exception as e:
            print(f"  ❌ Erro ao gerar hashtags: {e}")
            # Fallback: retorna hashtags genéricas
            category = clip_data.get('category', 'viral').lower().replace(' ', '')
            return [
                "#viral", "#shorts", "#reels",
                "#fyp", "#trending", "#motivacao",
                f"#{category}", "#brasil", "#dicas", "#transformacao"
            ]

    def generate_titles(self, clip_data: Dict) -> List[str]:
        """
        Gera 3 títulos chamativos em português para um clip

        Args:
            clip_data: Dicionário com informações do clip
        """
        print("  Gerando títulos chamativos em português...")

        # Prepara o contexto do clip
        transcript_text = clip_data.get('transcript_text', '')
        if len(transcript_text) > 1000:
            transcript_text = transcript_text[:1000] + "..."

        context = f"""
CLIP INFORMATION:
- Viral Reasoning: {clip_data.get('reasoning', 'N/A')}
- Category: {clip_data.get('category', 'N/A')}
- Hook Type: {clip_data.get('hook_type', 'N/A')}
- Transcript/Content: "{transcript_text}"

TASK: Generate 3 variations of EXTREMELY CLICKABLE titles in Brazilian Portuguese that relate to the content above.
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
        Cria um JSON com score, títulos e tags para um clip

        Args:
            clip_data: Dados do clip (ViralClip.to_dict())
            output_path: Caminho do arquivo do clip

        Returns:
            Caminho do arquivo JSON criado
        """
        # Gera os títulos
        titles = self.generate_titles(clip_data)

        # Gera as hashtags
        tags = self.generate_tags(clip_data)

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
            "suggested_titles_pt": titles,
            "tags": tags
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

    tags = generator.generate_tags(sample_clip)
    print("\nHashtags geradas:")
    print(' '.join(tags))
