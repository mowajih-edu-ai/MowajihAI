import { useQuestionnaire } from "../hooks/useQuestionnaire";

const Questionnaire = () => {
  const { questions, currentIndex, userResponse, setUserResponse, handleNext } = useQuestionnaire();

  if (!questions || questions.length === 0 || currentIndex >= questions.length) {
    return <p className="text-center text-white text-lg">Loading...</p>;
  }

  const currentQuestion = questions[currentIndex];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-blue-900">
      <div className="bg-white text-blue-900 p-6 rounded-lg shadow-lg w-full max-w-md">
        <h2 className="text-2xl font-bold text-center">{currentQuestion?.question || "No more questions available"}</h2>

        {currentQuestion?.type === "text" && (
          <input
            type="text"
            value={userResponse}
            onChange={(e) => setUserResponse(e.target.value)}
            className="w-full border border-gray-300 p-3 rounded mt-4 bg-blue-100 text-blue-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your response..."
          />
        )}

        {currentQuestion?.type === "number" && (
          <input
            type="number"
            value={userResponse}
            onChange={(e) => setUserResponse(e.target.value)}
            className="w-full border border-gray-300 p-3 rounded mt-4 bg-blue-100 text-blue-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter a number..."
          />
        )}

        {currentQuestion?.type === "dropdown" && currentQuestion.options?.length && (
          <select
            value={userResponse}
            onChange={(e) => setUserResponse(e.target.value)}
            className="w-full border border-gray-300 p-3 rounded mt-4 bg-blue-100 text-blue-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select an option</option>
            {currentQuestion.options.map((option: string, index: number) => (
              <option key={index} value={option}>
                {option}
              </option>
            ))}
          </select>
        )}

        <button
          onClick={handleNext}
          className={`w-full mt-6 py-3 text-lg font-semibold rounded transition ${
            userResponse
              ? "bg-blue-600 hover:bg-blue-700 text-white"
              : "bg-gray-400 text-gray-700 cursor-not-allowed"
          }`}
          disabled={!userResponse}
        >
          {currentIndex === questions.length - 1 ? "Submit" : "Next"}
        </button>
      </div>
    </div>
  );
};

export default Questionnaire;
