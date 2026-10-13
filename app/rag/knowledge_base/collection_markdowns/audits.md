# Audit Logs Collection Documentation

## Collection: `audits`

**Description**  
The `audits` collection stores system-wide audit and activity logs.  
Each document represents a **tracked event, action, or state change** performed by users, systems, or external integrations.

This collection is the **central source of truth for compliance, debugging, monitoring, and forensic analysis**.

---

## Collection Fields

### 🔑 Core Identifiers

* **`_id`**  
  MongoDB ObjectId uniquely identifying the audit log entry.

* **`masterAccountId`**  
  Reference to the master account under which the activity occurred.

* **`dbId`**  
  Reference to the affected database document (if applicable).

---

### 👤 Actor References

* **`playerId`**  
  Reference to the player involved in the activity.

* **`affiliateId`**  
  Reference to the affiliate involved in the activity.

---

### ⏱️ Time & Origin

* **`timestamp`**  
  Date and time when the activity occurred.

* **`sourceIpAddress`**  
  IP address from which the action originated.

* **`userAgent`**  
  User-agent string of the client.

* **`device`**  
  Device or platform information.

---

### 🧭 Classification

* **`source`**  
  Origin of the activity.  
  *Values:* CRM, Game, Script, Website, Affiliate

* **`component`**  
  System component responsible for or affected by the activity  
  *(e.g., Player, Transaction, AffiliateChannel, WithdrawRequest, Schedule, etc.)*

* **`action`**  
  Action performed.  
  *Values:* Login, Logout, Add, Update, Delete, Initiate, Report, Email, SMS, ExternalApi, PostbackRegisterApi, PostbackQftdApi

---

### 🚨 Severity & Messaging

* **`severity`**  
  Importance level of the event.  
  *Values:* Verbose, Debugging, Notification, Informational, Success, Warning, Alert, Error, Critical, Emergency

* **`summary`**  
  Short description of the event.

* **`activity`**  
  Detailed description of the activity performed.

---

### 🧾 Payload & Details

* **`json`**  
  Raw JSON payload associated with the event.

* **`multipleLogs`**  
  Array of detailed log entries related to the same audit event.

  * **`timestamp`**  
    Time of the sub-log entry.

  * **`activity`**  
    Description of the sub-activity.

  * **`summary`**  
    Summary of the sub-log.

  * **`json`**  
    Raw payload for the sub-log.

  * **`severity`**  
    Severity level of the sub-log.

---

### 👁️ Read Tracking

* **`readBy`**  
  List of user IDs who have viewed this audit entry.

---

## 🔗 Relationships

* **`audits.playerId → players._id`**
* **`audits.affiliateId → affiliates._id`**
* **`audits.dbId → <any_collection>._id`**

---

## ℹ️ Notes

* This collection is **append-only**
* Used for **compliance, monitoring, debugging, and analytics**
* No business logic should rely on audits for state
* High-volume writes — ensure TTL or archival strategy if needed
