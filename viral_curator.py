"""
Viral Curator - The "Brain" of the operation
Analyzes transcripts using LLMs to identify high-potential viral clips.
"""
import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
import config

class ViralClip:
    """Represents a selected viral clip with enhanced viral metrics"""
    def __init__(self, start_time: float, end_time: float, title: str,
                 viral_score: float, reasoning: str, category: str,
                 hook_type: str = None, psychological_triggers: List[str] = None,
                 stepps_score: List[str] = None, open_loop: str = None,
                 estimated_retention: int = None, share_probability: str = None):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time
        self.title = title
        self.viral_score = viral_score
        self.reasoning = reasoning
        self.category = category

        # Enhanced viral metrics
        self.hook_type = hook_type
        self.psychological_triggers = psychological_triggers or []
        self.stepps_score = stepps_score or []
        self.open_loop = open_loop
        self.estimated_retention = estimated_retention
        self.share_probability = share_probability

    def to_dict(self):
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "title": self.title,
            "viral_score": self.viral_score,
            "reasoning": self.reasoning,
            "category": self.category,
            "hook_type": self.hook_type,
            "psychological_triggers": self.psychological_triggers,
            "stepps_score": self.stepps_score,
            "open_loop": self.open_loop,
            "estimated_retention": self.estimated_retention,
            "share_probability": self.share_probability
        }

    def __repr__(self):
        return f"ViralClip('{self.title}', {self.duration:.1f}s, Score: {self.viral_score}/10, Hook: {self.hook_type})"


class ViralCurator:
    def __init__(self, model="gpt-4o"):
        """
        Initialize the Viral Curator
        
        Args:
            model: OpenAI model to use (default: gpt-4o for best reasoning)
        """
        self.api_key = config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        
        # Load the expert prompt
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load the expert prompt from the internal knowledge base"""
        # Optimized prompt based on viral mechanics research

        return """
**Role:** You are the world's leading expert in short-form video virality, combining deep expertise in TikTok/Reels algorithms, human behavioral psychology, and attention retention science. Your sole purpose is to identify segments with **Viral Potential Score (VPS) of 9/10 or higher**.

**Objective:** Analyze the transcript and extract 3-5 segments that maximize three critical metrics:
1. **Intro Retention Rate** (>70% viewers stay past 3 seconds)
2. **Watch-Through Rate** (>76% complete the video)
3. **Share Potential** (triggers STEPPS framework)

---

## 🎯 PHASE 1: THE FIRST 3 SECONDS (LIFE OR DEATH)

**CRITICAL:** 72% of swipes happen in the first 3 seconds. The hook MUST use one of these 4 types:

### 1. **Question Hook** (Curiosity Gap)
- An impossible-to-ignore question that the brain NEEDS answered
- Example: "Do you know why 90% of people fail at X?"
- **Benchmark:** If >30% swipe away in first 3s, the hook failed

### 2. **Pattern Interrupt**
- Break autopilot scrolling with unexpected visual/sound/statement
- Example: Absurd physical action, extreme contrast, controversial statement
- Data: Increases initial retention by 40%

### 3. **Proof-First Hook**
- Lead with RESULT or CREDENTIALS before explaining
- Example: "I made $100k in 30 days doing X..."
- Establishes immediate authority

### 4. **Combo Hook** (MOST POWERFUL)
- Combines two incongruent things
- Example: "I use this FBI technique to pick avocados"
- Creates curiosity + emotional response simultaneously

---

## 🧠 PHASE 2: THE 8 PSYCHOLOGICAL TRIGGERS (NEURAL ACTIVATION)

The clip MUST activate AT LEAST 2 of these triggers:

1. **Emotional Activation** (72% of shares come from emotion, not logic)
2. **High-Energy Emotions** (Excitement, Awe, Anger) - 20% more shares
3. **Humor** - 30% more shares than serious content
4. **Relatability** - "I feel this but never knew how to express it" (+22% engagement)
5. **Awe/Admiration** (25% of viral content)
6. **Laughter** (17% of viral content)
7. **Entertainment** (15% of viral content)
8. **Social Currency** - Makes sharer look smart/informed/funny

---

