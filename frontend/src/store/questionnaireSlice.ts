import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface Question {
  id: number;
  question: string;
  type: string;
  options?: string[];
}

interface Answer {
  id: number;
  question: string;
  answer: string;
}

interface Recommendation {
  title: string;
  description: string;
  opportunities: string[];
  access_conditions: string;
  score: number;
}

interface QuestionnaireState {
  questions: Question[];
  currentIndex: number;
  answers: Answer[];
  recommendations: Recommendation[];
}

const initialState: QuestionnaireState = {
  questions: [],
  currentIndex: 0,
  answers: [],
  recommendations: [],
};

const questionnaireSlice = createSlice({
  name: "questionnaire",
  initialState,
  reducers: {
    setQuestions: (state, action: PayloadAction<Question[]>) => {
      state.questions = action.payload;
    },
    saveAnswer: (state, action: PayloadAction<Answer>) => {
      state.answers.push(action.payload);
    },
    incrementCurrentIndex: (state) => {
      if (state.currentIndex < state.questions.length - 1) {
        state.currentIndex += 1; // ✅ Only increment if there are more questions
      }
    },
    resetQuestionnaire: (state) => {
      state.currentIndex = 0;
      state.answers = [];
      state.recommendations = [];
    },
    setRecommendations: (state, action: PayloadAction<Recommendation[]>) => {
      state.recommendations = action.payload;
    },
  },
});

export const { setQuestions, saveAnswer, incrementCurrentIndex, resetQuestionnaire, setRecommendations } = questionnaireSlice.actions;
export default questionnaireSlice.reducer;
