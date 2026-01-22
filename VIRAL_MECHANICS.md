# Viral Mechanics Implementation

## Overview

This document explains the viral optimization system implemented in the Clips Generator based on scientific research on short-form video virality (TikTok, Reels, YouTube Shorts).

## Research Foundation

The implementation is based on comprehensive studies analyzing:
- **50+ viral videos** with 1M+ views
- **Psychological triggers** from behavioral research
- **Algorithm mechanics** (TikTok, Reels)
- **Jonah Berger's STEPPS Framework**
- **Real performance benchmarks** from social platforms

---

## Key Metrics & Benchmarks

### 1. The First 3 Seconds (Critical)
- **72% of swipes** happen in first 3 seconds
- **Target:** >70% intro retention rate
- **Reject if:** >30% swipe away in first 3s

### 2. Watch-Through Rate
- **Strong:** 76% completion (50-60s videos)
- **Acceptable:** 42% completion (shorter videos)
- **Videos with open loops:** 76% vs 42% without

### 3. Engagement Boost
- **Humor:** +30% shares vs serious content
- **High-energy emotions:** +20% shares
- **Relatable content:** +22% engagement
- **Videos 40s+:** +33% engagement vs short clips

---

## The 4 Hook Types (First 3 Seconds)

### 1. Question Hook (Curiosity Gap)
Creates an information void the brain needs to fill.

**Example:** "Do you know why 90% of people fail at X?"

**Effectiveness:** Opens a loop that must be closed

### 2. Pattern Interrupt
Breaks autopilot scrolling with unexpected elements.

**Example:** Physical action that doesn't make sense at first

**Effectiveness:** +40% initial retention boost

### 3. Proof-First Hook
Leads with results/credentials before explanation.

**Example:** "I made $100k in 30 days..."

**Effectiveness:** Establishes immediate authority

### 4. Combo Hook (Most Powerful)
Combines two incongruent concepts.

**Example:** "I use this FBI technique to pick avocados"

**Effectiveness:** Simultaneous curiosity + emotional response

---

## The 8 Psychological Triggers

The AI analyzes for these neural activation patterns:

1. **Emotional Activation** - 72% of shares are emotion-driven
2. **High-Energy Emotions** (Awe, Excitement, Anger) - +20% shares
3. **Humor** - +30% shares
4. **Relatability** - "I feel this but never expressed it"
5. **Awe/Admiration** - 25% of viral content
6. **Laughter** - 17% of viral content
7. **Entertainment** - 15% of viral content
8. **Social Currency** - Makes sharer look good

**Requirement:** Each clip must trigger AT LEAST 2 of these

---

## Open Loop Architecture

### What is an Open Loop?
An unanswered question or incomplete thought that creates curiosity.

**Structure:**
```
Hook (0-3s) → Open Loop (4-15s) → Journey (16-45s) → Resolution (46-60s)
```

### Techniques:
- Raise question early, answer at end
- "I'll tell you something surprising at the end"
- Show result first, explain "how" later
- Incomplete story arc forcing continued watch

### Impact:
- **With open loop:** 76% watch-through
- **Without open loop:** 42% watch-through

---

## STEPPS Framework (Shareability)

Based on Jonah Berger's research, viral content hits 2+ of:

1. **Social Currency** - Makes sharer look smart/funny/informed
2. **Triggers** - Associated with everyday moments
3. **Emotion** - High-energy emotional activation
4. **Public** - Observable/visible behavior
5. **Practical Value** - Genuinely useful information
6. **Stories** - Clear narrative arc

**Finding:** 100% of analyzed viral videos hit at least 2 STEPPS

---

## Optimal Duration

### Data-Driven Sweet Spots:

| Duration | Watch-Through Rate | Use Case |
|----------|-------------------|----------|
| 15-30s | 42% | Beginners, simple hooks |
| 40-50s | +33% engagement | Experienced creators |
| **50-60s** | **76%** | **IDEAL** (dense structure) |
| 60-90s | Requires mastery | Expert storytellers only |