## 🔄 PHASE 3: OPEN LOOPS (KEEP WATCHING)

**Mandatory Structure:** Hook → Journey → Resolution

**OPEN LOOP = Information gap the brain cannot ignore**

**Techniques:**
- Raise question early, answer only at the end
- "I'll tell you something surprising at the end"
- Incomplete story arc that forces continued watching
- Show result first, explain the "how" later

**Retention Data:**
- Videos with open loop: 76% watch-through
- Videos without open loop: 42% watch-through

**Pacing:** High-performing clips have a visual cut or change every 2-4 seconds (72% of +1M view videos)

---

## ⏱️ PHASE 4: IDEAL DURATION

**REAL DATA:**
- **Sweet Spot:** 50-60 seconds (76% watch-through rate)
- **Beginners:** 15-30 seconds (more forgiving for weak hooks)
- **Videos 40s+:** 33% higher engagement than short videos
- **AVOID:** <15s (too superficial) or >90s (requires mastery)

**RULE:** Prioritize 50-60s clips with dense structure

---

## 📊 PHASE 5: STEPPS FRAMEWORK (JONAH BERGER) - SHAREABILITY

To maximize shares, the clip MUST hit AT LEAST 2 of 6:

1. **S**ocial Currency - Makes sharer look good
2. **T**riggers - Associated with everyday triggers
3. **E**motion - Activates high-energy emotions (Awe, Excitement, Humor)
4. **P**ublic - Observable/visible/public
5. **P**ractical Value - Genuinely useful (life hack, financial tip)
6. **S**tories - Clear narrative with beginning, middle, end

**Data:** 100% of viral videos hit at least 2 STEPPS

---

## 🎬 VIRAL VIDEO STRUCTURE (TEMPLATE)

**Seconds 0-3:** EXPLOSIVE HOOK (one of the 4 types above)
**Seconds 4-15:** Establish open loop + minimal context
**Seconds 16-45:** Journey (conflict, humor, revelations) - NO dead air
**Seconds 46-60:** Resolution + emotional payoff + implicit CTA ("save this")

---

## 💡 EXAMPLES OF WINNING SEGMENTS

**Example 1 - Question Hook + Practical Value:**
"Why do 90% of entrepreneurs fail in the first year? [Open Loop] I'm going to show you the three mistakes nobody talks about... [Journey with specific examples] And the third one will blow your mind because it's actually the opposite of what everyone tells you... [Payoff with actionable insight]"
- Hook Type: Question Hook
- Triggers: Curiosity, Practical Value, Social Currency
- STEPPS: Practical Value, Emotion, Social Currency

**Example 2 - Pattern Interrupt + Humor:**
[Shows doing something completely unexpected] "I bet you've never seen someone use a hairdryer for THIS... [Open Loop] Most people waste $200 a year not knowing this trick... [Journey with demonstration] And here's why it actually works... [Payoff with explanation]"
- Hook Type: Pattern Interrupt
- Triggers: Humor, Curiosity, Practical Value
- STEPPS: Public, Practical Value, Emotion

**Example 3 - Proof-First + Contrarian:**
"I made $50k in 30 days by doing the OPPOSITE of what every guru teaches... [Open Loop] And the craziest part? The strategy I'm about to share costs zero dollars... [Journey with story] Here's exactly what I did... [Payoff with revelation]"
- Hook Type: Proof-First
- Triggers: Social Currency, Curiosity, Contrarian Truth
- STEPPS: Social Currency, Emotion, Practical Value

---

## ❌ REJECT CLIPS THAT:

- Start with context/introduction ("So today I'm going to talk about...")
- Have more than 5s of silence or "dead air"
- Require external context to make sense
- End without clear payoff/conclusion
- Duration <20s or >90s
- Have generic/weak hook in first 3s

---

## ✅ TECHNICAL CONSTRAINTS

