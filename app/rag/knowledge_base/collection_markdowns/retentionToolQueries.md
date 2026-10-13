# Retention Tool Queries Collection Documentation

## Collection: `retentionToolQueries`

**Description**  
The `retentionToolQueries` collection stores reusable query definitions used by the retention engine.  
Each document represents a **saved player segmentation or filtering logic** that can be executed dynamically by schedules, campaigns, or automation workflows.

This collection acts as the **query source of truth for retention, reactivation, and engagement use cases**.

---

## Collection Fields

### 🔑 Core Identifiers

* **`_id`**  
  MongoDB ObjectId uniquely identifying the retention query.

* **`name`**  
  Human-readable name of the query.  
  *Usage:* Identification in schedules and retention tools

---

### 🧠 Query Definition

* **`queryJson`**  
  Serialized query logic used to filter players.  
  *Usage:* Executed dynamically at runtime for segmentation

---

### ⏱️ Lifecycle Tracking

* **`createdAt`**  
  Date and time when the query was created.

* **`updatedAt`**  
  Date and time when the query was last updated.


---

## 🔗 Relationships

* **`schedules.retentionToolQueriesId → retentionToolQueries._id`**

---

## ℹ️ Notes

* Queries are evaluated **at execution time**, not at creation time
* `queryJson` must remain backward-compatible for scheduled jobs
* This collection contains **no execution results**, only definitions
