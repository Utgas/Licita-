/** Nome da variável de JSON Logic para um ID: WZ-23 -> WZ_23, CK-C-14.2 -> CK_C_14_2, VAR-001 -> VAR_001. */
export function variavelDoId(id: string): string {
  return id.replace(/[-.]/g, "_");
}
