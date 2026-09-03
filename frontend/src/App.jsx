import { useState } from "react";
import { uploadReport } from "./services/reportService";

const REPORT_TYPES = [
  "Sales",
  "Purchase",
  "Inventory",
  "Manufacturing",
  "Accounting",
  "Receivables",
  "Payables",
  "Other",
];

function App() {
  const [file, setFile] = useState(null);
  const [reportType, setReportType] = useState("Sales");

  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0] || null;

    setFile(selectedFile);
    setSuccess(null);
    setError(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setSuccess(null);
    setError(null);

    if (!file) {
      setError("Please select a report file.");
      return;
    }

    try {
      setUploading(true);

      const result = await uploadReport(
        file,
        reportType
      );

      setSuccess(result);

      setFile(null);
      event.target.reset();

    } catch (err) {
      setError(
        err.message || "Something went wrong while uploading."
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1>Business AI</h1>

        <p style={styles.subtitle}>
          Upload a business report to begin processing.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={styles.field}>
            <label htmlFor="report-file">
              Report File
            </label>

            <input
              id="report-file"
              type="file"
              accept=".pdf,.xlsx,.xls,.csv"
              onChange={handleFileChange}
              disabled={uploading}
            />

            <small>
              Supported formats: PDF, XLSX, XLS, CSV
            </small>
          </div>

          <div style={styles.field}>
            <label htmlFor="report-type">
              Report Type
            </label>

            <select
              id="report-type"
              value={reportType}
              onChange={(event) =>
                setReportType(event.target.value)
              }
              disabled={uploading}
            >
              {REPORT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={uploading}
          >
            {uploading ? "Uploading..." : "Upload Report"}
          </button>
        </form>

        {success && (
          <div style={styles.success}>
            <strong>Report uploaded successfully.</strong>

            <p>
              Report ID: <strong>{success.id}</strong>
            </p>

            <p>
              Filename: {success.original_filename}
            </p>

            <p>
              Type: {success.report_type}
            </p>

            <p>
              Status: {success.status}
            </p>
          </div>
        )}

        {error && (
          <div style={styles.error}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "#f5f6f8",
    padding: "20px",
  },

  card: {
    width: "100%",
    maxWidth: "500px",
    background: "#ffffff",
    padding: "32px",
    borderRadius: "12px",
    boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
  },

  subtitle: {
    color: "#666",
    marginBottom: "28px",
  },

  field: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    marginBottom: "20px",
  },

  label: {
    fontWeight: "600",
  },

  button: {
    width: "100%",
  },

  success: {
    marginTop: "24px",
    padding: "16px",
    borderRadius: "8px",
    background: "#eaf7ee",
    border: "1px solid #b7dfc3",
  },

  error: {
    marginTop: "24px",
    padding: "16px",
    borderRadius: "8px",
    background: "#fdecec",
    border: "1px solid #f1b5b5",
    color: "#a00000",
  },
};

export default App;