/**
 * Math Term Normalization Layer (Client-Side).
 *
 * Normalizes spoken Indonesian mathematical terms into standard symbols
 * before sending to Tutor AI or displaying in the transcript input.
 *
 * Examples:
 *   "satu per dua" -> "1/2"
 *   "setengah" -> "1/2"
 *   "x kuadrat" -> "x²"
 *   "dua pangkat tiga" -> "2³"
 *   "akar dua" -> "√2"
 *   "dua x ditambah tiga sama dengan tujuh" -> "2x + 3 = 7"
 */

const NUMBER_WORDS: Record<string, number> = {
  nol: 0,
  satu: 1,
  se: 1,
  dua: 2,
  tiga: 3,
  empat: 4,
  lima: 5,
  enam: 6,
  tujuh: 7,
  delapan: 8,
  sembilan: 9,
  sepuluh: 10,
  sebelas: 11,
  "dua belas": 12,
  "tiga belas": 13,
  "empat belas": 14,
  "lima belas": 15,
  "enam belas": 16,
  "tujuh belas": 17,
  "delapan belas": 18,
  "sembilan belas": 19,
  "dua puluh": 20,
  "tiga puluh": 30,
  "empat puluh": 40,
  "lima puluh": 50,
  "enam puluh": 60,
  "tujuh puluh": 70,
  "delapan puluh": 80,
  "sembilan puluh": 90,
  seratus: 100,
};

const SUPERSCRIPTS: Record<string, string> = {
  "0": "⁰",
  "1": "¹",
  "2": "²",
  "3": "³",
  "4": "⁴",
  "5": "⁵",
  "6": "⁶",
  "7": "⁷",
  "8": "⁸",
  "9": "⁹",
  n: "ⁿ",
  x: "ˣ",
  y: "ʸ",
};

const NAMED_FRACTIONS: Record<string, string> = {
  setengah: "1/2",
  seperdua: "1/2",
  sepertiga: "1/3",
  seperempat: "1/4",
  seperlima: "1/5",
  seperenam: "1/6",
  seperdelapan: "1/8",
  sepersepuluh: "1/10",
};

function parseNumberWord(word: string): string {
  const cleaned = word.trim().toLowerCase();
  if (/^\d+$/.test(cleaned)) return cleaned;

  if (cleaned in NUMBER_WORDS) {
    return String(NUMBER_WORDS[cleaned]);
  }

  const parts = cleaned.split(/\s+/);
  if (parts.length === 3 && parts[1] === "puluh") {
    const tens = NUMBER_WORDS[`${parts[0]} puluh`] ?? 0;
    const units = NUMBER_WORDS[parts[2]] ?? 0;
    if (tens && units) return String(tens + units);
  }

  return word;
}

const NUM_PATTERN =
  "(?:(?:dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)\\s+puluh\\s+(?:satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)|" +
  "(?:dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)\\s+belas|" +
  "(?:dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)\\s+puluh|" +
  "sebelas|sepuluh|seratus|" +
  "nol|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|\\d+)";

