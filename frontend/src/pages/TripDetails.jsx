
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import API from "../services/api";

function TripDetails() {
  const { tripId } = useParams();
  const navigate = useNavigate();

  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [myRole, setMyRole] = useState("");
  // Edit trip states
const [showEditForm, setShowEditForm] = useState(false);
const [editLoading, setEditLoading] = useState(false);
const [editError, setEditError] = useState("");
const [editSuccess, setEditSuccess] = useState("");

const [editData, setEditData] = useState({
  title: "",
  destination: "",
  start_date: "",
  end_date: "",
  budget: "",
  description: ""
});

  // Invitation states
  const [role, setRole] = useState("viewer");
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteData, setInviteData] = useState(null);
  const [inviteError, setInviteError] = useState("");
  const [copied, setCopied] = useState(false);

useEffect(() => {
  const fetchTripDetails = async () => {
    try {
      // Fetch trip details
      const tripResponse = await API.get(`/trips/${tripId}`);
      setTrip(tripResponse.data.trip);

      // Fetch logged-in user's role in this trip
      const roleResponse = await API.get(
        `/trips/${tripId}/my-role`
      );

      setMyRole(
        roleResponse.data.role ||
        roleResponse.data.my_role ||
        ""
      );

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load trip details."
      );
    } finally {
      setLoading(false);
    }
  };

  fetchTripDetails();
}, [tripId]);


// Open edit form with existing trip details
const openEditForm = () => {
  setEditData({
    title: trip.title || "",
    destination: trip.destination || "",
    start_date: trip.start_date || "",
    end_date: trip.end_date || "",
    budget: trip.budget ?? "",
    description: trip.description || ""
  });

  setEditError("");
  setEditSuccess("");
  setShowEditForm(true);
};

// Handle form input changes
const handleEditChange = (e) => {
  const { name, value } = e.target;

  setEditData((previous) => ({
    ...previous,
    [name]: value
  }));
};

