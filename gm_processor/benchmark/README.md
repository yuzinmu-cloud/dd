# GM Benchmark v0.1

此 Benchmark 評估 GM Processor 的結構正確性、行動理解、規則裁定、創意應變、一致性與安全失敗。它不以固定敘事逐字比對，也不代表完整 TRPG 主持品質。

```powershell
python -m gm_processor.benchmark.benchmark_runner
python -m gm_processor.benchmark.benchmark_runner --category safety
python -m gm_processor.benchmark.benchmark_runner --context-mode ollama
```

預設 Mock 模式使用通用且可重複的 AIClient-compatible provider。Ollama 模式使用目前本機模型；服務不可用時仍會產生安全報告。

實際 JSON/Markdown 報告寫入 `benchmark/reports/` 並由 Git 忽略。
