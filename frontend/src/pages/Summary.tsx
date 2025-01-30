import { useSelector, useDispatch } from "react-redux";
import { RootState } from "../store/store";
import { useNavigate } from "react-router-dom";
import { resetQuestionnaire } from "../store/questionnaireSlice";

const Summary = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { answers, recommendations } = useSelector((state: RootState) => state.questionnaire);

  const handleRestart = () => {
    dispatch(resetQuestionnaire());
    navigate("/");
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-blue-900 p-6">
      <div className="bg-white text-blue-900 p-6 rounded-lg shadow-lg w-full max-w-2xl">
        <h2 className="text-2xl font-bold text-center">Summary</h2>

        <div className="mt-6">
          <h3 className="text-lg font-semibold">Your Answers</h3>
          {answers.length > 0 ? (
            <ul className="mt-4 space-y-3">
              {answers.map((item, index) => (
                <li key={index} className="border border-gray-300 p-4 rounded-lg bg-blue-100 text-blue-900">
                  <p className="font-semibold">{item.question}</p>
                  <p className="text-blue-800">{item.answer}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-700 mt-2">No answers available.</p>
          )}
        </div>

        <div className="mt-6">
          <h3 className="text-lg font-semibold">Recommended Programs</h3>
          {recommendations.length > 0 ? (
            <ul className="mt-4 space-y-3">
              {recommendations.map((program, index) => (
                <li key={index} className="border border-gray-300 p-4 rounded-lg bg-blue-100 text-blue-900">
                  <h3 className="text-lg font-semibold">{program.title}</h3>
                  <p className="text-blue-800">{program.description}</p>
                  <p><strong>Opportunities:</strong> {program.opportunities?.join(", ") || "Not specified"}</p>
                  <p><strong>Access Conditions:</strong> {program.access_conditions || "Not specified"}</p>
                  <p><strong>Relevance Score:</strong> {program.score?.toFixed(2) || "N/A"}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-700 mt-2">No recommendations available.</p>
          )}
        </div>

        <button
          onClick={handleRestart}
          className="w-full mt-6 py-3 text-lg font-semibold rounded bg-blue-600 hover:bg-blue-700 text-white transition"
        >
          Restart
        </button>
      </div>
    </div>
  );
};

export default Summary;
