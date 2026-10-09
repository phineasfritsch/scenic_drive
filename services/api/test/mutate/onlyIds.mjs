// The one `--only` parser every services/api/test/mutate/*Mutants.mjs driver uses (T-0347).
//
// A typo'd selection must never read as a pass when only the exit status is read, so every refusal here exits
// EXIT_ONLY_REFUSED (64, sysexits EX_USAGE) - a status no other refusal in these drivers uses (STALE anchors,
// a dirty src/ and a red baseline are 2). Both `--only A,B` and `--only=A,B` are accepted, repeatable; a token is
// one mutation id, never a range (`49-55` is one unknown id); EVERY token must name a mutation. The drivers call it
// as the first statement of main, before any STALE check, git or vitest run. ops/lib/check-mutate-only.py runs
// every driver with a selection that names nothing and one that does not parse, and refuses unless each exits 64.

export const EXIT_ONLY_REFUSED = 64;
const FLAG = "--only";

function refuse(why) {
  process.stdout.write(`REFUSING TO RUN: ${why}\n`);
  process.exit(EXIT_ONLY_REFUSED);
}

/** null when argv carries no --only; otherwise the distinct ids it names, every one of them in `ids`. */
export function onlyIds(argv, ids) {
  let tokens = null;
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    let value;
    if (arg === FLAG) {
      if (i + 1 >= argv.length || argv[i + 1].startsWith("--")) refuse(`${FLAG} has no value`);
      value = argv[i + 1];
      i += 1;
    } else if (arg.startsWith(`${FLAG}=`)) {
      value = arg.slice(FLAG.length + 1);
    } else if (arg.startsWith(FLAG)) {
      refuse(`'${arg}' is not a flag this driver knows; did you mean ${FLAG}?`);
    } else {
      continue;
    }
    const parts = value.split(",");
    if (parts.some((p) => p.trim() === "" || p !== p.trim())) refuse(`${FLAG} '${value}' has an empty or padded token`);
    tokens = (tokens ?? []).concat(parts);
  }
  if (tokens === null) return null;
  const known = new Set(ids);
  const unknown = tokens.filter((t) => !known.has(t));
  if (unknown.length > 0) refuse(`${FLAG} names no entry of this population: ${unknown.join(", ")} (a token is one mutation id, never a range)`);
  return [...new Set(tokens)];
}
