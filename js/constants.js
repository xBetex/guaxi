// ============================================================
// js/constants.js — Immutable data: themes, colors, sprites
// ============================================================

const THEMES = {
  manha: { sky1: "#74b9ff", sky2: "#81ecec", sky3: "#ffeaa7", mountain: "#827397", mountainLight: "#a29bfe" },
  dia:   { sky1: "#0984e3", sky2: "#74b9ff", sky3: "#81ecec", mountain: "#4a5b63", mountainLight: "#636e72" },
  tarde: { sky1: "#6c5ce7", sky2: "#e84393", sky3: "#fdcb6e", mountain: "#1b1b2f", mountainLight: "#2d3436" },
  noite: { sky1: "#000000", sky2: "#1e272e", sky3: "#0f1423", mountain: "#0a0a0f", mountainLight: "#1e272e" },
};

const SEASON_COLORS = {
  spring: { grass1: "#55efc4", grass2: "#00b894", leafM: "#fd79a8", leafN: "#e84393", leafE: "#d63031" },
  summer: { grass1: "#78e08f", grass2: "#38ada9", leafM: "#2ecc71", leafN: "#27ae60", leafE: "#1e8449" },
  autumn: { grass1: "#e58e26", grass2: "#b71540", leafM: "#f39c12", leafN: "#d35400", leafE: "#e67e22" },
  winter: { grass1: "#dfe6e9", grass2: "#b2bec3", leafM: "#ecf0f1", leafN: "#bdc3c7", leafE: "#95a5a6" },
};

const BASE_COLORS = {
  T: null,
  K: "#1e272e", B: "#834c32", D: "#5c3a21",
  S: "#f1c40f", O: "#e67e22", C: "#f5f6fa",
  Y: "#ffffff", V: "#dcdde1", I: "#7f8fa6",
  G: "#a5b1c2", A: "#485460", R: "#ff9ff3",
  P: "#f368e0", F: "#e74c3c",
};

function getColor(char, season) {
  if (BASE_COLORS[char] !== undefined) return BASE_COLORS[char];
  const sc = SEASON_COLORS[season];
  if (char === "M") return sc.leafM;
  if (char === "N") return sc.leafN;
  if (char === "E") return sc.leafE;
  return "#000";
}

// ─── Sprite definitions ───────────────────────────────────────
const TREE = [
  "TTTTTTTTTTKKKKKKTTTTTTTTTT",
  "TTTTTTTKKKMMMMMMKKKTTTTTTT",
  "TTTTTKKMMMMMMMMMMMMKKTTTTT",
  "TTTTKMMMMMMNNNNMMMMMMKTTTT",
  "TTTKMMMMMNNNNNNNNMMMMMKTTT",
  "TTKMMMMMNNNNNNNNNNMMMMMKTT",
  "TKMMMMMNNNNNNNNNNNNMMMMKTT",
  "TKMMMMNNNNNNNNNNNNNNMMMMKT",
  "KMMMMNNNNNNNNNNNNNNNNMMMMK",
  "KMMMNNNNNNNEEEENNNNNNNMMMK",
  "KMMMNNNNNNEEEEEEENNNNNMMMK",
  "KMMNNNNNNNEEEEEEEENNNNNMMK",
  "TKNNNNNNNNEEEEEEEENNNNNNKT",
  "TKNNNNNNNNEEEEEEEENNNNNNKT",
  "TTKNNNNNNNEEEEEEEENNNNNKTT",
  "TTTKKNNNNNEEEEEEENNNNKKTTT",
  "TTTTTKKNNNEEEEEENNNKKTTTTT",
  "TTTTTTTKKNEEEEEENKKTTTTTTT",
  "TTTTTTTTTKKEEEEKKTTTTTTTTT",
  "TTTTTTTTTTTKBBKTTTTTTTTTTT",
  "TTTTTTTTTTTKBDBKTTTTTTTTTT",
  "TTTTTTTTTTTKBDBKTTTTTTTTTT",
  "TTTTTTTTTTTKKKKKTTTTTTTTTT",
  "TTTTTTTTTTTKKKKKTTTTTTTTTT",
  "TTTTTTTTTTKKKKKKKTTTTTTTTT",
  "TTTTTTTTTKKKKKKKKKTTTTTTTT",
  "TTTTTTTTTKKKKKKKKKTTTTTTTT",
];

const BONFIRE_1 = [
  "TTTTTFTTTTT", "TTTTFOFTTTT", "TTTOOOFTTTT",
  "TTFOOSOFTTT", "TFOOSSOOFTT", "TFOOSSSOFTT",
  "FOOSSSSSOFT", "KDKKBBKKDKT", "TKDBKKBDKTT", "TTKKKKKTTTT",
];
const BONFIRE_2 = [
  "TTTTTTFTTTT", "TTTTTFOFTTT", "TTTTOOFTTTT",
  "TTTOOSOFTTT", "TTFOOSOOFTT", "TFOOSSSOFTT",
  "FOOSSSSSOFT", "KDKKBBKKDKT", "TKDBKKBDKTT", "TTKKKKKTTTT",
];

const BUSH = [
  "TTTTTTMMMMMNTTTTTT",
  "TTTTMMMMMMNNNNTTTT",
  "TTTMMMMMMNNNNNETTT",
  "TTMMMMMMMNNNNNEETT",
  "TMMMMMMNNNNNEEEEET",
  "MMMMMNNNNNEEEEEEEE",
  "MMMMNNNNNNEEEEEEEE",
];

const FLOWER = ["TRT", "RPR", "TRT", "TNT", "MNN"];
const ROCK   = ["TTGGTT", "TGGGGT", "GDDGGA", "DAAADA"];

const CLOUD = [
  "TTTTTTTTYYYYTTTTTTTT",
  "TTTTTTYYYYYYYYTTTTTT",
  "TTTTYYYYYYYYYYYYTTTT",
  "TTYYYYYYYYYYYYYYYYTT",
  "YYYYYYYYYYYYYYYYYYYY",
  "YYYYYYYYYYYYYYYYYYYY",
  "TYYYYYYYYYYYYYYYYYYT",
];
