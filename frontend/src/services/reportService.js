const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

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

  let data;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(
      data?.detail || "Failed to upload report."
    );
  }

  return data;
}