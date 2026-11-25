
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import API from "../services/api";

const emptyForm = {
  day: 1,
  activity: "",
  location: "",
  activity_date: "",
  start_time: "",
  end_time: "",
  estimated_cost: 0,
  notes: "",
};

function Itinerary() {
  const { tripId } = useParams();
  const navigate = useNavigate();

  const [itinerary, setItinerary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [canEdit, setCanEdit] = useState(false);

  const [formData, setFormData] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);

  // FETCH ITINERARY AND USER ROLE
  const fetchItinerary = async (showLoader = true) => {
    try {
      if (showLoader) setLoading(true);

      const response = await API.get(
        `/trips/${tripId}/itinerary`
      );

      setItinerary(response.data.itinerary || []);
      setError("");

      try {
        const roleResponse = await API.get(
          `/trips/${tripId}/my-role`
        );

        setCanEdit(roleResponse.data.can_edit);
      } catch (roleError) {
        setCanEdit(false);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load itinerary."
      );
    } finally {
      if (showLoader) setLoading(false);
    }
  };

  useEffect(() => {
    fetchItinerary();
  }, [tripId]);

  // HANDLE FORM INPUTS
  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // RESET FORM
  const resetForm = () => {
    setFormData(emptyForm);
    setEditingId(null);
  };

  // ADD OR UPDATE ACTIVITY
  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setSubmitting(true);
      setError("");
      setSuccess("");

      const payload = {
        ...formData,
        day: Number(formData.day),
        estimated_cost: Number(formData.estimated_cost),
        start_time: formData.start_time || null,
        end_time: formData.end_time || null,
        notes: formData.notes || null,
      };

      if (editingId) {
        await API.patch(
          `/trips/${tripId}/itinerary/${editingId}`,
          payload
        );

        setSuccess("Activity updated successfully!");
      } else {
        await API.post(
          `/trips/${tripId}/itinerary`,
          payload
        );

        setSuccess("Activity added successfully!");
      }

      resetForm();
      await fetchItinerary(false);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to save activity."
      );
    } finally {
      setSubmitting(false);
    }
  };

  // LOAD ACTIVITY INTO EDIT FORM
  const handleEdit = (activity) => {
    setEditingId(activity.id);

    setFormData({
      day: activity.day,
      activity: activity.activity,
      location: activity.location,
      activity_date: activity.activity_date,
      start_time: activity.start_time?.slice(0, 5) || "",
      end_time: activity.end_time?.slice(0, 5) || "",
      estimated_cost: activity.estimated_cost,
      notes: activity.notes || "",
    });

    setError("");
    setSuccess("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // DELETE ACTIVITY
  const handleDelete = async (activityId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this activity?"
    );

    if (!confirmed) return;

    try {
      setError("");
      setSuccess("");

      await API.delete(
        `/trips/${tripId}/itinerary/${activityId}`
      );

      setSuccess("Activity deleted successfully!");

      if (editingId === activityId) {
        resetForm();
      }

      await fetchItinerary(false);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to delete activity."
      );
    }
  };

  // GROUP ACTIVITIES BY DAY
  const groupedItinerary = itinerary.reduce(
    (groups, activity) => {
      const day = activity.day;

      if (!groups[day]) {
        groups[day] = [];
      }

      groups[day].push(activity);
      return groups;
    },
    {}
  );

  if (loading) {
    return (
      <div className="itinerary-page">
        <h2>Loading itinerary...</h2>
      </div>
    );
  }

  return (
    <div className="itinerary-page">

      {/* HEADER */}
      <div className="itinerary-header">
        <button
          type="button"
          onClick={() => navigate(`/trips/${tripId}`)}
        >
          ← Back to Trip
        </button>

        <h1>Trip Itinerary</h1>

        <p>
          Total Activities: <strong>{itinerary.length}</strong>
        </p>
      </div>

      {/* ERROR AND SUCCESS MESSAGES */}
      {error && (
        <p className="error-message">{error}</p>
      )}

      {success && (
        <p className="success-message">{success}</p>
      )}

      {/* ADD / EDIT ACTIVITY FORM */}
      {canEdit && (
        <div className="itinerary-form-panel">

          <h2>
            {editingId ? "Edit Activity" : "Add New Activity"}
          </h2>

          <form
            onSubmit={handleSubmit}
            className="itinerary-form"
          >

            <div className="form-field">
              <label htmlFor="day">Day Number</label>
              <input
                className="form-field-input"
                id="day"
                type="number"
                name="day"
                min="1"
                value={formData.day}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="activity">Activity Name</label>
              <input
                className="form-field-input"
                id="activity"
                type="text"
                name="activity"
                value={formData.activity}
                onChange={handleChange}
                placeholder="e.g. Visit Mysore Palace"
                minLength="3"
                maxLength="200"
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="location">Location</label>
              <input
                className="form-field-input"
                id="location"
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="Enter location"
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="activity_date">Activity Date</label>
              <input
                className="form-field-input"
                id="activity_date"
                type="date"
                name="activity_date"
                value={formData.activity_date}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="start_time">Start Time</label>
              <input
                className="form-field-input"
                id="start_time"
                type="time"
                name="start_time"
                value={formData.start_time}
                onChange={handleChange}
              />
            </div>

            <div className="form-field">
              <label htmlFor="end_time">End Time</label>
              <input
                className="form-field-input"
                id="end_time"
                type="time"
                name="end_time"
                value={formData.end_time}
                onChange={handleChange}
              />
            </div>

            <div className="form-field">
              <label htmlFor="estimated_cost">
                Estimated Cost (₹)
              </label>
              <input
                className="form-field-input"
                id="estimated_cost"
                type="number"
                name="estimated_cost"
                min="0"
                step="0.01"
                value={formData.estimated_cost}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="notes">Notes</label>
              <textarea
                className="form-field-input"
                id="notes"
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                placeholder="Additional information"
                rows="3"
              />
            </div>

            {/* FORM BUTTONS */}
            <div className="itinerary-form-actions">
              <button type="submit" disabled={submitting}>
                {submitting
                  ? "Saving..."
                  : editingId
                  ? "Update Activity"
                  : "Add Activity"}
              </button>

              {editingId && (
                <button
                  type="button"
                  className="button-secondary"
                  onClick={resetForm}
                >
                  Cancel Edit
                </button>
              )}
            </div>

          </form>
        </div>
      )}

      {/* DISPLAY ACTIVITIES */}
      {itinerary.length === 0 ? (
        <div className="itinerary-empty">
          <h2>No Activities Yet</h2>
          <p>Start planning your trip by adding activities.</p>
        </div>
      ) : (
        Object.keys(groupedItinerary)
          .sort((a, b) => Number(a) - Number(b))
          .map((day) => (
            <div
              key={day}
              className="itinerary-day-card"
            >
              <h2>Day {day}</h2>

              {groupedItinerary[day].map((activity) => (
                <div
                  key={activity.id}
                  className="itinerary-activity-card"
                >
                  <h3>{activity.activity}</h3>

                  <p>
                    <strong>Location:</strong> {activity.location}
                  </p>

                  <p>
                    <strong>Date:</strong> {activity.activity_date}
                  </p>

                  <p>
                    <strong>Time:</strong>{" "}
                    {activity.start_time || "Not specified"}
                    {activity.end_time
                      ? ` - ${activity.end_time}`
                      : ""}
                  </p>

                  <p>
                    <strong>Estimated Cost:</strong>{" "}
                    ₹{activity.estimated_cost}
                  </p>

                  {activity.notes && (
                    <p>
                      <strong>Notes:</strong> {activity.notes}
                    </p>
                  )}

                  {/* EDIT AND DELETE BUTTONS */}
                  {canEdit && (
                    <div className="activity-actions">
                      <button
                        type="button"
                        onClick={() => handleEdit(activity)}
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        className="button-danger"
                        onClick={() => handleDelete(activity.id)}
                      >
                        Delete
                      </button>
                    </div>
                  )}

                </div>
              ))}
            </div>
          ))
      )}

    </div>
  );
}

export default Itinerary;
