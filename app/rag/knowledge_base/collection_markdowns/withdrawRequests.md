# Withdraw Requests Collection Documentation

## Collection: `withdrawRequests`

**Description**  
The `withdrawRequests` collection stores all player-initiated withdrawal requests.  
Each document represents a **single withdrawal intent** linked to a financial transaction and is used for **manual or automated payout processing, review, and auditing**.

This collection acts as the **operational layer for withdrawals**, while financial truth remains in the `transactions` collection.

---

## Collection Fields

### 🔑 Core Identifiers

* **`_id`**  
  MongoDB ObjectId uniquely identifying the withdrawal request.

* **`playerId`**  
  Reference to the player who initiated the withdrawal.  
  *Usage:* Player-level lookup and compliance checks

* **`transactionId`**  
  Reference to the withdrawal transaction record.  
  *Usage:* Financial reconciliation and traceability

---

### 💳 Payment Details

* **`paymentProcessor`**  
  Payment gateway or processor handling the withdrawal.  
  *Usage:* Routing, reporting, and failure analysis

* **`amount`**  
  Withdrawal amount in player currency.

* **`baseCurrencyAmount`**  
  Withdrawal amount converted to system base currency.  
  *Usage:* Unified financial reporting

---

### 📊 Status & Messaging

* **`status`**  
  Current state of the withdrawal request.  
  *Values:* Pending, Completed, Rejected, Cancelled  
  *Usage:* Workflow control and filtering

* **`message`**  
  Administrative or system-generated message related to the request.

---

### ⏱️ Time & Audit

* **`createdAt`**  
  Date and time when the withdrawal request was created.

* **`updatedAt`**  
  Date and time when the withdrawal request was last updated.

---

## 📌 Indexes

* **Index on `playerId`**  
  Optimizes player withdrawal history lookups.

* **Index on `paymentProcessor`**  
  Optimizes processor-based filtering and reporting.

---

## 🔗 Relationships

* **`withdrawRequests.playerId → players._id`**
* **`withdrawRequests.transactionId → transactions._id`**

---

## ℹ️ Notes

* Financial balance updates must be derived from the `transactions` collection
* Rejected or cancelled requests do **not** imply fund movement
* Each withdrawal request maps to **exactly one transaction**
