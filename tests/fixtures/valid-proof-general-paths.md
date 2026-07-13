Decision: verified
Change rationale: The accepted repository contract covers root files, Unicode paths, and unchanged generated companions without narrowing the proof to one stack.
Changed files:
- go.sum
- BUILD.bazel
- requirements.in
- LICENSE
- 用户资料编辑页面.vue
- src/api/client.ts
- Generated files remain unchanged after review: src/api/schema.generated.ts
Context source: Manual diff inspection of the listed explicit files.
Behavior claims:
- C1 [source: existing-contract] [source-ref: go.sum:1]: The dependency checksum file ends with the exact digest emitted by the locked module graph.
- C2 [source: existing-contract] [source-ref: BUILD.bazel:12]: The relative order of rows with equal timestamps remains stable after sorting.
- C3 [source: specified] [source-ref: user wording: "The profile page writes the selected locale"]: 用户资料编辑页面.vue 保存后写入用户选择的语言值。
Counterexamples considered:
- C1: If the generated checksum ends with a different digest for the same module graph, the lock contract is disproved.
- C2: If two tied rows reverse order after sorting, the stable-order contract is disproved.
- C3: 如果用户选择中文后保存仍写入旧语言值，就推翻该主张。
Evidence:
- C1: PASS. The regression test inspected go.sum after resolving the locked graph and matched the expected digest.
- C2: PASS. The sorting regression test used tied timestamps and observed the original row order.
- C3: 通过。前端回归测试保存中文选项后读取请求载荷，并断言语言值为中文。
Checks run:
- PASS. `./gradlew test` executed the focused behavior suite.
- PASS. `./mvnw test` executed the focused behavior suite.
- PASS. `bazel test //...` executed the repository behavior targets.
- PASS. `npx vitest run` executed the frontend regression suite.
- PASS. `mix test` executed the service regression suite.
- PASS. `flutter test` executed the client regression suite.
Remaining risks: Platform-specific line-ending normalization remains outside this same-platform proof.
