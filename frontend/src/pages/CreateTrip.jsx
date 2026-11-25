
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";

function CreateTrip() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    title: "",
    destination: "",
    start_date: "",
    end_date: "",
    budget: "",
    description: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const payload = {
        ...formData,
        budget: Number(formData.budget),
      };

      const response = await API.post("/trips/", payload);
const createdTrip = response.data;

if (createdTrip.trip_id) {
  navigate(`/trips/${createdTrip.trip_id}`);
} else {
  setError("Trip created, but trip ID was not returned.");
}
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to create trip. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h2>Create New Trip</h2>
        <button onClick={() => navigate("/dashboard")}>
          Back
        </button>
      </header>

      <main className="dashboard-content">
        <form className="auth-card" onSubmit={handleSubmit}>
          <h1>Plan Your Adventure</h1>
          <p>Enter your trip details below.</p>

          {error && <p className="error-message">{error}</p>}

          <label>Trip Title</label>
          <input
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Bangalore Weekend Trip"
            required
          />

          <label>Destination</label>
          <input
            name="destination"
            value={formData.destination}
            onChange={handleChange}
            placeholder="Bangalore, India"
            required
          />

          <label>Start Date</label>
          <input
            type="date"
            name="start_date"
            value={formData.start_date}
            onChange={handleChange}
            required
          />

          <label>End Date</label>
          <input
            type="date"
            name="end_date"
            value={formData.end_date}
            onChange={handleChange}
            required
          />

          <label>Total Budget (₹)</label>
          <input
            type="number"
            name="budget"
            value={formData.budget}
            onChange={handleChange}
            min="1"
            placeholder="15000"
            required
          />

          <label>Description</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Describe your trip..."
            rows="4"
          />

          <button type="submit" disabled={loading}>
            {loading ? "Creating Trip..." : "Create Trip"}
          </button>
        </form>
      </main>
    </div>
  );
}

export default CreateTrip;
