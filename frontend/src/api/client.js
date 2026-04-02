// In production, set VITE_API_URL in Vercel to your Render backend URL
// e.g. "https://fairsplit-api.onrender.com/api"
const BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
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
  submitSurvey: (enrollment, preferences) =>
    request("/survey", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enrollment, preferences }),
    }),
  getSurveyStatus: () => request("/survey/status"),
  allocate: (mode = "balanced") =>
    request("/allocate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode }),
    }),
  getAllocation: () => request("/allocation"),
  getMetrics: () => request("/metrics"),
};

export const devApi = {
  generateRandomSurveys: (seed) =>
    request(`/survey/random?seed=${seed ?? Date.now()}`, { method: "POST" }),
  loadDummy: (n, seed) =>
    request(`/dummy?n=${n}&seed=${seed ?? Date.now()}`, { method: "POST" }),
};
