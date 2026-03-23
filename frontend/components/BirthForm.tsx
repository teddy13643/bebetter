"use client";

import { useState } from "react";

interface UnifiedResponse {
  qimen: Record<string, any>;
  liuren: Record<string, any>;
  taiyi: Record<string, any>;
  interpretation: string | null;
}

const fields = [
  { key: "year", label: "年", min: 1900, max: 2100 },
  { key: "month", label: "月", min: 1, max: 12 },
  { key: "day", label: "日", min: 1, max: 31 },
  { key: "hour", label: "時", min: 0, max: 23 },
  { key: "minute", label: "分", min: 0, max: 59 },
] as const;

const qimenFields = ["干支", "排局", "節氣", "排盤方式"];

const liurenInfoFields = [
  { key: "節氣", label: "節氣" },
  { key: "日期", label: "日期" },
  { key: "農曆月", label: "農曆月" },
  { key: "格局", label: "格局" },
];
const sanChuan = ["初傳", "中傳", "末傳"] as const;
const sanChuanLabels = ["地支", "天將", "六親", "天干"];

const taiyiInfoFields = [
  { key: "太乙", label: "太乙" },
  { key: "天乙", label: "天乙" },
  { key: "地乙", label: "地乙" },
  { key: "八門值事", label: "八門值事" },
];
const taiyiCalcFields = [
  { key: "主算", label: "主算" },
  { key: "客算", label: "客算" },
  { key: "定算", label: "定算" },
];

function formatTaiyiCalc(val: any): string {
  if (!Array.isArray(val)) return String(val);
  const [num, desc] = val;
  const descStr = Array.isArray(desc) ? desc.join("、") : desc;
  return `${num}（${descStr}）`;
}

export function BirthForm() {
  const [form, setForm] = useState({
    year: 1991,
    month: 1,
    day: 13,
    hour: 2,
    minute: 40,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UnifiedResponse | null>(null);
  const [error, setError] = useState("");

  function updateField(key: string, value: number) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch("/api/interpret", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || `排盤失敗 (${res.status})`);
      }
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message || "排盤失敗，請檢查輸入");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Form Card */}
      <div className="rounded-2xl border border-brand-border bg-brand-surface/60 p-8 backdrop-blur">
        <h2 className="mb-2 font-heading text-xl font-bold text-white">
          三式合參
        </h2>
        <p className="mb-6 text-sm text-brand-muted">
          同時排奇門遁甲、大六壬、太乙神數，AI 統整解讀
        </p>
        <form className="space-y-6" onSubmit={submit}>
          <div className="grid grid-cols-5 gap-3">
            {fields.map((f) => (
              <div key={f.key}>
                <label className="mb-1.5 block text-sm font-medium text-brand-muted">
                  {f.label}
                </label>
                <input
                  type="number"
                  min={f.min}
                  max={f.max}
                  value={form[f.key]}
                  onChange={(e) => updateField(f.key, Number(e.target.value))}
                  className="w-full rounded-lg border border-brand-border bg-brand-bg px-3 py-2.5 text-white placeholder-brand-muted/50 transition focus:border-brand-accent focus:outline-none focus:ring-1 focus:ring-brand-accent"
                />
              </div>
            ))}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-brand-accent py-3 font-heading text-base font-bold text-white transition hover:bg-brand-accent-hover disabled:opacity-50"
          >
            {loading ? "三式排盤解讀中..." : "開始解讀"}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-900/30 p-4 text-red-300">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* 三盤摘要 */}
          <div className="grid gap-6 lg:grid-cols-3">
            {/* 奇門遁甲 */}
            <div className="rounded-2xl border border-brand-border bg-brand-surface/60 p-6 backdrop-blur">
              <h3 className="mb-3 font-heading text-lg font-bold text-brand-accent">
                奇門遁甲
              </h3>
              <div className="space-y-2 text-sm">
                {qimenFields.map((field) => (
                  <div
                    key={field}
                    className="rounded-lg bg-brand-bg/50 px-3 py-2"
                  >
                    <span className="text-brand-muted">{field}</span>
                    <p className="mt-0.5 text-brand-text">
                      {result.qimen[field]}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* 大六壬 */}
            <div className="rounded-2xl border border-brand-border bg-brand-surface/60 p-6 backdrop-blur">
              <h3 className="mb-3 font-heading text-lg font-bold text-brand-accent">
                大六壬
              </h3>
              <div className="space-y-2 text-sm">
                {liurenInfoFields.map((f) => (
                  <div
                    key={f.key}
                    className="rounded-lg bg-brand-bg/50 px-3 py-2"
                  >
                    <span className="text-brand-muted">{f.label}</span>
                    <p className="mt-0.5 text-brand-text">
                      {Array.isArray(result.liuren[f.key])
                        ? result.liuren[f.key].join("、")
                        : result.liuren[f.key]}
                    </p>
                  </div>
                ))}
              </div>
              {/* 三傳 */}
              {result.liuren["三傳"] && (
                <div className="mt-3 grid grid-cols-3 gap-2">
                  {sanChuan.map((name) => (
                    <div
                      key={name}
                      className="rounded-lg bg-brand-bg/50 px-2 py-2 text-center"
                    >
                      <div className="mb-1 text-xs font-medium text-brand-muted">
                        {name}
                      </div>
                      {(result.liuren["三傳"][name] as any[]).map(
                        (val, idx) => (
                          <div key={idx} className="text-xs">
                            <span className="text-brand-muted">
                              {sanChuanLabels[idx]}
                            </span>
                            <span className="ml-1 text-brand-text">{val}</span>
                          </div>
                        ),
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 太乙神數 */}
            <div className="rounded-2xl border border-brand-border bg-brand-surface/60 p-6 backdrop-blur">
              <h3 className="mb-3 font-heading text-lg font-bold text-brand-accent">
                太乙神數
              </h3>
              <div className="space-y-2 text-sm">
                {taiyiInfoFields.map((f) => (
                  <div
                    key={f.key}
                    className="rounded-lg bg-brand-bg/50 px-3 py-2"
                  >
                    <span className="text-brand-muted">{f.label}</span>
                    <p className="mt-0.5 text-brand-text">
                      {result.taiyi[f.key]}
                    </p>
                  </div>
                ))}
              </div>
              {/* 主客定算 */}
              <div className="mt-3 grid grid-cols-3 gap-2">
                {taiyiCalcFields.map((f) => (
                  <div
                    key={f.key}
                    className="rounded-lg bg-brand-bg/50 px-2 py-2 text-center"
                  >
                    <div className="mb-1 text-xs font-medium text-brand-muted">
                      {f.label}
                    </div>
                    <div className="text-xs text-brand-text">
                      {formatTaiyiCalc(result.taiyi[f.key])}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* AI 統整解讀 */}
          {result.interpretation && (
            <div className="rounded-2xl border border-brand-border bg-brand-surface/60 p-8 backdrop-blur">
              <h2 className="mb-4 font-heading text-xl font-bold text-brand-accent">
                三式合參 — AI 解讀
              </h2>
              <div className="whitespace-pre-wrap leading-relaxed text-brand-text">
                {result.interpretation}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
