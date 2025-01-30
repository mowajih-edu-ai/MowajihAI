import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "../store/store";
import { setQuestions, saveAnswer, incrementCurrentIndex, setRecommendations } from "../store/questionnaireSlice";

import questionsData from "../data/questions.json";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export const useQuestionnaire = () => {
    const dispatch = useDispatch();
    const navigate = useNavigate();
  
    const { questions, currentIndex, answers } = useSelector((state: RootState) => state.questionnaire);
    const [userResponse, setUserResponse] = useState("");
  
    useEffect(() => {
      dispatch(setQuestions(questionsData));
    }, [dispatch]);
  
    const handleNext = () => {
      if (!userResponse) return;
  
      const currentQuestion = questions[currentIndex];
  
      dispatch(saveAnswer({ id: currentQuestion.id, question: currentQuestion.question, answer: userResponse }));
      setUserResponse("");
  
      if (currentIndex < questions.length - 1) {
        dispatch(incrementCurrentIndex());
      } else {
        sendToBackend();
      }
    };
  
    const sendToBackend = async () => {
      try {
        const response = await axios.post("http://localhost:5000/recommend", { answers });
  
        if (response.data?.recommendations?.length) {
          dispatch(setRecommendations(response.data.recommendations));
          navigate("/summary");
        } else {
          console.error("No recommendations returned from backend.");
        }
      } catch (error) {
        console.error("Error submitting answers", error);
      }
    };
  
    return { questions, currentIndex, userResponse, setUserResponse, handleNext };
  };
  