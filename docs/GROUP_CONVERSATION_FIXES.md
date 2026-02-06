# Latest Fixes - Group Conversation Support

## Date: 2026-02-04 17:20

## Changes Implemented

### 1. ✅ Emoji Removal (Complete)
**Files Modified**:
- `app/main.py` - Added "Never use emojis" to Gemini prompt
- `app/services/script_normalizer.py` - Added comprehensive emoji filter

**Details**:
- Primary prevention: Instructed Gemini to never generate emojis
- Backup filter: Unicode-based emoji regex that strips ALL emoji types:
  - Emoticons (😊, 😂, etc.)
  - Symbols & pictographs (🎉, 🔥, etc.)
  - Transport symbols (🚗, ✈️, etc.)
  - Flags, dingbats, and more

**Result**: AI responses will be completely emoji-free in all languages

---

### 2. ✅ Single-Speaker Mode for Group Conversations
**File Modified**: `app/services/vad_service.py`

**Problem**: 
When 4 people are around one phone, multiple voices could trigger VAD simultaneously, causing confusion and cross-talk.

**Solution - "Speaker Lock" System**:

#### How It Works:
1. **Lock Acquisition**: 
   - When someone starts speaking (voice detected for 120ms)
   - System acquires a "speaker lock" for **3 seconds**
   - Console shows: `🔒 SPEAKER LOCK ACQUIRED (expires in 3.0s)`

2. **Lock Protection**:
   - During the 3-second lock period
   - Other voices are **completely ignored**
   - New speech detection returns `False` immediately
   - Only the current speaker's voice is processed

3. **Lock Release**:
   - **Automatic**: When the speaker finishes (1 second of silence)
   - Console shows: `🔓 SPEAKER LOCK RELEASED (turn complete)`
   - **Timeout**: Automatically releases after 3 seconds
   - Next person can now speak

#### Example Scenario (4 people):
```
Time  | Action                          | System Response
------|----------------------------------|------------------
0.0s  | Person A starts speaking        | 🔒 LOCK ACQUIRED
0.5s  | Person B tries to speak         | ❌ Ignored (locked)
1.2s  | Person C tries to speak         | ❌ Ignored (locked)
2.0s  | Person A finishes speaking      | 🔓 LOCK RELEASED
2.1s  | Person D starts speaking        | 🔒 LOCK ACQUIRED (new turn)
```

#### Benefits:
- ✅ Clean turn-taking in groups
- ✅ No voice conflicts or mixed inputs
- ✅ Natural conversation flow (like passing a microphone)
- ✅ Automatic timeout prevents permanent lock if someone pauses mid-thought

#### Technical Details:
- Lock duration: **3 seconds** (configurable via `SPEAKER_LOCK_DURATION`)
- Lock scope: Global (applies to ALL incoming audio)
- Lock bypass: Current speaker can continue (checked via `speech_session_active`)
- Lock reset: On commit or timeout (whichever comes first)

---

## Files Modified Summary

1. **app/main.py** 
   - Added "Never use emojis" instruction

2. **app/services/script_normalizer.py**
   - Comprehensive emoji Unicode filtering

3. **app/services/vad_service.py**
   - Added speaker lock variables (`speaker_lock_until`, `SPEAKER_LOCK_DURATION`)
   - Modified `is_speech()` to check and enforce speaker lock
   - Modified `check_commit()` to release speaker lock
   - Added debug logging for lock acquire/release

---

## Testing Instructions

### Test 1: Emoji Removal
1. Ask: "Tell me something fun" (in any language)
2. Check response: Should have NO emojis (no 😊, 🎉, etc.)

### Test 2: Single Speaker Mode (Solo)
1. Start speaking
2. Check console: Should see `🔒 SPEAKER LOCK ACQUIRED`
3. Finish speaking (1s silence)
4. Check console: Should see `🔓 SPEAKER LOCK RELEASED`

### Test 3: Single Speaker Mode (Group - Simulated)
1. Person A starts speaking
2. While A is still in their turn (within 3s), person B tries to speak
3. Person B's voice should be ignored
4. After A finishes (commit), person B can speak successfully

**Note**: The 3-second lock duration strikes a balance:
- Long enough to prevent interruptions during a sentence
- Short enough to allow quick turn-taking
- Auto-expires to prevent deadlock

---

## Logging Reference

When using the system in a group, you'll see:
```
🔒 SPEAKER LOCK ACQUIRED (expires in 3.0s)    ← Someone started speaking
🏁 SPEECH END (Commit)                        ← They finished
🔓 SPEAKER LOCK RELEASED (turn complete)       ← Lock released, next person can speak
```

If someone tries to speak while locked:
- No log entry (silently ignored)
- Returns `False` from `is_speech()` immediately

---

## Configuration Options

If you want to adjust the speaker lock duration:
- Edit `app/services/vad_service.py`
- Line 32: `self.SPEAKER_LOCK_DURATION = 3.0`
- Change to desired seconds (e.g., 2.0 for faster turns, 5.0 for longer thinking pauses)
