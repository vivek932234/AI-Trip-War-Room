
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import { logoutUser } from "../services/authService";

function Dashboard() {
  const navigate = useNavigate();

  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [inviteInput, setInviteInput] = useState("");
  const [joining, setJoining] = useState(false);
  const [joinError, setJoinError] = useState("");
  const [joinSuccess, setJoinSuccess] = useState("");
  const [showJoinForm, setShowJoinForm] = useState(false);

  // FETCH USER TRIPS
  const fetchTrips = async () => {
    try {
      const response = await API.get("/trips/");
      const data = response.data;

      setTrips(Array.isArray(data) ? data : data.trips || []);
      setError("");
    } catch (err) {
      if (err.response?.status === 401) {
        logoutUser();
        navigate("/login");
        return;
      }

      setError("Unable to load trips. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrips();
  }, [navigate]);

  // EXTRACT INVITATION CODE FROM LINK OR INPUT
  const extractInviteCode = (value) => {
    const cleanedValue = value.trim();

    if (!cleanedValue) return "";

    try {
      const url = new URL(cleanedValue);
      const pathParts = url.pathname.split("/").filter(Boolean);

      return pathParts[pathParts.length - 1] || "";
    } catch {
      return cleanedValue;
    }
  };

  // JOIN TRIP
  const handleJoinTrip = async (e) => {
    e.preventDefault();

    setJoinError("");
    setJoinSuccess("");

    const inviteCode = extractInviteCode(inviteInput);

    if (!inviteCode) {
      setJoinError("Please enter an invitation link or code.");
      return;
    }

    try {
      setJoining(true);

      const response = await API.post("/trips/join", {
        invite_code: inviteCode
      });

      setJoinSuccess(
        response.data.message || "You joined the trip successfully!"
      );

      setInviteInput("");

      // Refresh dashboard trips
      await fetchTrips();

    } catch (err) {
      setJoinError(
        err.response?.data?.detail ||
        "Unable to join trip. Please check your invitation."
      );
    } finally {
      setJoining(false);
    }
  };

  // LOGOUT
  const handleLogout = () => {
    logoutUser();
    navigate("/login");
  };

  return (
    <div className="dashboard-container">

      {/* HEADER */}
      <header className="dashboard-header">
        <h2>Airbnb Trip War Room</h2>
        <button onClick={handleLogout}>Logout</button>
      </header>

      <main className="dashboard-content">

        {/* DASHBOARD TITLE */}
        <div className="dashboard-title-row">
          <div>
            <h1>My Trips</h1>
            <p>
              Plan, collaborate and explore your next adventure.
            </p>
          </div>

          <button onClick={() => navigate("/create-trip")}>
            + Create New Trip
          </button>
        </div>

{/* JOIN EXISTING TRIP */}

<div className="join-trip-panel">

  <div className="join-trip-heading">
    <div>
      <h2>🔗 Join an Existing Trip</h2>
      <p>Have an invitation from your friend?</p>
    </div>

    <button
      type="button"
      onClick={() => {
        setShowJoinForm((previous) => !previous);
        setJoinError("");
        setJoinSuccess("");
      }}
    >
      {showJoinForm ? "Close" : "+ Join a Trip"}
    </button>
  </div>

  {showJoinForm && (
    <div className="join-trip-content">

      <p>
        Paste your invitation link or enter your invitation code.
      </p>

      <form
        onSubmit={handleJoinTrip}
        className="join-trip-form"
      >
        <input
          type="text"
          value={inviteInput}
          onChange={(e) => setInviteInput(e.target.value)}
          placeholder="Paste invitation link or enter code"
          disabled={joining}
        />

        <button
          type="submit"
          disabled={joining || !inviteInput.trim()}
        >
          {joining ? "Joining..." : "Join Trip"}
        </button>
      </form>

      {joinError && (
        <p className="error-message">{joinError}</p>
      )}

      {joinSuccess && (
        <p className="success-message">{joinSuccess}</p>
      )}

    </div>
  )}

</div>

        {/* LOADING */}
        {loading && <p>Loading your trips...</p>}

        {error && <p className="error-message">{error}</p>}

        {/* EMPTY STATE */}
        {!loading && !error && trips.length === 0 && (
          <div className="empty-state">
            <h2>No trips yet!</h2>
            <p>
              Create a new trip or join one using an invitation.
            </p>
          </div>
        )}

        {/* USER TRIPS */}
        <div className="trip-grid">
          {trips.map((trip) => (
            <div
             className="trip-card dashboard-trip-card"
              key={trip._id || trip.id}
              onClick={() =>
                navigate(`/trips/${trip._id || trip.id}`)
              }
              style={{ cursor: "pointer" }}
            >
              <h2>{trip.title}</h2>
              <p>📍 {trip.destination}</p>
              <p>💰 Budget: ₹{trip.budget}</p>
              <p>
                📅 {trip.start_date} to {trip.end_date}
              </p>
            </div>
          ))}
        </div>

      </main>
    </div>
  );
}

export default Dashboard;
