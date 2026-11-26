
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import API from "../services/api";

function BudgetTracker() {
  const { tripId } = useParams();
  const navigate = useNavigate();

  const [trip, setTrip] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchBudgetData = async () => {
      try {
        setLoading(true);

        const [tripResponse, itineraryResponse] = await Promise.all([
          API.get(`/trips/${tripId}`),
          API.get(`/trips/${tripId}/itinerary`),
        ]);

        setTrip(tripResponse.data.trip);
        setActivities(itineraryResponse.data.itinerary || []);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          "Unable to load budget information."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchBudgetData();
  }, [tripId]);

  if (loading) {
    return <h2>Loading budget tracker...</h2>;
  }

  if (error) {
    return <p style={{ color: "red" }}>{error}</p>;
  }

  if (!trip) return null;

  // Calculate total trip budget
  const totalBudget = Number(trip.budget) || 0;

  // Calculate total estimated itinerary expenses
  const totalExpenses = activities.reduce(
    (total, activity) =>
      total + (Number(activity.estimated_cost) || 0),
    0
  );

  // Calculate remaining budget
  const remainingBudget = totalBudget - totalExpenses;

  // Calculate budget usage percentage
  const budgetPercentage =
    totalBudget > 0
      ? (totalExpenses / totalBudget) * 100
      : 0;

  // Group expenses by day
  const dailyExpenses = activities.reduce((groups, activity) => {
    const day = activity.day;

    groups[day] =
      (groups[day] || 0) +
      (Number(activity.estimated_cost) || 0);

    return groups;
  }, {});

  return (
    <div
      style={{
        padding: "30px",
        maxWidth: "1000px",
        margin: "auto",
      }}
    >
      <button onClick={() => navigate(`/trips/${tripId}`)}>
         ← Back to Trip
      </button>

      <h1>Shared Budget Tracker</h1>
      <h2>{trip.title}</h2>

      {/* Budget Summary */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "15px",
          marginTop: "25px",
        }}
      >
        <div style={cardStyle}>
          <h3>Total Budget</h3>
          <h2>₹{totalBudget.toLocaleString("en-IN")}</h2>
        </div>

        <div style={cardStyle}>
          <h3>Estimated Expenses</h3>
          <h2>₹{totalExpenses.toLocaleString("en-IN")}</h2>
        </div>

        <div style={cardStyle}>
          <h3>Remaining Budget</h3>
          <h2
            style={{
              color: remainingBudget < 0 ? "red" : "green",
            }}
          >
            ₹{remainingBudget.toLocaleString("en-IN")}
          </h2>
        </div>
      </div>

      {/* Budget Usage */}
      <div style={cardStyle}>
        <h2>Budget Usage</h2>

        <div
          style={{
            width: "100%",
            height: "18px",
            background: "#e5e7eb",
            borderRadius: "10px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${Math.min(budgetPercentage, 100)}%`,
              height: "100%",
              background:
                budgetPercentage > 100 ? "red" : "#16a34a",
              transition: "width 0.3s ease",
            }}
          />
        </div>

        <p>
          {budgetPercentage.toFixed(2)}% of the trip budget used
        </p>

        {remainingBudget < 0 && (
          <p style={{ color: "red" }}>
            Warning: Your estimated expenses exceed the trip budget!
          </p>
        )}
      </div>

      {/* Daily Expenses */}
      <div style={cardStyle}>
        <h2>Daily Expense Breakdown</h2>

        {Object.keys(dailyExpenses).length === 0 ? (
          <p>No itinerary expenses available yet.</p>
        ) : (
          Object.keys(dailyExpenses)
            .sort((a, b) => Number(a) - Number(b))
            .map((day) => (
              <div
                key={day}
                style={{
                  padding: "12px",
                  borderBottom: "1px solid #ddd",
                }}
              >
                <strong>Day {day}</strong>
                <span style={{ float: "right" }}>
                  ₹{dailyExpenses[day].toLocaleString("en-IN")}
                </span>
              </div>
            ))
        )}
      </div>

      {/* Activity Expense Details */}
      <div style={cardStyle}>
        <h2>Expense Details</h2>

        {activities.length === 0 ? (
          <p>No activities available.</p>
        ) : (
          activities.map((activity) => (
            <div
              key={activity.id}
              style={{
                padding: "12px",
                borderBottom: "1px solid #ddd",
              }}
            >
              <strong>{activity.activity}</strong>
              <p>Day: {activity.day}</p>
              <p>Location: {activity.location}</p>
              <p>
                Estimated Cost: ₹
                {Number(activity.estimated_cost).toLocaleString("en-IN")}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

const cardStyle = {
  border: "1px solid #ddd",
  borderRadius: "10px",
  padding: "20px",
  marginBottom: "20px",
};

export default BudgetTracker;
