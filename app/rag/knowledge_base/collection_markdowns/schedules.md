# Schedules Collection Documentation

## Collection: `schedules`

**Description**  
The `schedules` collection stores automated task definitions used by the retention and engagement system.  
Each document represents a **configured job** that runs on a defined schedule to trigger emails, SMS, reports, or player categorization/segmentation actions.

This collection is the **source of truth for cron-like execution logic and campaign automation**.

---

## Collection Fields

### 🔑 Core Identifiers

* **`_id`**  
  MongoDB ObjectId uniquely identifying the schedule.

* **`retentionToolQueriesId`**  
  Reference to the retention query definition used to fetch target players.  
  *Usage:* Audience selection and segmentation

* **`masterAccountId`**  
  Reference to the master account owning the schedule.

* **`emailTemplateId`**  
  Reference to the email template used for email-based actions.

---

### 📝 Schedule Definition

* **`name`**  
  Human-readable name of the schedule.

* **`status`**  
  Current state of the schedule.  
  *Values:* Pending, Active, Inactive

* **`frequency`**  
  Execution frequency of the schedule.  
  *Values:* OneTime, Daily, Monthly, CustomDays

* **`daysNumber`**  
  Interval in days when `frequency` is set to `CustomDays`.

* **`date`**  
  Execution date for one-time schedules.

* **`startTime`**  
  Time of day when the schedule should run.

* **`timezone`**  
  Timezone used for execution timing.  
  *Default:* UTC

---

### ⚙️ Action Configuration

* **`action`**  
  Action executed when the schedule runs.  
  *Values:*  
  - SendBulkTransactions  
  - SendEmail  
  - SendSMS  
  - GenerateCsvSendEmail  
  - GenerateCsvSendSMS  
  - PlayerCategorization

* **`requestBodyJson`**  
  Serialized configuration payload used during execution.

---

### ⏱️ Execution Tracking

* **`lastRunAt`**  
  Timestamp of the most recent execution.

* **`createdAt`**  
  Date and time when the schedule was created.

* **`updatedAt`**  
  Date and time when the schedule was last updated.

---

## 🔗 Relationships

* **`schedules.retentionToolQueriesId → retentionToolQueries._id`**
* **`schedules.emailTemplateId → emailTemplates._id`**

---

## ℹ️ Notes

* Inactive schedules are ignored by the scheduler engine
* Execution failures should be logged outside this collection
* Schedules are timezone-aware and must be normalized at runtime
* Player selection is evaluated **at execution time**, not creation time
