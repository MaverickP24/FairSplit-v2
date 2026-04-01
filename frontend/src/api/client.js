// All API calls go through Vite's proxy → http://localhost:8000
// In production, change BASE to your deployed backend URL.
const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  // Data ingestion
  ingest: (pdfFile, excelFile) => {
    const form = new FormData();
    form.append("pdf_file", pdfFile);
    form.append("excel_file", excelFile);
    return request("/ingest", { method: "POST", body: form });
  },
  ingestJson: (jsonFile) => {
    const form = new FormData();
    form.append("file", jsonFile);
    return request("/ingest/json", { method: "POST", body: form });
  },
  getStudents: () => request("/students"),

  // Survey
  submitSurvey: (enrollment, preferences) =>
    request("/survey", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enrollment, preferences }),
    }),
  getSurveyStatus: () => request("/survey/status"),

  // Allocation
  allocate: (mode = "balanced") =>
    request("/allocate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode }),
    }),
  getAllocation: () => request("/allocation"),

  // Metrics
  getMetrics: () => request("/metrics"),
};

// Dev helpers
export const devApi = {
  generateRandomSurveys: (seed) =>
    request(`/survey/random?seed=${seed ?? Date.now()}`, { method: "POST" }),
  loadDummy: (n = 576, seed) =>
    request(`/dummy?n=${n}&seed=${seed ?? Date.now()}`, { method: "POST" }),
};
