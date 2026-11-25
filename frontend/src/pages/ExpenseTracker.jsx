
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import API from "../services/api";
import "./ExpenseTracker.css";

function ExpenseTracker() {
    const { tripId } = useParams();

    const [expenses, setExpenses] = useState([]);
    const [members, setMembers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [settlement, setSettlement] = useState(null);
    const [settlementLoading, setSettlementLoading] = useState(true);

    const [title, setTitle] = useState("");
    const [amount, setAmount] = useState("");
    const [category, setCategory] = useState("food");
    const [paidBy, setPaidBy] = useState("");
    const [splitBetween, setSplitBetween] = useState([]);
    const [notes, setNotes] = useState("");
    const [message, setMessage] = useState("");


// DASHBOARD SUMMARY CALCULATIONS
const totalExpenses = expenses.reduce(
    (total, expense) => total + Number(expense.amount || 0),
    0
);

const totalExpenseCount = expenses.length;

const totalMembers = members.length;


// SETTLEMENT SUMMARY CALCULATIONS

const receivedPayments = (settlement?.settlements || [])
    .filter((item) => item.status === "received")
    .reduce((total, item) => total + Math.round(item.amount * 100), 0) / 100;

const pendingPayments = (settlement?.settlements || [])
    .filter((item) => item.status === "pending")
    .reduce((total, item) => total + Math.round(item.amount * 100), 0) / 100;

const settlementStatus =
    settlement?.settlements?.length > 0 &&
    pendingPayments === 0
        ? "Fully Settled"
        : "Pending";




    // FETCH EXPENSES
    const fetchExpenses = async () => {
        try {
            const response = await API.get(
                `/trips/${tripId}/expenses`
            );

            setExpenses(response.data.expenses);
        } catch (error) {
            console.error("Error fetching expenses:", error);
        }
    };

    // FETCH TRIP MEMBERS
    const fetchMembers = async () => {
        try {
            const response = await API.get(
                `/trips/${tripId}/members`
            );

            setMembers(response.data.members);
        } catch (error) {
            console.error("Error fetching members:", error);
        }
    };


// FETCH EXPENSE SETTLEMENT
const fetchSettlement = async () => {
    try {
        setSettlementLoading(true);

        const response = await API.get(
            `/trips/${tripId}/expenses/settlement`
        );

        setSettlement(response.data);

    } catch (error) {
        console.error("Error fetching settlement:", error);
    } finally {
        setSettlementLoading(false);
    }
};


    // LOAD INITIAL DATA
   useEffect(() => {
    const loadData = async () => {
        setLoading(true);

        await Promise.all([
            fetchExpenses(),
            fetchMembers(),
            fetchSettlement()
        ]);

        setLoading(false);
    };

    loadData();
}, [tripId]);

    // ADD NEW EXPENSE
    const handleAddExpense = async (e) => {
        e.preventDefault();

        setMessage("");

        if (!title.trim()) {
            setMessage("Please enter an expense title.");
            return;
        }

        if (!amount || Number(amount) <= 0) {
            setMessage("Please enter a valid amount.");
            return;
        }

        if (!paidBy) {
            setMessage("Please select who paid.");
            return;
        }

        if (splitBetween.length === 0) {
            setMessage("Please select members to split.");
            return;
        }

        const expenseData = {
            title: title.trim(),
            amount: Number(amount),
            category,
            paid_by: paidBy,
            split_between: splitBetween,
            notes: notes.trim()
        };

        console.log("Expense being submitted:", expenseData);

        try {
            setSaving(true);

            await API.post(
                `/trips/${tripId}/expenses`,
                expenseData
            );

            setMessage("Expense added successfully!");

            // CLEAR FORM
            setTitle("");
            setAmount("");
            setCategory("food");
            setPaidBy("");
            setSplitBetween([]);
            setNotes("");

            // REFRESH EXPENSE LIST
            await fetchExpenses();
            await fetchSettlement();

        } catch (error) {
            console.error("Error adding expense:", error);

            setMessage(
                error.response?.data?.detail ||
                "Failed to add expense."
            );

        } finally {
            setSaving(false);
        }
    };


// MARK PAYMENT AS RECEIVED
const handleMarkReceived = async (payment) => {
    const confirmed = window.confirm(
        `Confirm that you received ₹${payment.amount} from ${payment.from}?`
    );

    if (!confirmed) return;

    try {
        await API.post(
            `/trips/${tripId}/expenses/settlement/received`,
            {
                from: payment.from_id,
                to: payment.to_id,
                amount: payment.amount
            }
        );

        alert("Payment marked as received successfully!");

        await fetchSettlement();

    } catch (error) {
        console.error("Payment confirmation error:", error);

        alert(
            error.response?.data?.detail ||
            "Unable to confirm payment."
        );
    }
};


    return (
        <div className="expense-container">

            <h1>Group Expense Tracker</h1>

            <p>Manage and split your trip expenses with friends.</p>

{/* DASHBOARD SUMMARY */}
<div className="expense-summary">

    <div className="summary-card">
        <span>💰</span>
        <h2>
            ₹{totalExpenses.toLocaleString("en-IN")}
        </h2>
        <p>Total Expenses Amount</p>
    </div>

    <div className="summary-card">
        <span>👥</span>
        <h2>{totalMembers}</h2>
        <p>Trip Members</p>
    </div>

    <div className="summary-card">
        <span>🧾</span>
        <h2>{totalExpenseCount}</h2>
        <p>Total Expense Records</p>
    </div>

</div>


            {/* ADD EXPENSE FORM */}
            <div className="expense-form">

                <h2>Add New Expense</h2>

                <form onSubmit={handleAddExpense}>

                    <label>Expense Title</label>
                    <input
                        type="text"
                        placeholder="e.g. Hotel Booking"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                    />

                    <label>Amount (₹)</label>
                    <input
                        type="number"
                        placeholder="Enter amount"
                        min="0.01"
                        step="0.01"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        required
                    />

                    <label>Category</label>
                    <select
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                    >
                        <option value="hotel">Hotel</option>
                        <option value="food">Food</option>
                        <option value="transport">Transport</option>
                        <option value="shopping">Shopping</option>
                        <option value="activities">Activities</option>
                        <option value="other">Other</option>
                    </select>

                    <label>Paid By</label>
                    <select
                        value={paidBy}
                        onChange={(e) => setPaidBy(e.target.value)}
                        required
                    >
                        <option value="">Select member</option>

                        {members.map((member) => (
                            <option
                                key={member.user_id}
                                value={member.user_id}
                            >
                                {member.full_name}
                            </option>
                        ))}
                    </select>

<label className="split-label">Split Between</label>

<div className="split-members">
    {members.map((member) => (
        <label
            className="split-member"
            key={member.user_id}
        >
            <input
                type="checkbox"
                checked={splitBetween.includes(member.user_id)}
                onChange={(e) => {
                    if (e.target.checked) {
                        setSplitBetween((previous) => [
                            ...previous,
                            member.user_id
                        ]);
                    } else {
                        setSplitBetween((previous) =>
                            previous.filter(
                                (id) => id !== member.user_id
                            )
                        );
                    }
                }}
            />

            <span>{member.full_name}</span>
        </label>
    ))}
</div>


                    <label>Notes</label>
                    <textarea
                        placeholder="Additional details..."
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                    />

                    <button type="submit" disabled={saving}>
                        {saving ? "Adding..." : "Add Expense"}
                    </button>

                </form>

                {message && <p>{message}</p>}

            </div>

{/* SETTLEMENT DASHBOARD */}
<div className="settlement-section">

    <h2>💰 Group Settlement</h2>

    {settlementLoading ? (
        <p>Calculating settlements...</p>
    ) : settlement ? (
        <>


{/* SETTLEMENT SUMMARY */}
<h3>Settlement Summary</h3>

<div className="expense-summary">

    <div className="summary-card">
        <span>💰</span>
        <h2>
            ₹{totalExpenses.toLocaleString("en-IN")}
        </h2>
        <p>Total Expenses</p>
    </div>

    <div className="summary-card">
        <span>✅</span>
        <h2>
            ₹{receivedPayments.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}
        </h2>
        <p>Payments Received</p>
    </div>

    <div className="summary-card">
        <span>⏳</span>
        <h2>
            ₹{pendingPayments.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}
        </h2>
        <p>Pending Payments</p>
    </div>

    <div className="summary-card">
        <span>📊</span>
        <h2>{settlementStatus}</h2>
        <p>Settlement Status</p>
    </div>

</div>


<h3>Member Outstanding Balances</h3>

<div className="settlement-balances">
    {Object.entries(settlement.outstanding_balances || {}).length === 0 ? (
        <p>Outstanding balance information is unavailable.</p>
    ) : (
        Object.entries(settlement.outstanding_balances || {}).map(
            ([memberName, balance]) => (
                <div
                    className={`settlement-card ${
                        balance > 0
                            ? "balance-positive"
                            : balance < 0
                            ? "balance-negative"
                            : "balance-neutral"
                    }`}
                    key={memberName}
                >
                    <h4>{memberName}</h4>

                    <h3>
                        Outstanding: ₹{Math.abs(balance).toFixed(2)}
                    </h3>

                    <strong>
                        {balance > 0
                            ? "Gets money back"
                            : balance < 0
                            ? "Needs to pay"
                            : "Fully Settled"}
                    </strong>
                </div>
            )
        )
    )}
</div>



            <h3>Who Owes Whom?</h3>

{settlement.settlements.length === 0 ? (
    <p>Everyone is settled up!</p>
) : (
    settlement.settlements.map((item, index) => (
        <div className="settlement-card" key={index}>
            <p>
                <strong>{item.from}</strong> owes{" "}
                <strong>{item.to}</strong>
            </p>

            <h3>₹{item.amount.toFixed(2)}</h3>

            <p>
                Status:{" "}
                <strong>
                    {item.status === "received"
                        ? "Payment Received"
                        : "Pending"}
                </strong>
            </p>

            {item.status === "pending" && (
                <button
                    onClick={() => handleMarkReceived(item)}
                >
                    Mark as Received
                </button>
            )}
        </div>
    ))
)}
        </>
    ) : (
        <p>Unable to load settlement information.</p>
    )}

</div>

            {/* ALL EXPENSES */}
            <h2>All Expenses</h2>

            {loading ? (
                <p>Loading expenses...</p>
            ) : expenses.length === 0 ? (
                <p>No expenses added yet.</p>
            ) : (
                expenses.map((expense) => (

<div className="expense-card" key={expense.id}>

    <div className="expense-card-header">
        <h3>
            {{
                hotel: "🏨",
                food: "🍽️",
                transport: "🚕",
                shopping: "🛍️",
                activities: "🎯",
                other: "📌"
            }[expense.category] || "💰"}{" "}
            {expense.title}
        </h3>

        <span className="expense-category">
            {expense.category}
        </span>
    </div>

    <h2 className="expense-amount">
        ₹{Number(expense.amount).toLocaleString("en-IN")}
    </h2>

    <p>
        <strong>Paid By:</strong>{" "}
        {expense.paid_by_name || "Unknown Member"}
    </p>

    <p>
        <strong>Split Between:</strong>{" "}
        {expense.split_between.length} members
    </p>

    <p className="expense-date">
        Added on:{" "}
        {expense.created_at
            ? new Date(expense.created_at).toLocaleDateString("en-IN")
            : "Date unavailable"}
    </p>

</div>

                ))
            )}

        </div>
    );
}

export default ExpenseTracker;