// Save updated trip details
const updateTripDetails = async (e) => {
  e.preventDefault();

  setEditLoading(true);
  setEditError("");
  setEditSuccess("");

  if (editData.end_date < editData.start_date) {
    setEditError("End date cannot be before start date.");
    setEditLoading(false);
    return;
  }

  if (
    editData.budget === "" ||
    !Number.isFinite(Number(editData.budget)) ||
    Number(editData.budget) < 0
  ) {
    setEditError("Please enter a valid budget.");
    setEditLoading(false);
    return;
  }

  try {
    await API.patch(`/trips/${tripId}`, {
      ...editData,
      budget: Number(editData.budget)
    });

    const response = await API.get(`/trips/${tripId}`);

    setTrip(response.data.trip);
    setShowEditForm(false);
    setEditSuccess("Trip details updated successfully!");

  } catch (err) {
    setEditError(
      err.response?.data?.detail ||
      "Unable to update trip details."
    );
  } finally {
    setEditLoading(false);
  }
};


  // Generate invitation
  const generateInvite = async () => {
    setInviteLoading(true);
    setInviteError("");
    setInviteData(null);
    setCopied(false);

    try {
      const response = await API.post(
        `/trips/${tripId}/invite`,
        { role }
      );

      setInviteData(response.data);
    } catch (err) {
      setInviteError(
        err.response?.data?.detail ||
        "Unable to generate invitation."
      );
    } finally {
      setInviteLoading(false);
    }
  };

  // Copy invitation link
  const copyInviteLink = async () => {
    try {
      await navigator.clipboard.writeText(inviteData.invite_link);
      setCopied(true);
    } catch {
      setInviteError("Unable to copy link. Please copy it manually.");
    }
  };

  if (loading) return <h2>Loading trip details...</h2>;

  if (error) {
    return (
      <div className="dashboard-content">
        <p className="error-message">{error}</p>
        <button onClick={() => navigate("/dashboard")}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!trip) return null;

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h2>Airbnb Trip War Room</h2>
        <button onClick={() => navigate("/dashboard")}>
          Back to Trips
        </button>
      </header>

      <main className="dashboard-content">

<div className="trip-welcome-section">

  <h1>
    Hi, {
      myRole === "viewer"
        ? "Viewer"
        : myRole === "planner"
        ? "Planner"
        : ["leader", "trip_leader", "owner", "creator"].includes(
            myRole.toLowerCase()
          )
        ? "Trip Leader"
        : "Welcome"
    }! 👋
  </h1>

  <p>
    Welcome to your {trip.title}.
    Your role helps determine what you can do in this trip.
  </p>

  <div className={`my-role-badge ${myRole.toLowerCase().replace("_", "-")}`}>
   Your Role: {
  myRole.toLowerCase() === "leader"
    ? "Trip Leader"
    : myRole.replace("_", " ")
}
  </div>

  <h2 className="trip-details-title">{trip.title}</h2>
  <p>📍 {trip.destination}</p>

</div>


{/* Edit Trip Details - Trip Leader Only */}
{myRole === "leader" && (
  <div className="trip-card">
    <h2>⚙️ Manage Trip Details</h2>

    <p>
      Update your trip title, destination, dates,
      budget and description.
    </p>

    {!showEditForm && (
      <button onClick={openEditForm}>
        Edit Trip Details
      </button>
    )}

    {showEditForm && (
     <form className="edit-trip-form" onSubmit={updateTripDetails}>

        <div className="edit-trip-field">
          <label>Trip Title</label>
        <input
          type="text"
          name="title"
          value={editData.title}
          onChange={handleEditChange}
          required
        />
        </div>
         <div className="edit-trip-field">
        <label>Destination</label>
        <input
          type="text"
          name="destination"
          value={editData.destination}
          onChange={handleEditChange}
          required
        /></div>

        <div className="edit-trip-field">
        <label>Start Date</label>
        <input
          type="date"
          name="start_date"
          value={editData.start_date}
          onChange={handleEditChange}
          required
        /></div>
        <div className="edit-trip-field">
        <label>End Date</label>
        <input
          type="date"
          name="end_date"
          value={editData.end_date}
          onChange={handleEditChange}
          required
        /></div>
         <div className="edit-trip-field">
        <label>Budget (₹)</label>
        <input
          type="number"
          name="budget"
          min="0"
          step="0.01"
          value={editData.budget}
          onChange={handleEditChange}
          required
        /></div>
         <div className="edit-trip-field">
        <label>Description</label>
        <textarea
          name="description"
          value={editData.description}
          onChange={handleEditChange}
          rows="3"
        /></div>

        {editError && (
  <p className="error-message">{editError}</p>
)}

<div className="edit-trip-actions">
  <button type="submit" disabled={editLoading}>
    {editLoading ? "Saving..." : "Save Changes"}
  </button>

  <button
    type="button"
    className="button-secondary"
    onClick={() => setShowEditForm(false)}
    disabled={editLoading}
  >
    Cancel
  </button>
</div>
      </form>
    )}

    {editSuccess && (
      <p className="success-message">{editSuccess}</p>
    )}
  </div>
)}


        {/* Trip Overview */}
        <div className="trip-card">
          <h2>Trip Overview</h2>
          <p>💰 Budget: ₹{trip.budget}</p>
          <p>📅 Start Date: {trip.start_date}</p>
          <p>📅 End Date: {trip.end_date}</p>
          <p>📝 {trip.description || "No description available."}</p>
        </div>

        {/* Trip Itinerary */}
<div className="trip-card">
  <h2>📅 Trip Itinerary</h2>

  <p>
    View daily activities, timings, locations and estimated costs
    planned for this trip.
  </p>

  <button
    onClick={() =>
      navigate(`/trips/${tripId}/itinerary`)
    }
  >
    View Trip Itinerary
  </button>
</div>


{/* Shared Budget Tracker */}
<div className="trip-card">
  <h2>💰 Shared Budget Tracker</h2>

  <p>
    Track your total trip budget, estimated expenses
    and remaining balance.
  </p>

  <button
    onClick={() =>
      navigate(`/trips/${tripId}/budget`)
    }
  >
    View Budget Tracker
  </button>
</div>


{/* GROUP TRIP CHAT */}
<div className="trip-card">
  <h2>💬 Group Trip Chat</h2>

  <p>
    Chat with your trip members in real time.
    Share updates, discuss plans and coordinate your journey.
  </p>

  <button
    onClick={() =>
      navigate(`/trips/${tripId}/chat`)
    }
  >
    Open Group Chat
  </button>
</div>



{/* Invite Members */}
<div className="trip-card invite-members-card">
  <h2>👥 Invite Members</h2>

  <p>
    Invite your friends to collaborate on this trip.
  </p>

  <div className="invite-role-field">
    <label htmlFor="memberRole">
      Select Member Role
    </label>

    <select
      id="memberRole"
      className="invite-role-select"
      value={role}
      onChange={(e) => setRole(e.target.value)}
    >
      <option value="viewer">Viewer</option>
      <option value="planner">Planner</option>
    </select>

    <small>
      {role === "viewer"
        ? "View trip details and participate in group discussions."
        : "Help manage and update the shared trip itinerary."}
    </small>
  </div>

  <button
    className="invite-generate-btn"
    onClick={generateInvite}
    disabled={inviteLoading}
  >
    {inviteLoading ? "Generating..." : "Generate Invite Link"}
  </button>

  {inviteError && (
    <p className="error-message">{inviteError}</p>
  )}

  {inviteData && (
    <div className="invite-result-card">

      <div className="invite-success-heading">
        <span className="invite-success-icon">✓</span>
        <div>
          <h3>Invitation Generated!</h3>
          <p>Your invitation link is ready to share.</p>
        </div>
      </div>

      <div className="invite-details-row">
        <div className="invite-detail-item">
          <span>Invitation Code</span>
          <strong>{inviteData.invite_code}</strong>
        </div>

        <div className="invite-detail-item">
          <span>Assigned Role</span>
          <strong className={`invite-role-badge ${inviteData.role}`}>
            {inviteData.role}
          </strong>
        </div>
      </div>

      <label className="invite-link-label">
        Invitation Link
      </label>

      <div className="invite-link-row">
        <input
          className="invite-link-input"
          type="text"
          value={inviteData.invite_link}
          readOnly
          onFocus={(e) => e.target.select()}
        />

        <button
          className="invite-copy-btn"
          onClick={copyInviteLink}
          type="button"
        >
          {copied ? "✓ Copied!" : "Copy Link"}
        </button>
      </div>

      <small className="invite-link-hint">
        Share this link with the person you want to invite.
      </small>

    </div>
  )}
</div>

        {/* AI Travel Concierge */}
        <div className="trip-card ai-plan-card">
          <h2>✨ AI Travel Concierge</h2>
          <p>
            Let AI create a personalized travel itinerary
            based on your destination, dates and budget.
          </p>

          <button
            onClick={() =>
              navigate(`/trips/${tripId}/ai-plan`)
            }
          >
            Generate AI Travel Plan
          </button>
        </div>
      </main>
    </div>
  );
}

export default TripDetails;
