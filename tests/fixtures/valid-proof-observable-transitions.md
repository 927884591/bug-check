Decision: verified
Change rationale: The accepted contracts define concrete time, numeric, ordering, filename, transaction, and visibility transitions.
Changed files:
- src/domain/transitions.py
- tests/test_transitions.py
Context source: Manual diff inspection of the two explicit files.
Behavior claims:
- C1 [source: existing-contract] [source-ref: tests/test_transitions.py: token expiry contract]: The access token expires exactly fifteen minutes after issuance.
- C2 [source: specified] [source-ref: user wording: "A three-unit debit changes 10 to 7"]: A three-unit debit decreases the account balance from 10 to 7.
- C3 [source: existing-contract] [source-ref: tests/test_transitions.py: stable ordering contract]: The relative order of rows with equal timestamps remains stable after sorting.
- C4 [source: specified] [source-ref: user wording: "Generated filenames use the JSON suffix"]: The generated filename ends with .json.
- C5 [source: existing-contract] [source-ref: tests/test_transitions.py: rollback contract]: The transaction rolls back after the second write fails.
- C6 [source: specified] [source-ref: user wording: "Closing removes the dialog"]: The dialog disappears after close.
Counterexamples considered:
- C1: If the token remains valid sixteen minutes after issuance, the expiry claim is disproved.
- C2: If the balance remains 10 after a three-unit debit, the numeric transition is disproved.
- C3: If tied rows reverse order after sorting, the stable-order claim is disproved.
- C4: If the filename ends with .txt, the suffix claim is disproved.
- C5: If the transaction keeps the first write after the second write fails, rollback is disproved.
- C6: If the dialog remains visible after close, the visibility claim is disproved.
Evidence:
- C1: PASS: The clock-controlled regression test observed expiry at fifteen minutes.
- C2: PASS: The numeric regression test asserted a final balance of 7 from an initial 10.
- C3: PASS: The tied-row regression test preserved the original order.
- C4: PASS: The filename regression test asserted the .json suffix.
- C5: PASS: The transaction regression test injected a second-write failure and observed no persisted writes.
- C6: PASS: The UI-state regression test closed the dialog and observed it absent.
Checks run:
- PASS: `pytest tests/test_transitions.py` completed with exit code 0 and 6 tests passed.
Remaining risks: Distributed-clock skew is not represented by the deterministic local clock fixture.
