## Findings for full5 (Kairos f1ff3f8, Kairos configs only; written after the run, tables below are generated)

full5 reruns the identical suite (same 30 tasks, checkers, fixtures, prompts, limits; v1's seeded order filtered to
Kairos) at Kairos f1ff3f8. New since full4 (0367e99): `browser_console` refuses while a dialog is open, with a 5 s
backstop (328f1a3); `browser_type` retypes once with CloakBrowser's typos off when the field holds the text plus
stray letters (0310529, a9820da); a gateway CLI Ctrl+C fix that is not on the bench path (f1ff3f8). The static
schema is unchanged (20 tools, 3,117 tokens). Full tables: `compare_full5.md`. From full5 on, each run record also
holds the client process's `exit_code`.

**The two targeted failures: fixed.**

1. *dyn-spa-create typos ("Orkion").* 0 of 8 runs created a name other than "Orion" (full4: 1 of 8, "Orkion"; full:
   1, "Oriomn"; full2: 1, "Orilon" then "Orion"; full3: 0). The retype is not logged, so it can only be inferred:
   two full5 `browser_type` calls took longer than any in full4 (gpt-6-luna r2 6.7 s, gpt-6.1-sol r2 5.5 s; full4
   max 4.6 s, full5 median 4.0 s), and both ended with the field holding exactly "Orion". With 8 runs and a failure
   rate of about 1 in 8 before, 0 of 8 is consistent with the fix but not proof on its own.
2. *dialogs-welcome console hang / silent exit.* 8 of 8 runs passed. Agents called `browser_console` 4 times while
   the alert was open; every call was refused in 0.001 s with "A alert dialog is open ("Welcome! Your access code is
   ZK-73."). Call browser_handle_dialog first.", and the agent then handled the dialog. With the old code, the same
   call blocked for the full 120 s browser-operation timeout in 9 runs across full to full4 (all still passed), and
   one full4 run (`full4.kairos.claude-haiku-5-5.dialogs-welcome.r2`) exited silently during it. In full5 all 240
   Kairos processes exited with code 0; no run ended in status error.

**Kairos across the reruns (tokens per success; success with 95% CI), full / full2 / full3 / full4 -> full5:**

- Haiku 5.5: success 100% / 97% / 98% / 93% -> 98% (91-100); tool errors per run 0.18 / 0.32 / 0.23 / 0.23 -> 0.18;
  tokens per success 35.6k / 39.4k / 26.1k / 27.8k -> 27.4k; large-page tokens per run 94k / 116k / 46k / 45k -> 45k;
  calls per task 4.6 / 4.8 / 4.1 / 4.2 -> 4.2. The only failure is `pub-quotes-author.r1` (checker strictness).
- glm-5.3-flash: 95% / 95% / 100% / 98% -> 98%; 20.4k / 23.7k / 22.0k / 20.2k -> 23.2k; large 150k / 98k / 46k / 33k
  -> 45k per run. The large-page rise vs full4 is inside glm's own v1 noise band (150k vs 98k between two runs of the
  same code).
- gpt-6-luna: 92% / 95% / 92% / 93% -> 95%; 19.2k / 17.4k / 16.8k / 14.4k -> 14.6k; large 50k / 37k / 34k / 16k ->
  16k.
- gpt-6.1-sol: 98% / 97% / 97% / 97% -> 97%; 18.3k / 19.2k / 15.2k / 15.3k -> 14.9k; large 34k / 39k / 19k / 17k ->
  17k.
- No hangs in any phase for any model. Small categories for Haiku stay within the v1 noise band (full -> full2 drift
  was -10% to +16% on tokens per success): full4 -> full5 basic +10%, forms -5%, dialogs +2%, frames-tabs -1%,
  dynamic -10%.

**Every full5 failure (7, none from the browser layer's new code):**

- `full5.kairos.claude-haiku-5-5.pub-quotes-author.r1`, `full5.kairos.glm-5.3-flash.pub-quotes-author.r1`,
  `full5.kairos.gpt-6-luna.pub-quotes-author.r1`, `full5.kairos.gpt-6-luna.pub-quotes-author.r2`: answered "July 12,
  1904 in Parral, Chile" (birthplace included; the strict pre-written checker expects the date only, as in every
  earlier phase).
- `full5.kairos.gpt-6-luna.pub-quotes-scroll.r1`: answered "Albert Einstein" (wrong quote counted; the same model
  error appears in every phase).
- `full5.kairos.gpt-6.1-sol.pub-js-prompt.r1` and `.r2`: answered "done" instead of the result text (sol does this
  in every phase).

**Other observations:** 1 provider stall (gpt-6.1-sol `pub-quotes-scroll.r1`, ~292 s waiting on the API with no
tool running; the harness killed it, recorded exit code 15 in `api_errors.jsonl`, and the rerun passed). No
request crossed the 100K-token price tier. full5 cost $0.83 (Haiku $0.06, glm $0.10, luna $0.04, sol $0.63);
project total $5.09.

**Caveat:** both fixes were designed after seeing these exact failures on this suite (`dyn-spa-create` "Orkion" and
the `dialogs-welcome` console hang in full4), so full5 shows they fix those cases, not that they generalize. Both
failures were intermittent (about 1 in 8 runs for the typo, 1 in 240 for the silent exit), so one clean run of 8
and 240 runs is supportive evidence, not proof; the console fix is better evidenced, since the refusal itself is
visible in all 4 calls. The suite, checkers and prompts are unchanged, and the full -> full2 drift of unchanged
code is the noise band to read the other numbers against.
