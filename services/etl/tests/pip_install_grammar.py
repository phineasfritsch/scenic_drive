"""pip's `install` argument grammar, as much of it as this repo is willing to vouch for.

Extracted verbatim from `test_dockerfile.py`, which was 436 lines against the repo's 300-line cap and was
two things wearing one filename: this parser, which knows nothing about Docker, and a set of assertions
about the image. Nothing here changed in the move - the flag whitelists, the quote-aware splitter, the
shlex tokenizer and the fail-closed classifier are byte-identical to the versions four rounds of review
argued into shape, and their docstrings carry that history because it is the reason each rule exists.

The one thing to preserve if you touch this file: **it is a whitelist, not a blacklist.** A token is safe
only when positively recognized as one of a few confidently-understood shapes. Everything else fails
closed. Round 4 is the argument for that - `--build` was whitelisted as a safe destination flag, is not a
real pip flag at all, and pip's long-option parser accepts it as an unambiguous abbreviation of
`--build-constraint`, so `pip install --build constraints.txt requests` passed every test in the suite.

Its only consumer is `test_dockerfile.py`. It is not named `test_*`, so pytest does not collect it, and it
imports nothing from the Dockerfile side - which is the point of the split.
"""
import re
import shlex


# Every flag name below was validated against a real, installed pip - not written from memory - after
# round 4 found a hallucinated entry (`--build`) that created a real bypass; see pip_indirect_targets's
# docstring and the task log for how, and for what "validated" means here.

# Flags that read an external file (or a `pyproject.toml` dependency group) whose *content* decides what
# gets installed - the actual unreadable-target class this whole check exists for.
PIP_UNREADABLE_TARGET_FLAGS_LONG = (
    "--requirement", "--editable", "--constraint", "--build-constraint",
    "--requirements-from-script", "--group",
)

# Long flags confidently known to take a value that is NOT an install source - a destination directory, an
# index host, a timeout, ... Their value is skipped rather than examined, so a perfectly ordinary
# `pip install --target /opt/vendor requests` is never misread as installing from "/opt/vendor". This is
# a whitelist, not a blacklist: a long flag that is not on this list, the unreadable-target list, or the
# boolean list below is treated as unrecognized (see `pip_indirect_targets`), not assumed safe.
PIP_DESTINATION_VALUE_FLAGS_LONG = (
    "--target", "--root", "--prefix", "--src", "--cache-dir", "--log", "--python",
    "--platform", "--python-version", "--implementation", "--abi", "--proxy", "--retries", "--timeout",
    "--progress-bar", "--report", "--index-url", "--extra-index-url", "--find-links", "--trusted-host",
    "--cert", "--client-cert", "--upgrade-strategy", "--config-settings",
    "--no-binary", "--only-binary", "--exists-action", "--root-user-action",
    "--all-releases", "--only-final", "--uploaded-prior-to", "--keyring-provider",
    "--use-feature", "--use-deprecated", "--resume-retries",
)

# Long flags confidently known to take no value at all - stable, common, unambiguous. Also a whitelist:
# absence from this list is not evidence of danger, it is just not something this check will vouch for.
PIP_BOOLEAN_FLAGS_LONG = (
    "--user", "--upgrade", "--no-deps", "--no-cache-dir", "--no-compile", "--compile",
    "--no-build-isolation", "--check-build-dependencies", "--break-system-packages",
    "--force-reinstall", "--ignore-requires-python", "--no-warn-script-location", "--no-warn-conflicts",
    "--prefer-binary", "--no-clean", "--require-hashes", "--no-input",
    "--no-index", "--pre", "--disable-pip-version-check", "--no-color", "--dry-run", "--ignore-installed",
    "--help", "--quiet", "--verbose", "--isolated", "--debug", "--require-virtualenv", "--version",
)