export function normalizeMathTerms(text: string): string {
  if (!text || !text.trim()) return text;

  let out = text;

  // 1. Parentheses
  out = out.replace(/\bbuka\s+kurung\s+(.*?)\s+tutup\s+kurung\b/gi, "($1)");
  out = out.replace(/\bbuka\s+kurung\s+siku\s+(.*?)\s+tutup\s+kurung\s+siku\b/gi, "[$1]");
  out = out.replace(/\bbuka\s+kurung\s+kurawal\s+(.*?)\s+tutup\s+kurung\s+kurawal\b/gi, "{$1}");

  // 2. Named Fractions
  for (const [name, frac] of Object.entries(NAMED_FRACTIONS)) {
    out = out.replace(new RegExp(`\\b${name}\\b`, "gi"), frac);
  }

  // 3. Explicit fractions: pecahan dengan pembilang A dan penyebut B
  out = out.replace(
    /\bpecahan\s+(?:dengan\s+)?pembilang\s+([a-zA-Z0-9\s]+?)\s+dan\s+penyebut\s+([a-zA-Z0-9\s]+?)(?=\s|$|,|\.)/gi,
    (_, num, denom) => `${parseNumberWord(num)}/${parseNumberWord(denom)}`
  );

  // 4. Fractions: A per B
  const fracRegex = new RegExp(`\\b(${NUM_PATTERN}|[a-zA-Z])\\s+per\\s+(${NUM_PATTERN}|[a-zA-Z])\\b`, "gi");
  out = out.replace(fracRegex, (_, n, d) => `${parseNumberWord(n)}/${parseNumberWord(d)}`);

  // 5. Roots: akar pangkat tiga / akar kuadrat / akar
  out = out.replace(
    new RegExp(`\\bakar\\s+pangkat\\s+(?:tiga|3)\\s+dari\\s+(${NUM_PATTERN}|[a-zA-Z]+|\\([^)]+\\))\\b`, "gi"),
    (_, val) => `∛${parseNumberWord(val)}`
  );
  out = out.replace(
    new RegExp(`\\bakar\\s+(?:kuadrat\\s+)?(?:dari\\s+)?(${NUM_PATTERN}|[a-zA-Z]+|\\([^)]+\\))\\b`, "gi"),
    (_, val) => `√${parseNumberWord(val)}`
  );

  // 6. Exponents
  out = out.replace(
    new RegExp(`\\b(${NUM_PATTERN}|[a-zA-Z0-9)]+)\\s+kuadrat\\b`, "gi"),
    (_, base) => `${parseNumberWord(base)}²`
  );
  out = out.replace(
    new RegExp(`\\b(${NUM_PATTERN}|[a-zA-Z0-9)]+)\\s+kubik\\b`, "gi"),
    (_, base) => `${parseNumberWord(base)}³`
  );
  out = out.replace(
    new RegExp(`\\b(${NUM_PATTERN}|[a-zA-Z0-9)]+)\\s+pangkat\\s+(${NUM_PATTERN}|[a-zA-Z])\\b`, "gi"),
    (_, base, exp) => {
      const b = parseNumberWord(base);
      const e = parseNumberWord(exp).toLowerCase();
      if (e === "2") return `${b}²`;
      if (e === "3") return `${b}³`;
      if (e in SUPERSCRIPTS) return `${b}${SUPERSCRIPTS[e]}`;
      return `${b}^${e}`;
    }
  );

  // 7. Comparisons
  const comparisons: [RegExp, string][] = [
    [/\bkurang\s+dari\s+atau\s+sama\s+dengan\b/gi, "≤"],
    [/\blebih\s+kecil\s+(?:dari\s+)?atau\s+sama\s+dengan\b/gi, "≤"],
    [/\blebih\s+dari\s+atau\s+sama\s+dengan\b/gi, "≥"],
    [/\blebih\s+besar\s+(?:dari\s+)?atau\s+sama\s+dengan\b/gi, "≥"],
    [/\btidak\s+sama\s+dengan\b/gi, "≠"],
    [/\bkira-?kira\s+sama\s+dengan\b/gi, "≈"],
    [/\bhampir\s+sama\s+dengan\b/gi, "≈"],
    [/\bkurang\s+lebih\b/gi, "±"],
    [/\bplus\s+minus\b/gi, "±"],
    [/\bsama\s+dengan\b/gi, "="],
    [/\bkurang\s+dari\b/gi, "<"],
    [/\blebih\s+kecil\s+dari\b/gi, "<"],
    [/\blebih\s+dari\b/gi, ">"],
    [/\blebih\s+besar\s+dari\b/gi, ">"],
  ];
  for (const [pattern, sym] of comparisons) {
    out = out.replace(pattern, ` ${sym} `);
  }

  // 8. Constants
  out = out.replace(/\b(?:phi|pi)\b/gi, "π");
  out = out.replace(/\bderajat\b/gi, "°");
  out = out.replace(/\bpersen\b/gi, "%");
  out = out.replace(/\btak\s+(?:hingga|terhingga)\b/gi, "∞");

  // 9. Arithmetic operators
  out = out.replace(/\b(?:ditambah|tambah|plus)\b/gi, " + ");
  out = out.replace(/\b(?:dikurangi|kurang|minus)\b/gi, " - ");
  out = out.replace(/\b(?:dikali(?:kan)?|kali)\b/gi, " × ");
  out = out.replace(/\b(?:dibagi|bagi)\b/gi, " ÷ ");

  // 10. Variable coefficients: "dua x" -> "2x", "dua π" -> "2π" (single letter variable or π only)
  out = out.replace(
    new RegExp(`\\b(${NUM_PATTERN})\\s*([a-zA-Zπ])(?![a-zA-Z])`, "gi"),
    (_, num, v) => `${parseNumberWord(num)}${v}`
  );
  out = out.replace(/π\s*([a-zA-Z])/g, "π$1");

  // 11. Standalone numbers around symbols
  out = out.replace(
    new RegExp(`([+\\-×÷=≤≥<>≈≠(])(\\s+)(${NUM_PATTERN})\\b`, "gi"),
    (_, sym, space, word) => `${sym}${space}${parseNumberWord(word)}`
  );
  out = out.replace(
    new RegExp(`\\b(${NUM_PATTERN})(\\s+)([+\\-×÷=≤≥<>≈≠)])`, "gi"),
    (_, word, space, sym) => `${parseNumberWord(word)}${space}${sym}`
  );

  // 12. Numbers before units: "90 derajat" -> "90°"
  out = out.replace(
    new RegExp(`\\b(${NUM_PATTERN})\\s*([°%])`, "gi"),
    (_, word, unit) => `${parseNumberWord(word)}${unit}`
  );

  // 13. Clean whitespace
  out = out.replace(/\s+/g, " ").trim();
  out = out.replace(/\(\s+/g, "(").replace(/\s+\)/g, ")");

  return out;
}
