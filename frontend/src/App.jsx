
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import TripDetails from "./pages/TripDetails";
import AITravelPlan from "./pages/AITravelPlan";
import CreateTrip from "./pages/CreateTrip";
import JoinTrip from "./pages/JoinTrip";
import Itinerary from "./pages/Itinerary";
import BudgetTracker from "./pages/BudgetTracker";
import ExpenseTracker from "./pages/ExpenseTracker";
import GroupChat from "./pages/GroupChat";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />

        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/create-trip" element={<CreateTrip />} />
        <Route path="/trips/:tripId" element={<TripDetails />} />
        <Route path="/trips/:tripId/budget" element={<BudgetTracker />} />
        <Route path="/trips/:tripId/ai-plan" element={<AITravelPlan />} />
        <Route path="/trips/:tripId/itinerary" element={<Itinerary />} />
        <Route path="/join/:inviteCode" element={<JoinTrip />} />
        <Route path="/trips/:tripId/expenses" element={<ExpenseTracker />} />
        <Route path="/trips/:tripId/chat" element={<GroupChat />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