# Single letters pip's `install` recognizes as short options, UNBUNDLED (see `pip_indirect_targets` for
# why a bundle of two or more is never resolved at all): which spell an unreadable target, which take a
# value that is a destination rather than a source, and which take no value.
PIP_UNREADABLE_TARGET_LETTERS = set("rce")  # -r requirement / -c constraint / -e editable
PIP_DESTINATION_VALUE_LETTERS = set("tCif")  # -t target / -C config-settings / -i index-url / -f find-links
PIP_BOOLEAN_LETTERS = set("qvUIhV")  # -q quiet / -v verbose / -U upgrade / -I ignore-installed / -h help / -V version


def _split_unquoted(text, seps=("&&", "|", ";")):
    """Split `text` on `&&`, `|`, or `;` - the boundaries the rest of this file treats as command
    separators - but never inside a single- or double-quoted region.

    Round 3's `re.split(r"&&|\\||;", run_line)` split on *every* `;` in the raw text, including one
    sitting inside an ordinary quoted argument - `pip install "requests; python_version>='3.8'"`, a
    completely standard PEP 508 environment marker, was torn into two fake command segments before this
    file ever got a chance to recognize the quoting, and round 3's "unresolvable quoting fails closed"
    rule then rejected the fragments. This function tracks quote state with a single pass and one
    character of lookahead - no backslash-escape handling - which is enough for ordinary Dockerfile RUN
    text; anything stranger either still segments correctly by luck or surfaces later as an "unparsable"
    `pip_install_arglists` result via `_shlex_tokens`, which is the fail-closed outcome this file wants
    regardless.
    """
    out, buf, quote = [], [], None
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue
        sep = next((s for s in seps if text.startswith(s, i)), None)
        if sep:
            out.append("".join(buf))
            buf = []
            i += len(sep)
            continue
        buf.append(ch)
        i += 1
    out.append("".join(buf))
    return out


def _shlex_tokens(text):
    """Tokenize `text` the way a POSIX shell would - quotes grouped and their delimiters stripped - using
    the standard library's `shlex` rather than a hand-rolled quote parser, so `"./localpkg"` arrives as
    one token, `./localpkg`, with no separate quote-stripping step needed downstream, and a quoted PEP 508
    marker like `"requests; python_version>='3.8'"` arrives as one token instead of being split on its own
    whitespace.

    Returns `(tokens, ok)`. `ok` is False when `text` cannot be tokenized at all - almost always an
    unbalanced quote, which happens when this text was extracted from inside a *still larger* quoted
    context this function never saw, such as a `pip install` written inside `sh -c "..."` (the extraction
    keeps everything from "install" to the end of that segment, which ends mid-quote when the segment
    itself was quoted from the outside). That failure is reported as unparsable, not silently ignored or
    guessed at - the same fail-closed answer this file gives a heredoc it cannot read into.
    """
    try:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer), True
    except ValueError:
        return [], False


def pip_install_arglists(run_line):
    """`(tokens, ok)` for every `pip install` invocation in one RUN instruction (`pip`, `pip3`, or
    `python -m pip`/`python3 -m pip` all match, and so does a `pip` wrapped in `sh -c "..."` or given by
    its full path) - split at unquoted &&/|/; boundaries (`_split_unquoted`) so one command's flags can
    never leak into another's, and so a `;` inside a quoted argument never manufactures a fake boundary.
    """
    out = []
    for segment in _split_unquoted(run_line):
        for m in re.finditer(r"\bpip3?\b[^&|;]*?\binstall\b", segment):
            out.append(_shlex_tokens(segment[m.end():]))
    return out


