决策：verified

变更依据：筛选条件变化后仍沿用旧页码，导致第 3 页请求返回空数据，而匹配记录实际位于第 1 页。

修改文件：
- src/pages/UserList.tsx
- src/pages/UserList.test.tsx

上下文来源：手动检查上述两个文件的差异，并使用 build-bug-context.py 收集变更范围。

行为主张：
- C1：[source: specified] [source-ref: 用户原句：“修改筛选条件时，页码重置为 1”] 用户在任意页修改筛选条件时，下一次请求会先把页码重置为 1。
- C2：[source: existing-contract] [source-ref: src/pages/UserList.test.tsx：筛选空状态回归测试] 筛选结果为零条时，页面展示筛选空状态且不保留旧列表行。

最小反例：
- C1：用户停留在第 3 页，再选择仅有一页结果的筛选条件；若请求仍携带第 3 页，就推翻该主张。
- C2：页面先展示旧数据，再应用返回零条记录的筛选条件；若旧行仍可见，就推翻该主张。

证据：
- C1：通过：检查 src/pages/UserList.tsx 可见筛选处理器先写入页码 1，再构造请求；回归测试通过并断言了请求页码。
- C2：通过：src/pages/UserList.test.tsx 的回归测试先写入旧列表，再模拟空响应，测试通过并断言筛选空状态与旧行消失。

执行检查：
- 通过：`npm test -- UserList.test.tsx`，退出码 0，2 项测试通过。
- 通过：浏览器检查从第 3 页执行单页筛选与空结果筛选，两条路径都展示预期状态。

剩余风险：当前页面未启用跨页全选，因此未覆盖该组合路径。
