# Commander Deckbuilding Template: The "New Era" Standard

This template is based on research and recommendations from *The Command Zone* (Episode 658) for modern, consistent Commander play. Use these counts as a starting point for all new deck builds and major overhauls.

## 📊 The Core Ratios (100 Cards Total)

| Category | Recommended Count | Description |
| :--- | :---: | :--- |
| **Lands** | **38** | Ensures you hit land drops through turn 4-5 consistently. |
| **Ramp** | **10** | Mana rocks, dorks, or land-search spells (e.g., Sol Ring, Arcane Signet). |
| **Card Advantage** | **12** | Mix of "Burst" (one-time draw) and "Engine" (repeatable) draw. |
| **Targeted Disruption** | **12** | Instant-speed removal for various permanent types. |
| **Mass Disruption** | **6** | Board wipes or asymmetrical resets. |
| **Plan Cards** | **31** | The core synergy, win-cons, and flavor of the specific deck. |
| **Commander** | **1** | The leader of the deck. |

## 🛠️ Implementation Notes

*   **GFM Formatting:** When listing the "Plain Text Copy/Paste" section, ensure every card line ends with **two spaces** to force correct line breaks on GitHub.
*   **Flexibility:** These numbers are guidelines. A deck with a very low average CMC might shave a land for a plan card, or a dedicated ramp deck might increase the ramp count.
*   **Bracket Compliance:** Always cross-reference the inclusion of "Game Changers" with the target power level bracket in `COMMANDER_DECKBUILDING_RULES.md`.

## 🧪 Goldfish Validation Protocol (The "Honest Trial")

After completing a new build or a major overhaul, perform a **5-game "Honest Goldfish" simulation** to verify the deck's performance and mana stability.

### 🃏 The "Honest" Rules:
1.  **Strict Mana Tracking:** Lands enter tapped/untapped according to their rules. Life must be paid for shock-lands if they are needed untapped.
2.  **No Foresight:** Do not look at future cards. Draw one card per turn (plus any additional draws from spells/abilities).
3.  **Real-Time Shuffling:** If a card causes a search (e.g., *Evolving Wilds*, *Demonic Tutor*), the remaining deck MUST be re-shuffled immediately.
4.  **Turn-by-Turn Analysis:**
    *   **Recap:** List actions, spells cast, and mana spent. **MANDATORY:** Include Scryfall links or Markdown image renders for every card drawn or played so the user can visually inspect them.
    *   **Board Status:** Briefly state the current board state.
    *   **Turn Comment:** Provide real-time strategic thoughts on the game flow, any "mana-screw" or "flood," and the perceived efficiency of the current hand.
5.  **Logging:** Save the results to a `GOLDFISH_LOG.md` file within the deck's directory.

### 📊 Validation Goals:
*   **Mana Stability:** Can the deck hit its colors and curve out by Turn 4-5?
*   **Synergy Check:** Does the "Plan" section actually resolve and create an engine?
*   **Draw Consistency:** Does the "Anti-Stall" package keep the hand full during mid-game?

## 🔗 References

*   [The Command Zone #658: Commander Deckbuilding Template for the New Era](https://www.youtube.com/watch?v=OSNV6224cHg)
