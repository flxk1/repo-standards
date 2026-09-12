# Contribution guide

Be nice and respect the maintainer's time. This is a one-person workspace;
everything below exists to keep it maintainable.

## Contribute

Code is not the only contribution. Fixing typos, improving docs, triaging
issues, and reviewing pull requests are all valued.

## Issues

- Search existing issues first, including closed ones.
- Bug reports include a reproduction — ideally a failing test.
- Don't bump issues without new information.

## Pull requests

- For large or breaking changes, open an issue first.
- Don't open a pull request you don't plan to see through.
- No unrelated changes; adhere to the existing code style and the repo's
  gates (`main.yml` must be green, or say why it can't be).
- Add tests and docs where relevant. Keep the REUSE/SPDX headers intact.
- Commit subjects ≤ 72 characters. If AI tooling assisted, attribute it in
  the commit body as
  `Assisted by <tool> (<vendor>); not an author or copyright holder.` —
  never as a `Co-Authored-By` trailer. CI enforces this in several repos.
- Branch from the default branch; never PR from it.
- Check "Allow edits from maintainers".

## Review

- Push new commits during review (no force-push squashing mid-review);
  squash happens at merge.
- Present solutions rather than questions where you can.
- Be patient, then bump politely.

Some repositories carry a CLA; the repository's own contributing file takes
precedence over this default wherever both exist.
