"""
Test script para o TitleGenerator
"""
from title_generator import TitleGenerator

def test_title_generation():
    print("\n" + "="*60)
    print("🧪 TESTANDO GERADOR DE TÍTULOS")
    print("="*60)

    # Inicializa o gerador
    try:
        generator = TitleGenerator()
        print("✓ TitleGenerator inicializado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar TitleGenerator: {e}")
        return

    # Clip de teste
    sample_clips = [
        {
            'title': 'The Secret Productivity Hack Nobody Talks About',
            'category': 'Contrarian Truth',
            'hook_type': 'Question Hook',
            'psychological_triggers': ['Curiosity', 'Practical Value', 'Social Currency'],
            'reasoning': 'Strong hook with open loop and practical payoff',
            'duration': 55.0,
            'viral_score': 9.2,
            'estimated_retention': 78,
            'share_probability': 'High',
            'stepps_score': ['Social Currency', 'Practical Value', 'Emotion']
        },
        {
            'title': 'Why 90% of Entrepreneurs Fail (shocking truth)',
            'category': 'Educational',
            'hook_type': 'Pattern Interrupt',
            'psychological_triggers': ['Fear', 'Curiosity', 'Social Currency'],
            'reasoning': 'Controversial opening with data-backed insights',
            'duration': 48.0,
            'viral_score': 8.9,
            'estimated_retention': 72,
            'share_probability': 'High',
            'stepps_score': ['Emotion', 'Practical Value', 'Stories']
        },
        {
            'title': 'This Cooking Trick Changed My Life',
            'category': 'Life Hack',
            'hook_type': 'Proof-First Hook',
            'psychological_triggers': ['Awe', 'Practical Value', 'Humor'],
            'reasoning': 'Surprising demonstration with immediate practical value',
            'duration': 42.0,
            'viral_score': 8.5,
            'estimated_retention': 75,
            'share_probability': 'Medium-High',
            'stepps_score': ['Practical Value', 'Public', 'Emotion']
        }
    ]

    print(f"\n📊 Testando com {len(sample_clips)} clips de exemplo\n")

    for i, clip in enumerate(sample_clips, 1):
        print(f"\n{'='*60}")
        print(f"Teste {i}/3: {clip['title']}")
        print(f"  Score: {clip['viral_score']}/10")
        print(f"  Hook: {clip['hook_type']}")
        print(f"  Duração: {clip['duration']}s")
        print(f"{'='*60}\n")

        # Gera títulos
        try:
            titles = generator.generate_titles(clip)

            if titles and len(titles) == 3:
                print(f"\n✅ Sucesso! {len(titles)} títulos gerados:")
                for j, title in enumerate(titles, 1):
                    print(f"  {j}. {title}")
                    print(f"     Tamanho: {len(title)} caracteres")
            else:
                print(f"⚠️  Aviso: Número de títulos inesperado: {len(titles)}")

        except Exception as e:
            print(f"❌ Erro ao gerar títulos: {e}")

    # Teste de criação de metadata JSON
    print(f"\n{'='*60}")
    print("Testando geração de metadata JSON completo")
    print(f"{'='*60}\n")

    test_output_path = "outputs/test_clip_final.mp4"

    try:
        metadata_path = generator.create_metadata_json(
            sample_clips[0],
            test_output_path
        )

        print(f"\n✅ Metadata JSON criado com sucesso!")
        print(f"   Arquivo: {metadata_path}")

        # Lê e exibe o conteúdo
        import json
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        print("\n📄 Conteúdo do JSON:")
        print(json.dumps(metadata, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Erro ao criar metadata JSON: {e}")

    print("\n" + "="*60)
    print("✅ TESTES CONCLUÍDOS")
    print("="*60)


if __name__ == "__main__":
    test_title_generation()
