/**
 * Unit tests for Math Term Normalization (frontend/src/lib/mathNormalizer.ts).
 */

import { describe, it, expect } from "vitest";
import { normalizeMathTerms } from "../mathNormalizer";

describe("normalizeMathTerms", () => {
  it("normalizes named fractions", () => {
    expect(normalizeMathTerms("setengah")).toBe("1/2");
    expect(normalizeMathTerms("sepertiga")).toBe("1/3");
    expect(normalizeMathTerms("seperempat")).toBe("1/4");
  });

  it("normalizes spoken fractions", () => {
    expect(normalizeMathTerms("satu per dua")).toBe("1/2");
    expect(normalizeMathTerms("tiga per empat")).toBe("3/4");
    expect(normalizeMathTerms("tujuh per delapan")).toBe("7/8");
  });

  it("normalizes exponents", () => {
    expect(normalizeMathTerms("x kuadrat")).toBe("x²");
    expect(normalizeMathTerms("dua kuadrat")).toBe("2²");
    expect(normalizeMathTerms("a kubik")).toBe("a³");
    expect(normalizeMathTerms("x pangkat dua")).toBe("x²");
    expect(normalizeMathTerms("dua pangkat tiga")).toBe("2³");
    expect(normalizeMathTerms("x pangkat n")).toBe("xⁿ");
  });

  it("normalizes roots", () => {
    expect(normalizeMathTerms("akar dua")).toBe("√2");
    expect(normalizeMathTerms("akar dari sembilan")).toBe("√9");
    expect(normalizeMathTerms("akar kuadrat dari enam belas")).toBe("√16");
    expect(normalizeMathTerms("akar pangkat tiga dari delapan")).toBe("∛8");
  });

  it("normalizes arithmetic equations", () => {
    expect(normalizeMathTerms("dua ditambah tiga")).toBe("2 + 3");
    expect(normalizeMathTerms("sepuluh dibagi dua")).toBe("10 ÷ 2");
    expect(normalizeMathTerms("dua x ditambah tiga sama dengan tujuh")).toBe("2x + 3 = 7");
    expect(normalizeMathTerms("x kuadrat dikurangi empat x ditambah empat sama dengan nol")).toBe("x² - 4x + 4 = 0");
  });

  it("normalizes constants and parentheses", () => {
    expect(normalizeMathTerms("buka kurung x ditambah satu tutup kurung")).toBe("(x + 1)");
    expect(normalizeMathTerms("dua phi r")).toBe("2πr");
    expect(normalizeMathTerms("sembilan puluh derajat")).toBe("90°");
    expect(normalizeMathTerms("seratus persen")).toBe("100%");
  });

  it("handles empty and edge cases", () => {
    expect(normalizeMathTerms("")).toBe("");
    expect(normalizeMathTerms("   ")).toBe("   ");
  });
});
