/**
 * Every bound of the ruled appAccountToken shape (asn.ts's UUID, after lowercasing), as rows that are functions of
 * one valid lower-case token: both ends of its length (35 and 37 characters, at either end), each hyphen moved or
 * replaced, one character past each end of 0-9, a-f and A-F, trailing whitespace, and the types that are not a
 * string. POST /attest (attestVerify) and POST /attest/assert (attestAssert) each run the whole list as defects
 * (T-0322 pre-review M3: a 37-character token was admitted on both routes and no row sent one).
 */
const at = (token: string, i: number, c: string) => `${token.slice(0, i)}${c}${token.slice(i + 1)}`;

export function malformedTokens(token: string): [string, unknown][] {
  const last = token.length - 1;
  return [
    ["appAccountToken of 35 characters: the last dropped", token.slice(0, last)],
    ["appAccountToken of 35 characters: the first dropped", token.slice(1)],
    ["appAccountToken of 37 characters: a hex digit appended", `${token}0`],
    ["appAccountToken of 37 characters: a hex digit prepended", `0${token}`],
    ["appAccountToken of 72 characters: itself twice", `${token}${token}`],
    ["appAccountToken with its first hyphen moved one place right", `${token.slice(0, 8)}${token[9]}-${token.slice(10)}`],
    ["appAccountToken with a hex digit where the first hyphen is", at(token, 8, "0")],
    ["appAccountToken with a hex digit where the last hyphen is", at(token, 23, "0")],
    ["appAccountToken with a hyphen where the first digit is", at(token, 0, "-")],
    ["appAccountToken with '/' (one before 0)", at(token, last, "/")],
    ["appAccountToken with ':' (one past 9)", at(token, last, ":")],
    ["appAccountToken with '`' (one before a)", at(token, last, "`")],
    ["appAccountToken with 'g' (one past f)", at(token, last, "g")],
    ["appAccountToken with '@' (one before A)", at(token, last, "@")],
    ["appAccountToken with 'G' (one past F)", at(token, last, "G")],
    ["appAccountToken with a space appended", `${token} `],
    ["appAccountToken with a newline appended", `${token}\n`],
    ["appAccountToken empty", ""],
    ["appAccountToken a number", 7],
    ["appAccountToken an object", {}],
  ];
}

/** Admitted at every class bound (0, 9, a, f, A, F): the act is the lower-case token. */
export const ADMITTED_TOKENS: [string, string][] = [
  ["0-9 and a-f at both bounds", "09af09af-09af-49af-89af-09af09af09af"],
  ["0-9 and A-F at both bounds, lowercased", "09AF09AF-09AF-49AF-89AF-09AF09AF09AF"],
];
