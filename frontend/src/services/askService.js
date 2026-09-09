const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";

export async function askQuestion(
  question
) {
  const response = await fetch(
    `${API_BASE_URL}/api/ask`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        question,
      }),
    }
  );

  let data;

  try {
    data = await response.json();
  } catch {
    throw new Error(
      "The backend returned an invalid response."
    );
  }

  if (!response.ok) {
    throw new Error(
      data.detail ||
        "Unable to answer the question."
    );
  }

  return data;
}