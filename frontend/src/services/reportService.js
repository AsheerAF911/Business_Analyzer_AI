const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";

export async function uploadReport(file, reportType) {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("report_type", reportType);

  const response = await fetch(
    `${API_BASE_URL}/api/reports/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Report upload failed."
    );
  }

  return data;
}