def pip_indirect_targets(args):
    """Everything in one `pip install` invocation's (already quote-resolved) argument list that this
    parser cannot confidently read, resolve, or vouch for.

    This is a whitelist, not a blacklist: a token is only ever treated as safe when it is positively
    recognized as one of a small number of confidently-understood shapes (a known boolean flag, a known
    destination-value flag, or a bare word that is not a flag, not a `$` substitution, and does not look
    like a local path). Everything else fails closed, including:

    - `-r`/`-c`/`-e`/`--build-constraint`/`--requirements-from-script`/`--group`, long or short,
      unbundled - flags that read an external file or `pyproject.toml` group whose *content* decides what
      gets installed. Round 4 added the last three: a real pip only has three single-letter flags of this
      shape (`-r`/`-c`/`-e`), but its long-form flag set has six, and this file only knew about half of
      them until reviewer-29's round-4 finding forced actually reading `pip install --help` instead of
      recalling it.
    - **any bundled short flag at all** (two or more letters after a single `-`), regardless of which
      letters. reviewer-29 proved short-option bundling resolves via the FIRST value-taking letter
      consuming the rest of that same token, not the LAST letter consuming the next token, and modeling
      that correctly for every letter pip might ever add is exactly the game of catch-up this file's
      docstrings already record losing repeatedly. Refusing to parse a bundle at all closes the whole
      class at once, at the cost of also failing on harmless bundles like `-qt` - a trade this file takes
      deliberately; see the task log.
    - a bare positional path (`.`, `..`, or anything starting `./`, `../` or `/`) - pip installs a local
      directory as a plain positional argument with no flag required at all.
    - a token containing `$` - a shell/build-time substitution (`ARG`/`ENV`) this parser cannot resolve;
      it could name a URL, a `git+` ref, or a `-r` file just as easily as a version pin.
    - a long or short flag that is not on one of the three small, explicitly-curated lists above - an
      "unrecognized flag" is a flag this check does not know it can vouch for, not a flag assumed safe.
      round 4 removed three entries from those lists (`--build`, `--use-pep517`,
      `--no-python-version-warning`) that were never real pip flags to begin with - `--build` in
      particular is what let `pip install --build constraints.txt requests` through: pip does not have a
      `--build` flag, but its long-option parser accepts any unambiguous prefix of a real one, and
      `--build` is an unambiguous prefix of `--build-constraint`. Whitelisting a flag name that was never
      validated against a real pip whitelisted a bypass without anyone writing one on purpose. This
      whitelist stays sound only because every entry is an *exact, complete* name copied from a real
      `pip install --help`, matched here with plain string equality - never a prefix, never a guess - so
      the abbreviation feature that created the `--build` hole has nothing to attach to on this side: an
      abbreviated or unvalidated spelling of *any* flag, safe or dangerous, is simply not on the list and
      therefore always falls through to "unrecognized" and fails closed.

    None of this reads what a target *contains* - only whether the argument list names one this parser
    cannot see into, or contains something it cannot confidently classify at all.
    """
    offenders = []
    skip_next = False
    for tok in args:
        if skip_next:
            skip_next = False
            continue

        if "$" in tok:
            offenders.append((tok, "a shell/build-arg substitution this parser cannot resolve"))
            continue

        if tok.startswith("--"):
            head = tok.split("=", 1)[0]
            if head in PIP_UNREADABLE_TARGET_FLAGS_LONG:
                offenders.append((tok, "an unreadable target flag"))
                skip_next = "=" not in tok
                continue
            if head in PIP_DESTINATION_VALUE_FLAGS_LONG:
                skip_next = "=" not in tok
                continue
            if head in PIP_BOOLEAN_FLAGS_LONG:
                continue
            offenders.append((tok, "a long flag this check does not recognize"))
            continue

        if tok.startswith("-") and len(tok) > 1:
            letters = tok[1:]
            if len(letters) > 1:
                offenders.append((tok, "a bundled short flag - bundling order is not modeled"))
                continue
            letter = letters
            if letter in PIP_UNREADABLE_TARGET_LETTERS:
                offenders.append((tok, "an unreadable target flag"))
                skip_next = True
                continue
            if letter in PIP_DESTINATION_VALUE_LETTERS:
                skip_next = True
                continue
            if letter in PIP_BOOLEAN_LETTERS:
                continue
            offenders.append((tok, "a short flag this check does not recognize"))
            continue

        if tok in (".", "..") or tok.startswith(("./", "../", "/")):
            offenders.append((tok, "a local path"))
            continue
        # else: an ordinary requirement specifier - a package name, optionally pinned, extras'd, or
        # carrying a PEP 508 environment marker - and therefore safe as far as this check goes.
    return offenders
