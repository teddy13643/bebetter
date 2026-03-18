interface ChartRequest {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
}

interface ChartResponse {
  chart: Record<string, any>;
  interpretation: string | null;
}

export function useApi() {
  const config = useRuntimeConfig();
  const baseURL = config.public.apiBase;

  async function getChart(req: ChartRequest): Promise<ChartResponse> {
    return $fetch(`${baseURL}/chart`, { method: "POST", body: req });
  }

  async function interpretChart(req: ChartRequest): Promise<ChartResponse> {
    return $fetch(`${baseURL}/chart/interpret`, { method: "POST", body: req });
  }

  return { getChart, interpretChart };
}
