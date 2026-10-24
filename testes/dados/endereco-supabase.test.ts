/** Endereço do Supabase: o da Data API (com /rest/v1/) vira o do projeto, que é o que o Auth espera. */
import { describe, expect, it } from "vitest";
import { enderecoDoSupabase } from "../../src/auth/supabase.ts";

describe("endereço do Supabase", () => {
  it("descarta o caminho da Data API e a barra final", () => {
    expect(enderecoDoSupabase("https://exemplo.supabase.co/rest/v1/")).toBe("https://exemplo.supabase.co");
    expect(enderecoDoSupabase("https://exemplo.supabase.co/")).toBe("https://exemplo.supabase.co");
    expect(enderecoDoSupabase("http://127.0.0.1:54321")).toBe("http://127.0.0.1:54321");
  });

  it("recusa o que não é endereço", () => {
    expect(() => enderecoDoSupabase("exemplo.supabase.co")).toThrow(/não é um endereço válido/);
  });
});
