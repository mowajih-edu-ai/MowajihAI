import { NavLink, Outlet } from "react-router-dom";

const QuestionnaireLayout = () => {
  return (
    <div className="flex h-screen">

      <aside className="w-64 bg-gray-800 text-white p-6">
        <h2 className="text-xl font-bold mb-6">Navigation</h2>
        <nav className="flex flex-col gap-4">
          <NavLink to="/" className={({ isActive }) => isActive ? "text-blue-400 font-semibold" : "text-white"}>
            Questionnaire
          </NavLink>
          <NavLink to="/summary" className={({ isActive }) => isActive ? "text-blue-400 font-semibold" : "text-white"}>
            Summary
          </NavLink>
        </nav>
      </aside>

      <main className="flex-1 p-6 bg-gray-100 overflow-auto h-full">
        <Outlet /> 
      </main>
    </div>
  );
};

export default QuestionnaireLayout;
