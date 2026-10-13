# Affiliates Collection Documentation

## Collection: `affiliates`

**Description**  
The `affiliates` collection stores all affiliate partner accounts registered on the platform.  
Each document represents a **single affiliate entity** responsible for traffic acquisition, player referrals, and revenue generation.

This collection is the **source of truth for affiliate identity, access level, contact details, and postback configurations**.

---

## Collection Fields

### 🔑 Core Identifiers

* **`_id`**  
  MongoDB ObjectId uniquely identifying the affiliate.

* **`username`**  
  Unique login identifier for the affiliate.  
  *Usage:* Authentication, dashboards, and internal references

* **`email`**  
  Unique email address of the affiliate.  
  *Usage:* Communication, login, password recovery

---

### 🌍 Geography

* **`countryId`**  
  Reference to the affiliate’s registered country.  
  *Usage:* Geographic reporting, compliance, and regional restrictions

---

### 👤 Personal Information

* **`firstName`**  
  Affiliate’s first name.

* **`lastName`**  
  Affiliate’s last name.

* **`gender`**  
  Gender of the affiliate.  
  *Values:* Male, Female, Other

* **`dob`**  
  Date of birth of the affiliate (ISO date-time).

---

### 📞 Contact Details

* **`mobile`**  
  Mobile phone number of the affiliate.

* **`telegramId`**  
  Telegram identifier for communication.

* **`skypeId`**  
  Skype identifier for communication.

* **`address`**  
  Primary address of the affiliate.

* **`address2`**  
  Secondary address information.

* **`state`**  
  State or province.

* **`city`**  
  City name.

* **`pinCode`**  
  Postal or ZIP code.

---

### 🔐 Authentication & Access

* **`password`**  
  Encrypted password used for affiliate login.

* **`access`**  
  Access level of the affiliate account.  
  *Values:* Normal, Manager  
  *Usage:* Role-based access control

---

### 📊 Status & Lifecycle

* **`status`**  
  Current state of the affiliate account.  
  *Values:* Pending, Active, Inactive  
  *Usage:* Account enablement and filtering

* **`createdAt`**  
  Date and time when the affiliate account was created.

* **`updatedAt`**  
  Date and time when the affiliate account was last updated.

---

### 📢 Marketing & Traffic

* **`trafficSource`**  
  Description of the affiliate’s traffic origin (SEO, PPC, Social, etc.).

* **`marketingVia`**  
  Primary marketing channel used by the affiliate.  
  *Values:* Digital, Media, Mail, Advertisements

* **`sendNewsletter`**  
  Indicates whether the affiliate has opted in for newsletters.

---

### 🏢 Company Information

* **`companyName`**  
  Registered company or brand name of the affiliate.

---

### 🔗 Postback Configuration

* **`postbackUrls`**  
  Container for affiliate postback endpoints.

  * **`registerUrl`**  
    Postback URL triggered on player registration.

  * **`qFtdUrl`**  
    Postback URL triggered on Qualified First Time Deposit (QFTD).

---

### 💰 Financial

* **`balance`**  
  Current payable balance for the affiliate.  
  *Default:* 0  
  *Minimum:* 0  
  *Usage:* Affiliate payouts and revenue tracking
  
---

## 📌 Indexes

* **Unique Index on `username`**  
  Ensures no duplicate affiliate usernames.

* **Unique Index on `email`**  
  Ensures one affiliate account per email address.

---

## 🔗 Relationships

* **`affiliates.countryId → countries._id`**
* **`transactions.affiliateId → affiliates._id`**
* **`affiliateChannels.affiliateId → affiliates._id`**
* **`players.affiliateId → affiliates._id`**


---

## ℹ️ Notes

* Affiliate balances are **derived from transaction-level aggregation**
* Postback URLs must be validated before activation
* Affiliate access level controls visibility and management permissions
* Deactivating an affiliate doe*
