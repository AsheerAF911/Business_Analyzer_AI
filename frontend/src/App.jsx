import { useState } from "react";
import { uploadReport } from "./services/reportService";
import {
  askQuestion,
} from "./services/askService";

const COMMON_QUESTIONS = [
  "Which products were received under D1IN0818?",
  "Tell me about D1IN0820.",
  "Which transaction contains chilli powder?",
  "What was received from TEAM 2?",
  "What was the total quantity received?",
  "Which transaction received the highest quantity?",
];

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
  const [file, setFile] =
    useState(null);

  const [reportType, setReportType] =
    useState("Inventory");

  const [uploading, setUploading] =
    useState(false);

  const [uploadMessage, setUploadMessage] =
    useState("");

  const [uploadError, setUploadError] =
    useState("");

  const [question, setQuestion] =
    useState("");

  const [asking, setAsking] =
    useState(false);

  const [answer, setAnswer] =
    useState("");

  const [sources, setSources] =
    useState([]);

  const [askError, setAskError] =
    useState("");


  async function handleUpload(event) {
    event.preventDefault();

    if (!file) {
      setUploadError(
        "Please select a report."
      );
      return;
    }

    setUploading(true);
    setUploadError("");
    setUploadMessage("");

    try {
      const result =
        await uploadReport(
          file,
          reportType
        );

      setUploadMessage(
        `Report processed successfully. ${
          result.chunks_indexed
            ? `${result.chunks_indexed} chunks indexed.`
            : ""
        }`
      );
    } catch (error) {
      setUploadError(
        error.message ||
          "Report processing failed."
      );
    } finally {
      setUploading(false);
    }
  }


  async function submitQuestion(
    value = question
  ) {
    const cleanQuestion =
      value.trim();

    if (!cleanQuestion) {
      setAskError(
        "Please enter a question."
      );
      return;
    }

    setQuestion(cleanQuestion);
    setAsking(true);
    setAskError("");
    setAnswer("");
    setSources([]);

    try {
      const result =
        await askQuestion(
          cleanQuestion
        );

      setAnswer(result.answer);
      setSources(
        result.sources || []
      );
    } catch (error) {
      setAskError(
        error.message ||
          "Unable to contact the AI service."
      );
    } finally {
      setAsking(false);
    }
  }


  return (
    <main className="app-shell">
      <header className="hero">
        <p className="eyebrow">
          Business Report Intelligence
        </p>

        <h1>
          AI Business Investigator
        </h1>

        <p className="hero-copy">
          Upload a business report,
          index its evidence, and ask
          questions about the data.
        </p>
      </header>

      <section className="panel">
        <div className="section-heading">
          <h2>Upload report</h2>
          <p>
            Process and index a report
            before asking questions.
          </p>
        </div>

        <form
          className="upload-form"
          onSubmit={handleUpload}
        >
          <select
            value={reportType}
            onChange={(event) =>
              setReportType(
                event.target.value
              )
            }
          >
            <option value="Inventory">
              Inventory
            </option>
          </select>

          <input
            type="file"
            accept=".xlsx,.xls,.csv,.pdf"
            onChange={(event) =>
              setFile(
                event.target.files?.[0] ||
                  null
              )
            }
          />

          <button
            type="submit"
            disabled={uploading}
          >
            {uploading
              ? "Processing..."
              : "Upload & Process"}
          </button>
        </form>

        {uploadMessage && (
          <p className="success-message">
            {uploadMessage}
          </p>
        )}

        {uploadError && (
          <p className="error-message">
            {uploadError}
          </p>
        )}
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>Common questions</h2>
          <p>
            Try a question against the
            indexed report.
          </p>
        </div>

        <div className="question-grid">
          {COMMON_QUESTIONS.map(
            (item) => (
              <button
                key={item}
                type="button"
                className="question-card"
                disabled={asking}
                onClick={() =>
                  submitQuestion(item)
                }
              >
                {item}
              </button>
            )
          )}
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>Ask AI</h2>
        </div>

        <textarea
          rows="4"
          placeholder="Ask a question about the uploaded report..."
          value={question}
          onChange={(event) =>
            setQuestion(
              event.target.value
            )
          }
        />

        <button
          type="button"
          className="primary-button"
          disabled={asking}
          onClick={() =>
            submitQuestion()
          }
        >
          {asking
            ? "Investigating..."
            : "Ask AI"}
        </button>

        {askError && (
          <p className="error-message">
            {askError}
          </p>
        )}
      </section>

      {answer && (
        <section className="panel answer-panel">
          <div className="section-heading">
            <h2>Answer</h2>
          </div>

          <div className="answer-text">
            {answer}
          </div>

          {sources.length > 0 && (
            <div className="sources">
              <h3>Evidence</h3>

              {sources.map(
                (source, index) => (
                  <div
                    className="source-card"
                    key={
                      source.chunk_id ||
                      index
                    }
                  >
                    <strong>
                      Source {index + 1}
                    </strong>

                    <span>
                      {source.source_file ||
                        "Unknown file"}
                    </span>

                    {source.sheet && (
                      <span>
                        Sheet:{" "}
                        {source.sheet}
                      </span>
                    )}

                    {source.source_rows && (
                      <span>
                        Rows:{" "}
                        {source.source_rows.join(
                          ", "
                        )}
                      </span>
                    )}

                    {source.transaction_number && (
                      <span>
                        Transaction:{" "}
                        {
                          source.transaction_number
                        }
                      </span>
                    )}

                    <span>
                      Retrieval score:{" "}
                      {source.score.toFixed(
                        4
                      )}
                    </span>
                  </div>
                )
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}

export default App;