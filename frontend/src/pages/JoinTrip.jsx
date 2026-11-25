
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import API from "../services/api";

function JoinTrip() {
  const { inviteCode } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [alreadyMember, setAlreadyMember] = useState(false);
  const [requiresLogin, setRequiresLogin] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const joinTrip = async () => {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setRequiresLogin(true);
        setLoading(false);
        return;
      }

      try {
        const response = await API.post("/trips/join", {
          invite_code: inviteCode,
        });

        if (!cancelled) {
          setMessage(response.data.message);
        }
      } catch (err) {
        if (cancelled) return;

        const status = err.response?.status;
        const detail = err.response?.data?.detail;

        if (status === 409) {
          setAlreadyMember(true);
          setMessage("You're already a member of this trip!");
        } else if (status === 404) {
          setError("This invitation code is invalid or inactive.");
        } else if (status === 400 && detail === "You are already the trip creator") {
          setAlreadyMember(true);
          setMessage("You're the creator of this trip!");
        } else {
          setError(detail || "Unable to join this trip. Please try again.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    joinTrip();

    return () => {
      cancelled = true;
    };
  }, [inviteCode]);

  return (
    <div className="dashboard-container">
      <main className="dashboard-content">
        <div className="trip-card">
          <h1>Join Trip</h1>

          <p>Invitation Code: {inviteCode}</p>

          {loading && <p>Joining your trip...</p>}

          {requiresLogin && (
            <>
              <p>Please log in before joining this trip.</p>

              <button
                onClick={() =>
                  navigate("/login", {
                    state: { from: `/join/${inviteCode}` },
                  })
                }
              >
                Login to Join
              </button>
            </>
          )}

          {message && (
            <div>
              <p className="success-message">{message}</p>

              <button onClick={() => navigate("/dashboard")}>
                {alreadyMember ? "Go to Dashboard" : "View My Trips"}
              </button>
            </div>
          )}

          {error && (
            <div>
              <p className="error-message">{error}</p>

              <button onClick={() => navigate("/dashboard")}>
                Back to Dashboard
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default JoinTrip;
