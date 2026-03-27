/**
 * Game constants — labels, icons, UI mappings, and phase data.
 */
const UNIT_ICONS = {
    warrior: "⚔️",
    cavalry: "🐎",
    archer:  "🏹",
    chief:   "👑",
};

const UNIT_LABELS = {
    warrior: "Soturi",
    cavalry: "Ratsuväki",
    archer:  "Jousiampuja",
    chief:   "Päällikkö",
};

const PHASE_ICONS = {
    movement:  "🚶",
    combat:    "⚔️",
    diplomacy: "🤝",
    resource:  "💰",
};

const PHASE_ORDER = ["movement", "combat", "diplomacy", "resource"];

const PHASE_LABELS = {
    movement:  "Liike",
    combat:    "Taistelu",
    diplomacy: "Diplomatia",
    resource:  "Resurssit",
};

const ACTION_CONFIG = {
    move:      { label: "Siirrä yksikköä",     icon: "🚶", style: "btn-secondary", hint: "Valitse yksikkö, sitten kohderuutu" },
    attack:    { label: "Hyökkää",              icon: "⚔️", style: "btn-danger",    hint: "Valitse yksikkö, sitten vihollinen" },
    diplomacy: { label: "Diplomatia",           icon: "🤝", style: "btn-secondary", hint: "Paranna suhteita vihollisheimoon" },
    collect:   { label: "Kerää resursseja",     icon: "💰", style: "btn-success",   hint: "Kerää tuloja yksiköidesi perusteella" },
    heal:      { label: "Paranna yksikköä",     icon: "💚", style: "btn-secondary", hint: "Valitse oma yksikkö parannettavaksi" },
    recruit:   { label: "Värvää yksikkö",       icon: "➕", style: "btn-secondary", hint: "Sijoita uusi yksikkö tyhjään ruutuun" },
    end_phase: { label: "Lopeta vaihe",         icon: "⏭️", style: "btn-ghost",     hint: "Siirry seuraavaan vaiheeseen" },
};

const EVENT_ICONS = {
    game_start: "🎮",
    move:       "🚶",
    combat:     "⚔️",
    diplomacy:  "🤝",
    resource:   "💰",
    heal:       "💚",
    recruit:    "➕",
    victory:    "🏆",
    defeat:     "💀",
};
