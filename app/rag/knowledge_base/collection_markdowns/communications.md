# Communications Collection Documentation

## Collection: `communications`

**Description**  
The `communications` collection stores all outbound player communications, including emails and SMS messages. It supports both one-to-one messages and campaign-based communication chains, and is used for CRM messaging, promotional campaigns, transactional notifications, and delivery tracking with provider responses.

---

## Collection Fields

### Communication Identity & Linking

* **`_id`**  
  MongoDB ObjectId uniquely identifying the communication record.  
  **Required:** No  
  **Format:** ObjectId (`^[0-9a-fA-F]{24}$`)

* **`campaignCommunicationId`**  
  Reference to another communication in the same collection when part of a campaign chain.  
  **Required:** No  
  **Format:** ObjectId  
  **Reference:** `communications._id`  
  **Usage:** Campaign sequencing and message grouping

---

### Ownership & Targeting

* **`playerId`**  
  Reference to the player receiving the communication.  
  **Required:** No  
  **Format:** ObjectId  
  **Reference:** `players._id`  
  **Usage:** Player-level CRM tracking

* **`masterAccountId`**  
  Reference to the master/admin account that initiated the communication.  
  **Required:** No  
  **Format:** ObjectId  
  **Usage:** Auditing and ownership tracking

---

### Communication Type & State

* **`type`**  
  Medium used to send the communication.  
  **Required:** Yes  
  **Values:** `Mail`, `SMS`  
  **Usage:** Routing to the appropriate delivery provider

* **`status`**  
  Current state of the communication lifecycle.  
  **Required:** Yes  
  **Values:** `Initiated`, `Success`, `Failed`  
  **Usage:** Delivery monitoring and retry logic

* **`isCampaign`**  
  Indicates whether the communication is part of a campaign.  
  **Required:** Yes  
  **Type:** Boolean  
  **Usage:** Distinguishes campaign messages from individual messages

---

### Recipient Details

* **`recipients`**  
  List of recipient identifiers such as email addresses or phone numbers.  
  **Required:** No  
  **Usage:** Multi-recipient support for campaigns

* **`email`**  
  Target email address when the communication type is `Mail`.  
  **Required:** No

* **`phone`**  
  Target phone number when the communication type is `SMS`.  
  **Required:** No

---

### Message Content

* **`subject`**  
  Subject or title of the message.  
  **Required:** Yes  
  **Usage:** Primarily used for email communications

* **`content`**  
  Body text of the message delivered to the recipient(s).  
  **Required:** No

---

### Delivery & Provider Metadata

* **`sentAt`**  
  Timestamp when the communication was dispatched to the provider.  
  **Required:** Yes  
  **Format:** ISO date-time  
  **Usage:** Delivery timing and reporting

* **`response`**  
  Raw response returned by the email/SMS provider.  
  **Required:** No  
  **Usage:** Delivery validation and diagnostics

* **`error`**  
  Error message recorded if delivery fails.  
  **Required:** No  
  **Usage:** Debugging, alerting, and retries

* **`selectedEmailId`**  
  Reference to the email credential used for sending.  
  **Required:** No  
  **Format:** ObjectId  
  **Reference:** `emailCredentials._id`

---

### System Fields

* **`__v`**  
  Mongoose internal version key.  
  **Required:** No  
  **Usage:** Concurrency control and document versioning
  
---

## Relationships

* `communications.campaignCommunicationId` → `communications._id` *(self-reference)*  
* `communications.playerId` → `players._id`  
* `communications.selectedEmailId` → `emailCredentials._id`

---

## Notes

* Campaign communications are linked via `campaignCommunicationId`  
* Status updates should be driven by provider callbacks or async workers  
* Both `recipients` and direct fields (`email`, `phone`) may coexist depending on delivery strategy  
* Failed messages should always retain `error` and provider `response` for audit and retries
