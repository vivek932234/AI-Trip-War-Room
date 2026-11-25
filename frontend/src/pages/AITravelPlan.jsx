
import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import API from "../services/api";
import AIChat from "./AIChat";

function AITravelPlan() {
  const { tripId } = useParams();
  const navigate = useNavigate();

  const [travelPlan, setTravelPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [itineraryHistory, setItineraryHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const generatePlan = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await API.post(
        `/ai/trips/${tripId}/travel-plan`
      );

      setTravelPlan(response.data.travel_plan);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to generate travel plan. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchItineraryHistory = async () => {
  setHistoryLoading(true);

  try {
    const response = await API.get(
      `/ai/trips/${tripId}/itineraries`
    );

    setItineraryHistory(response.data.itineraries);
  } catch (err) {
    setError(
      err.response?.data?.detail ||
      "Unable to load itinerary history."
    );
  } finally {
    setHistoryLoading(false);
  }
};

const loadItineraryVersion = async (version) => {
  setLoading(true);
  setError("");

  try {
    const response = await API.get(
      `/ai/trips/${tripId}/itineraries/${version}`
    );

    setTravelPlan(response.data.travel_plan);
  } catch (err) {
    setError(
      err.response?.data?.detail ||
      "Unable to load this itinerary version."
    );
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h2>AI Travel Concierge</h2>
        <button onClick={() => navigate(`/trips/${tripId}`)}>
          Back to Trip
        </button>
      </header>

      <main className="dashboard-content">
        <h1>✨ Your AI Travel Plan</h1>
        <p>Generate a personalized itinerary for your trip.</p>
        <div className="trip-card">
  <h2>📚 Saved Itinerary Versions</h2>

  <button
    onClick={fetchItineraryHistory}
    disabled={historyLoading}
  >
    {historyLoading ? "Loading..." : "View Itinerary History"}
  </button>

  {itineraryHistory.map((item) => (
    <div key={item.itinerary_id}>
      <h3>Version {item.version}</h3>

      <p>Destination: {item.destination}</p>

      <button
        onClick={() => loadItineraryVersion(item.version)}
        disabled={loading}
      >
        Open Version {item.version}
      </button>
    </div>
  ))}
</div>

        <button onClick={generatePlan} disabled={loading}>
          {loading ? "Generating..." : "Generate AI Travel Plan"}
        </button>

        {error && <p className="error-message">{error}</p>}

        {travelPlan && (
          <div className="trip-card">
            <h2>{travelPlan.destination}</h2>
            <p>Budget: ₹{travelPlan.budget}</p>

            {travelPlan.days.map((day) => (
              <div key={day.day}>
                <h2>Day {day.day} - {day.date}</h2>

                {day.activities.map((activity, index) => (
                  <div key={index}>
                    <h3>{activity.name}</h3>
                    <p>📍 {activity.location}</p>
                    <p>💰 ₹{activity.estimated_cost}</p>
                    <p>{activity.description}</p>
                  </div>
                ))}
              </div>
            ))}

            <h3>Total Estimated Cost: ₹{travelPlan.total_estimated_cost}</h3>
            <h3>Remaining Budget: ₹{travelPlan.remaining_budget}</h3>

            {travelPlan.over_budget && (
              <p className="error-message">
                Your estimated activities exceed the trip budget!
              </p>
            )}

            <h3>Travel Tips</h3>
            <ul>
              {travelPlan.travel_tips.map((tip, index) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>
        )}
        <AIChat />
      </main>
    </div>
  );
}

export default AITravelPlan;