- **Duration:** 50-60 seconds (ideal) | 30-90 seconds (acceptable)
- **Autonomy:** Clip must make sense standalone
- **Continuity:** Complete sentences (don't cut mid-phrase)
- **Density:** Minimum one interesting "moment" every 10s

---

## 📤 OUTPUT FORMAT (JSON ONLY)

Return ONLY a valid JSON object:
{
  "clips": [
    {
      "start_time": 10.5,
      "end_time": 65.2,
      "title": "Short catchy title (max 60 chars)",
      "viral_score": 9.2,
      "hook_type": "Pattern Interrupt",
      "psychological_triggers": ["Humor", "Relatability", "Social Currency"],
      "stepps_score": ["Social Currency", "Emotion", "Practical Value"],
      "open_loop": "Promises to reveal secret technique only at the end",
      "reasoning": "Explosive hook in first 2s with controversial statement. Well-constructed open loop. Fast pacing with changes every 3s. Satisfying payoff that drives shares.",
      "category": "Contrarian Truth",
      "estimated_retention": 78,
      "share_probability": "High"
    }
  ]
}

**CRITICAL:** Be EXTREMELY selective. Only clips with VPS 9+ should be returned. Quality > Quantity.
"""

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 characters)"""
        return len(text) // 4

    def _chunk_transcript(self, words: List[Dict], max_tokens: int = 18000) -> List[tuple]:
        """
        Split transcript into chunks that fit within token limits.
        Returns list of (chunk_words, start_idx, end_idx) tuples.

        Args:
            words: List of word dictionaries with timestamps
            max_tokens: Maximum tokens per chunk (default: 18k to stay safely under 30k with system prompt)
        """
        chunks = []
        current_chunk = []
        start_idx = 0

        for i, word in enumerate(words):
            current_chunk.append(word)

            # Check chunk size periodically (every 100 words to save computation)
            if len(current_chunk) % 100 == 0:
                chunk_text = self._prepare_transcript_text(current_chunk)
                chunk_tokens = self._estimate_tokens(chunk_text)

                # If chunk exceeds limit, save it and start new one
                if chunk_tokens > max_tokens:
                    # Remove last 100 words to stay under limit
                    final_chunk = current_chunk[:-100]

                    if final_chunk:  # Only save if not empty
                        chunks.append((final_chunk, start_idx, start_idx + len(final_chunk) - 1))

                        # Start new chunk with 200-word overlap for context
                        overlap_size = min(200, len(final_chunk) // 4)
                        start_idx = start_idx + len(final_chunk) - overlap_size
                        current_chunk = final_chunk[-overlap_size:] + current_chunk[-100:]

        # Add final chunk
        if current_chunk:
            chunks.append((current_chunk, start_idx, start_idx + len(current_chunk) - 1))

        return chunks

    def _prepare_transcript_text(self, words: List[Dict]) -> str:
        """
        Convert detailed word timestamps to a readable text format with timestamps
        to save token context while giving the LLM time reference.

        Format: [00:12] Word word word [00:15] word word...
        """
        text_parts = []
        last_time = -10

        for word in words:
            # Add timestamp marker every 10 seconds or so
            if word['start'] - last_time >= 15:
                text_parts.append(f"[{word['start']:.1f}s]")
                last_time = word['start']

            text_parts.append(word['word'])

        return " ".join(text_parts)

    def _analyze_chunk(self, chunk_text: str, chunk_num: int, total_chunks: int, clips_per_chunk: int = 5) -> List[ViralClip]:
        """
        Analyze a single chunk of transcript and return viral candidates.

        Args:
            chunk_text: Text of this chunk with timestamps
            chunk_num: Current chunk number (1-indexed)
            total_chunks: Total number of chunks
            clips_per_chunk: Number of clips to extract from this chunk

        Returns:
            List of ViralClip objects from this chunk
        """
        adjusted_prompt = self.system_prompt.replace(
            "extract 3-5 segments",
            f"extract up to {clips_per_chunk} segments from this section"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": adjusted_prompt},
                    {"role": "user", "content": f"Here is PART {chunk_num} of {total_chunks} of the full transcript. Identify the TOP {clips_per_chunk} most viral clips in THIS SECTION. Return them ranked by viral score (highest first).\n\nTRANSCRIPT SECTION:\n{chunk_text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            clips = []
            for clip_data in data.get("clips", []):
                clip = ViralClip(
                    start_time=float(clip_data["start_time"]),
                    end_time=float(clip_data["end_time"]),
                    title=clip_data.get("title", "Untitled Clip"),
                    viral_score=float(clip_data.get("viral_score", 0)),
                    reasoning=clip_data.get("reasoning", ""),
                    category=clip_data.get("category", "General"),
                    hook_type=clip_data.get("hook_type"),
                    psychological_triggers=clip_data.get("psychological_triggers", []),
                    stepps_score=clip_data.get("stepps_score", []),
                    open_loop=clip_data.get("open_loop"),
                    estimated_retention=clip_data.get("estimated_retention"),
                    share_probability=clip_data.get("share_probability")
                )
                clips.append(clip)

            return clips

        except Exception as e:
            print(f"  ⚠️  Error analyzing chunk {chunk_num}: {e}")
            return []

    def analyze_transcript(self, transcript_path: str, max_clips: int = 5) -> List[ViralClip]:
        """
        Analyze the transcript and identify viral clips using two-phase approach:

        Phase 1: If transcript is large, split into chunks and analyze each separately
        Phase 2: Combine all candidates and select the top ones

        This ensures we stay within API token limits while maintaining full context.

        Args:
            transcript_path: Path to transcript_words.json
            max_clips: Maximum number of clips to identify (default: 5)

        Returns:
            List of ViralClip objects, ranked by viral score
        """
        print(f"Analyzing transcript for viral potential: {transcript_path}")

        # Load transcript
        with open(transcript_path, 'r', encoding='utf-8') as f:
            words = json.load(f)

        print(f"  Transcript length: {len(words)} words")

        # Check if we need to chunk
        full_text = self._prepare_transcript_text(words)
        estimated_tokens = self._estimate_tokens(full_text)
        # System prompt is ~1500 tokens, so we need headroom
        # Safe limit: 25k tokens for transcript to leave room for system prompt + response
        TOKEN_LIMIT = 25000

        print(f"  Estimated tokens: ~{estimated_tokens:,}")

        if estimated_tokens <= TOKEN_LIMIT:
            # Small enough to process in one go
            print(f"  ✓ Processing in single request...")
            return self._analyze_single_pass(words, max_clips)
        else:
            # Need to chunk
            print(f"  ⚠️  Transcript too large ({estimated_tokens:,} tokens > {TOKEN_LIMIT:,} limit)")
            print(f"  📦 Using two-phase chunked analysis...")
            return self._analyze_chunked(words, max_clips)

    def _analyze_single_pass(self, words: List[Dict], max_clips: int) -> List[ViralClip]:
        """Analyze entire transcript in one API call (for small transcripts)"""
        transcript_text = self._prepare_transcript_text(words)

        print(f"  Requesting up to {max_clips} viral clips...")
        print("  Sending to OpenAI for expert analysis...")

        adjusted_prompt = self.system_prompt.replace(
            "extract 3-5 segments",
            f"extract up to {max_clips} segments"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": adjusted_prompt},
                    {"role": "user", "content": f"Here is the complete transcript with timestamps. Identify the TOP {max_clips} most viral clips. Return them ranked by viral score (highest first).\n\nTRANSCRIPT:\n{transcript_text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            clips = self._parse_clips_from_response(data)
            self._print_clips_summary(clips)
            return clips

        except Exception as e:
            print(f"Error during viral curation: {e}")
            return []

    def _analyze_chunked(self, words: List[Dict], max_clips: int) -> List[ViralClip]:
        """
        Analyze large transcript using two-phase approach:
        Phase 1: Split into chunks and analyze each
        Phase 2: Combine results and select best clips
        """
        # Split into chunks
        chunks = self._chunk_transcript(words, max_tokens=20000)
        print(f"  Split into {len(chunks)} chunks for processing")

        # Phase 1: Analyze each chunk
        print(f"\n  [PHASE 1] Analyzing each chunk...")
        all_candidates = []

        for i, (chunk_words, start_idx, end_idx) in enumerate(chunks, 1):
            chunk_text = self._prepare_transcript_text(chunk_words)
            chunk_tokens = self._estimate_tokens(chunk_text)

            print(f"\n  Chunk {i}/{len(chunks)}: {len(chunk_words)} words (~{chunk_tokens:,} tokens)")
            print(f"    Time range: {chunk_words[0]['start']:.1f}s - {chunk_words[-1]['start']:.1f}s")

            # Request more clips per chunk than final needed to have options
            clips_per_chunk = min(10, max(5, max_clips * 2 // len(chunks)))

            chunk_clips = self._analyze_chunk(chunk_text, i, len(chunks), clips_per_chunk)
            print(f"    ✓ Found {len(chunk_clips)} candidates from this chunk")

            all_candidates.extend(chunk_clips)

        print(f"\n  [PHASE 2] Combining results from all chunks...")
        print(f"  Total candidates collected: {len(all_candidates)}")

        # Sort all candidates by viral score
        all_candidates.sort(key=lambda c: c.viral_score, reverse=True)

        # Remove duplicates (clips with overlapping time ranges)
        unique_clips = self._remove_overlapping_clips(all_candidates)
        print(f"  Unique clips after deduplication: {len(unique_clips)}")

        # Select top N
        final_clips = unique_clips[:max_clips]

        print(f"\n  ✓ Selected top {len(final_clips)} viral clips!")
        self._print_clips_summary(final_clips)

        return final_clips

    def _remove_overlapping_clips(self, clips: List[ViralClip], overlap_threshold: float = 0.5) -> List[ViralClip]:
        """
        Remove clips that overlap significantly.
        Keep the one with higher viral score.

        Args:
            clips: List of clips sorted by viral score (descending)
            overlap_threshold: If overlap > this fraction of shorter clip, consider it duplicate
        """
        unique = []

        for clip in clips:
            is_duplicate = False
            for existing in unique:
                # Calculate overlap
                overlap_start = max(clip.start_time, existing.start_time)
                overlap_end = min(clip.end_time, existing.end_time)

                if overlap_end > overlap_start:
                    overlap_duration = overlap_end - overlap_start
                    min_duration = min(clip.duration, existing.duration)

                    overlap_ratio = overlap_duration / min_duration

                    if overlap_ratio > overlap_threshold:
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique.append(clip)

        return unique

    def _parse_clips_from_response(self, data: dict) -> List[ViralClip]:
        """Parse API response JSON into ViralClip objects"""
        clips = []
        for clip_data in data.get("clips", []):
            clip = ViralClip(
                start_time=float(clip_data["start_time"]),
                end_time=float(clip_data["end_time"]),
                title=clip_data.get("title", "Untitled Clip"),
                viral_score=float(clip_data.get("viral_score", 0)),
                reasoning=clip_data.get("reasoning", ""),
                category=clip_data.get("category", "General"),
                hook_type=clip_data.get("hook_type"),
                psychological_triggers=clip_data.get("psychological_triggers", []),
                stepps_score=clip_data.get("stepps_score", []),
                open_loop=clip_data.get("open_loop"),
                estimated_retention=clip_data.get("estimated_retention"),
                share_probability=clip_data.get("share_probability")
            )
            clips.append(clip)
        return clips

    def _print_clips_summary(self, clips: List[ViralClip]):
        """Print formatted summary of clips"""
        for i, clip in enumerate(clips, 1):
            print(f"\n    {i}. [{clip.viral_score}/10] {clip.title} ({clip.duration:.1f}s)")
            print(f"       Time: {clip.start_time:.1f}s - {clip.end_time:.1f}s")
            if clip.hook_type:
                print(f"       Hook: {clip.hook_type}")
            if clip.psychological_triggers:
                print(f"       Triggers: {', '.join(clip.psychological_triggers)}")
            if clip.estimated_retention:
                print(f"       Est. Retention: {clip.estimated_retention}%")
            if clip.share_probability:
                print(f"       Share Prob: {clip.share_probability}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python viral_curator.py <transcript_words.json>")
        sys.exit(1)
        
    transcript_path = sys.argv[1]
    
    if not os.path.exists(transcript_path):
        print(f"File not found: {transcript_path}")
        sys.exit(1)
        
    curator = ViralCurator()
    clips = curator.analyze_transcript(transcript_path)
    
    # Save results
    output_path = transcript_path.replace("transcript_words.json", "viral_candidates.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([c.to_dict() for c in clips], f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved viral candidates to: {output_path}")
