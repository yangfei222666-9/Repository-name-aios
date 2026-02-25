# AIOS 30-Second Demo Script

## 🎬 Visual Flow

**Duration**: 30 seconds  
**Format**: Screen recording with voiceover  
**Style**: Fast-paced, show don't tell

---

## 📝 Script

### [0-5s] Hook
**Visual**: Terminal with AIOS logo ASCII art  
**Voiceover**: "Your AI assistant makes the same mistake twice. AIOS doesn't."

```
    _    ___ ___  ____  
   / \  |_ _/ _ \/ ___| 
  / _ \  | | | | \___ \ 
 / ___ \ | | |_| |___) |
/_/   \_\___\___/|____/ 
                        
Self-Learning AI Agent Framework
```

---

### [5-10s] Problem
**Visual**: Split screen showing error logs repeating
```
[ERROR] 502 Bad Gateway - api.example.com
[ERROR] 502 Bad Gateway - api.example.com  
[ERROR] 502 Bad Gateway - api.example.com
```
**Voiceover**: "Traditional AI: repeats errors. No memory, no learning."

---

### [10-15s] Solution - Learning
**Visual**: Terminal showing AIOS learning loop
```bash
$ aios run

[SENSOR] Network error detected: 502 @ api.example.com
[ALERT]  High priority - repeated failure (3x in 5min)
[LEARN]  Creating lesson: network_502_retry
[RULE]   Auto-retry with exponential backoff
```
**Voiceover**: "AIOS learns from every mistake. Error → Lesson → Rule."

---

### [15-20s] Solution - Self-Healing
**Visual**: Dashboard showing auto-fix in action
```
┌─ AIOS Dashboard ─────────────────────────┐
│ Evolution Score: 0.24 → 0.457 (healthy) │
│                                          │
│ [REACTOR] Matched playbook: network_retry│
│ [ACTION]  Retry with backoff (2s → 4s)  │
│ [VERIFY]  ✓ Request succeeded            │
│ [FEEDBACK] Lesson validated              │
└──────────────────────────────────────────┘
```
**Voiceover**: "Detects issues. Matches playbooks. Fixes itself. Verifies."

---

### [20-25s] Solution - Multi-Agent
**Visual**: Terminal showing agent spawn
```bash
$ aios handle-task "Analyze this codebase"

[ROUTER]  Task type: code_analysis
[SPAWN]   Creating analyst agent... (0.3s)
[SPAWN]   Creating reviewer agent... (0.3s)
[DELEGATE] Splitting task into 3 subtasks
[PROGRESS] ████████░░ 80% complete
[RESULT]  Aggregated 2 agent reports
```
**Voiceover**: "Complex tasks? Spawns specialized agents. 600x faster."

---

### [25-30s] CTA
**Visual**: GitHub repo page with star button highlighted
```
github.com/yangfei222666-9/aios

⭐ Star if you believe AI should learn, not just respond.

pip install aios-framework  # Coming soon
```
**Voiceover**: "AIOS. From chatbot to operating system. Star on GitHub."

---

## 🎨 Production Notes

### Visual Style
- **Terminal theme**: Dark background, green/yellow/red for status
- **Font**: Monospace (Fira Code or JetBrains Mono)
- **Transitions**: Fast cuts (no fade), keep energy high
- **Cursor**: Show typing animation for commands

### Audio
- **Voiceover**: Clear, confident, slightly fast-paced
- **Music**: Optional subtle tech background (low volume)
- **Sound effects**: Terminal beeps for errors/success (subtle)

### Key Frames to Capture
1. ASCII logo (0s)
2. Error logs repeating (5s)
3. Learning loop in action (10s)
4. Dashboard evolution score (15s)
5. Agent spawn terminal (20s)
6. GitHub star button (25s)

---

## 📊 Alternative: GIF Version (Silent)

For README embedding, create a 10-second looping GIF:

```
Frame 1 (2s): Error → Error → Error
Frame 2 (2s): [LEARN] Creating lesson...
Frame 3 (2s): [REACTOR] Auto-fixing...
Frame 4 (2s): [VERIFY] ✓ Fixed
Frame 5 (2s): Evolution: 0.24 → 0.457
```

**Tool**: Use `asciinema` to record terminal, convert to GIF with `agg`

```bash
asciinema rec demo.cast
agg demo.cast demo.gif
```

---

## 🎯 Distribution

**Upload to:**
- GitHub README (embedded GIF)
- Twitter/X (30s video)
- YouTube Shorts (30s video)
- Reddit r/MachineLearning (video + discussion)
- Hacker News (link in Show HN post)

**Thumbnail text:**
```
AIOS
Self-Learning AI
From Chatbot → OS
```

---

## 📝 Voiceover Script (Full Text)

> "Your AI assistant makes the same mistake twice. AIOS doesn't.
> 
> Traditional AI repeats errors. No memory, no learning.
> 
> AIOS learns from every mistake. Error becomes lesson becomes rule.
> 
> Detects issues. Matches playbooks. Fixes itself. Verifies.
> 
> Complex tasks? Spawns specialized agents. Six hundred times faster.
> 
> AIOS. From chatbot to operating system. Star on GitHub."

**Word count**: 58 words  
**Speaking pace**: ~120 words/min  
**Duration**: ~29 seconds ✓

---

## 🛠️ Recording Checklist

- [ ] Clean terminal (no personal info)
- [ ] Prepare demo data (fake API endpoints)
- [ ] Test run 3x before recording
- [ ] Record at 1920x1080 or 2560x1440
- [ ] Export at 60fps for smooth terminal text
- [ ] Add subtitles (accessibility + silent viewing)
- [ ] Compress to <5MB for Twitter

---

**Ready to record? Let me know if you need the actual demo commands or test data setup.**
