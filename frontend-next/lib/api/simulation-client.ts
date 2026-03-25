import { SimulationResponse } from "@/lib/types/simulation";

const DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1";

export async function runSimulation(
  payload: Record<string, string | number>,
  baseUrl: string = process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_BASE_URL
): Promise<SimulationResponse> {
  const response = await fetch(`${baseUrl}/simulation/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Simulation request failed with status ${response.status}`);
  }

  return (await response.json()) as SimulationResponse;
}
