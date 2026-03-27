/**
 * Game constants — labels, icons, and UI mappings.
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

const ACTION_CONFIG = {
    move:      { label: "Siirrä yksikköä",     icon: "🚶", style: "btn-secondary" },
    attack:    { label: "Hyökkää",              icon: "⚔️", style: "btn-danger" },
    diplomacy: { label: "Diplomatia",           icon: "🤝", style: "btn-secondary" },
    collect:   { label: "Kerää resursseja",     icon: "💰", style: "btn-success" },
    heal:      { label: "Paranna yksikköä",     icon: "💚", style: "btn-secondary" },
    recruit:   { label: "Värvää yksikkö",       icon: "➕", style: "btn-secondary" },
    end_phase: { label: "Lopeta vaihe",         icon: "⏭️", style: "btn-ghost" },
};
