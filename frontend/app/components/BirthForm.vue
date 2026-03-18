<script setup lang="ts">
const { interpretChart } = useApi();

const form = reactive({
  year: 1991,
  month: 1,
  day: 13,
  hour: 2,
  minute: 40,
});

const loading = ref(false);
const result = ref<{
  chart: Record<string, any>;
  interpretation: string | null;
} | null>(null);
const error = ref("");

async function submit() {
  loading.value = true;
  error.value = "";
  result.value = null;

  try {
    result.value = await interpretChart(form);
  } catch (e: any) {
    error.value = e.data?.detail || "排盤失敗，請檢查輸入";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div>
    <form class="grid grid-cols-5 gap-3" @submit.prevent="submit">
      <div>
        <label class="block text-sm text-slate-400">年</label>
        <input
          v-model.number="form.year"
          type="number"
          min="1900"
          max="2100"
          class="w-full rounded bg-slate-700 px-3 py-2 text-white"
        />
      </div>
      <div>
        <label class="block text-sm text-slate-400">月</label>
        <input
          v-model.number="form.month"
          type="number"
          min="1"
          max="12"
          class="w-full rounded bg-slate-700 px-3 py-2 text-white"
        />
      </div>
      <div>
        <label class="block text-sm text-slate-400">日</label>
        <input
          v-model.number="form.day"
          type="number"
          min="1"
          max="31"
          class="w-full rounded bg-slate-700 px-3 py-2 text-white"
        />
      </div>
      <div>
        <label class="block text-sm text-slate-400">時</label>
        <input
          v-model.number="form.hour"
          type="number"
          min="0"
          max="23"
          class="w-full rounded bg-slate-700 px-3 py-2 text-white"
        />
      </div>
      <div>
        <label class="block text-sm text-slate-400">分</label>
        <input
          v-model.number="form.minute"
          type="number"
          min="0"
          max="59"
          class="w-full rounded bg-slate-700 px-3 py-2 text-white"
        />
      </div>

      <div class="col-span-5 mt-2">
        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded bg-emerald-600 py-3 font-semibold transition hover:bg-emerald-500 disabled:opacity-50"
        >
          {{ loading ? "排盤解讀中..." : "開始解讀" }}
        </button>
      </div>
    </form>

    <div v-if="error" class="mt-6 rounded bg-red-900/50 p-4 text-red-300">
      {{ error }}
    </div>

    <div v-if="result" class="mt-8 space-y-6">
      <!-- 盤面摘要 -->
      <div class="rounded-lg bg-slate-700/50 p-6">
        <h2 class="mb-3 text-lg font-semibold text-emerald-400">命盤資訊</h2>
        <div class="grid grid-cols-2 gap-2 text-sm text-slate-300">
          <div>干支：{{ result.chart["干支"] }}</div>
          <div>排局：{{ result.chart["排局"] }}</div>
          <div>節氣：{{ result.chart["節氣"] }}</div>
          <div>排盤方式：{{ result.chart["排盤方式"] }}</div>
        </div>
      </div>

      <!-- AI 解讀 -->
      <div v-if="result.interpretation" class="rounded-lg bg-slate-700/50 p-6">
        <h2 class="mb-3 text-lg font-semibold text-emerald-400">AI 解讀</h2>
        <div class="whitespace-pre-wrap text-slate-200 leading-relaxed">
          {{ result.interpretation }}
        </div>
      </div>
    </div>
  </div>
</template>