**Recommendation:** Prioritize 50-60s clips

---
  python run_viral.py "https://www.youtube.com/watch?v=tE_4ntnqYMU"
## Pacing Requirements

### Visual Density
- **Target:** 1 cut/change every 2-4 seconds
- **Finding:** 72% of +1M view videos follow fast pacing
- **Goal:** Eliminate "dead air" (>5s of nothing)

### Content Density
- Minimum 1 interesting "moment" every 10 seconds
- No long setup/context building
- Immediate value delivery

---

## AI Analysis Process

### Phase 1: Hook Validation
- Analyzes first 3 seconds for explosive start
- Identifies hook type (Question/Pattern/Proof/Combo)
- Rejects clips with weak/generic openings

### Phase 2: Psychological Profiling
- Maps to 8 psychological triggers
- Requires minimum 2 trigger activations
- Evaluates emotional energy level

### Phase 3: Structure Analysis
- Validates open loop presence
- Checks pacing (cuts, moments, density)
- Ensures satisfying payoff/resolution

### Phase 4: STEPPS Scoring
- Maps to Jonah Berger's framework
- Validates 2+ STEPPS elements
- Predicts share probability

### Phase 5: Metrics Prediction
- **Viral Score** (0-10)
- **Estimated Retention %**
- **Share Probability** (Low/Medium/High)

---

## Enhanced Output Data

Each selected clip now includes:

```json
{
  "start_time": 10.5,
  "end_time": 65.2,
  "title": "Short catchy title",
  "viral_score": 9.2,
  "hook_type": "Pattern Interrupt",
  "psychological_triggers": ["Humor", "Relatability", "Social Currency"],
  "stepps_score": ["Social Currency", "Emotion", "Practical Value"],
  "open_loop": "Promises to reveal secret technique at end",
  "reasoning": "Detailed analysis...",
  "category": "Contrarian Truth",
  "estimated_retention": 78,
  "share_probability": "High"
}
```

---

## Quality Standards

### Clips are REJECTED if:
- ❌ Weak hook in first 3s
- ❌ >5s of dead air
- ❌ Requires external context
- ❌ No clear payoff/conclusion
- ❌ <20s or >90s duration
- ❌ Triggers <2 psychological elements
- ❌ Hits <2 STEPPS factors

### Clips are ACCEPTED if:
- ✅ Viral Score ≥9/10
- ✅ Explosive hook (one of 4 types)
- ✅ 2+ psychological triggers
- ✅ 2+ STEPPS elements
- ✅ Clear open loop structure
- ✅ 50-60s duration (ideal)
- ✅ Fast pacing (cut every 2-4s)
- ✅ Satisfying resolution

---

## Usage Example

```bash
python run_viral.py "https://youtube.com/watch?v=..." --limit 3
```

The AI will:
1. Transcribe the full video
2. Analyze against viral mechanics
3. Return only clips with VPS ≥9/10
4. Include detailed viral metrics
5. Generate optimized shorts

---

## Performance Expectations

### Before Optimization:
- Generic clip selection
- No hook analysis
- No retention prediction
- Basic duration constraints

### After Optimization:
- **Hook-first** selection (4 proven types)
- **8-trigger** psychological profiling
- **STEPPS framework** validation
- **Retention prediction** (estimated %)
- **Share probability** scoring
- **Quality > Quantity** (only VPS ≥9)

---

## References

This implementation is based on research from:
- Shortimize (retention analytics)
- OpusClip (viral mechanics studies)
- Swydo (benchmark data)
- Journal of Consumer Psychology (2024)
- NYU/Buffer/Hootsuite (social media studies)
- Jonah Berger's "Contagious" (STEPPS framework)

---

## Future Enhancements

Potential improvements:
- [ ] A/B testing different hook types
- [ ] Real-time retention feedback loop
- [ ] Category-specific optimization
- [ ] Multi-language viral pattern analysis
- [ ] Automated thumbnail suggestion
- [ ] Music/sound effect recommendations

---

**Last Updated:** 2026-01-21
**Status:** Production Ready ✅
