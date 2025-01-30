import React from 'react'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Questionnaire from './pages/Questionnaire';
import QuestionnaireLayout from './layouts/questionnaire_layout/QuestionnaireLayout';
import Summary from './pages/Summary';
import './App.css'


const App: React.FC = () => {

  return (
      <Router>
      <Routes>
        <Route path="/*" element={<QuestionnaireLayout />}>
          <Route index element={<Questionnaire />} />
          <Route path="summary" element={<Summary />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
