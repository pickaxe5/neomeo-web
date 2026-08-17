// ISO 3166-1 alpha-2 country codes. Display names are localized at render time
// via Intl.DisplayNames so both ko/en show without maintaining a translated list here.
export const COUNTRY_CODES: string[] = [
  "KR", "US", "JP", "CN", "TW", "HK", "SG", "IN", "ID", "VN", "TH", "PH", "MY",
  "GB", "IE", "DE", "FR", "ES", "PT", "IT", "NL", "BE", "LU", "CH", "AT",
  "SE", "NO", "DK", "FI", "IS", "PL", "CZ", "SK", "HU", "RO", "BG", "GR",
  "UA", "RU", "TR", "IL", "AE", "SA", "EG",
  "ZA", "NG", "KE",
  "CA", "MX", "BR", "AR", "CL", "CO", "PE",
  "AU", "NZ",
  "KZ", "UZ", "MN",
];

export function countryLabel(code: string, lang: string): string {
  try {
    const dn = new Intl.DisplayNames([lang], { type: "region" });
    return dn.of(code) ?? code;
  } catch {
    return code;
  }
}
