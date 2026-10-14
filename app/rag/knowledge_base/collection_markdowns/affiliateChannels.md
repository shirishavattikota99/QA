# Affiliate Channels Collection Documentation

## Collection: `affiliateChannels`

**Description**  
The `affiliateChannels` collection represents individual tracking channels created under an affiliate.  
Each document defines **how traffic is tracked, attributed, monetized, and evaluated** for a specific affiliate source such as campaigns, links, or media placements.

This collection is the **source of truth for affiliate deal configuration, performance metrics, and attribution rules**.

---

## Collection Fields

### 🔑 Core Identifiers

* **`_id`**  
  MongoDB ObjectId uniquely identifying the affiliate channel.

* **`affiliateId`**  
  Reference to the affiliate that owns this channel.  
  *Usage:* Affiliate-level grouping and reporting

* **`name`**  
  Human-readable name of the affiliate channel.  
  *Usage:* Campaign identification and reporting

* **`endpoint`**  
  Unique tracking endpoint or referral code for this channel.  
  *Usage:* Player attribution and click tracking

---

### 📊 Status & Lifecycle

* **`status`**  
  Current state of the affiliate channel.  
  *Values:* Pending, Active, Inactive  
  *Usage:* Enablement and filtering

* **`createdAt`**  
  Date and time when the channel was created.

* **`updatedAt`**  
  Date and time when the channel was last updated.

---

### 🧾 Deal Configuration

* **`dealType`**  
  Commercial agreement model applied to this channel.  
  *Values:* CPA, RevenueSharing, Hybrid

* **`adminFeePercent`**  
  Platform administrative fee percentage deducted from earnings.

* **`dealAmount`**  
  Fixed payout amount (used mainly for CPA deals).

* **`dealPercentage`**  
  Revenue share percentage (used mainly for RevenueSharing deals).

---

### 📌 Deal Conditions

* **`conditionType`**  
  Qualification logic for payouts.  
  *Values:* Normal, QCPA

* **`baselineDepositAmount`**  
  Minimum deposit amount required to qualify.

* **`baselineDepositCount`**  
  Minimum number of deposits required to qualify.

* **`baselineWagerAmount`**  
  Minimum wagering amount required for qualification.

---

### 🖼️ Banners & Creatives

* **`banners`**  
  List of banners associated with this affiliate channel.

  * **`bannerId`**  
    Reference to the banner creative.  

  * **`status`**  
    Banner availability status.  
    *Values:* Pending, Active, Inactive

---

### 🔗 Tracking Parameters

* **`queryParams`**  
  Key-value parameters appended to the tracking URL.

  * **`key`**  
    Query parameter name.

  * **`value`**  
    Query parameter value.

---

### 📈 Performance Metrics

* **`signupCount`**  
  Total number of player registrations.

* **`depositCount`**  
  Total number of deposit transactions.

* **`withdrawCount`**  
  Total number of withdrawal transactions.

* **`ftdCount`**  
  Number of First Time Depositors (FTD).

* **`qFtdCount`**  
  Number of Qualified First Time Depositors (QFTD).

* **`qFtdPlayerIds`**  
  List of player IDs qualified as QFTD.

---

### 💰 Financial Aggregates

* **`totalDepositAmount`**  
  Total deposited amount attributed to this channel.

* **`totalQualifiedDepositAmount`**  
  Total deposit amount that met qualification rules.

* **`totalWithdrawAmount`**  
  Total withdrawn amount attributed to this channel.

* **`totalEarnings`**  
  Total earnings generated for the affiliate channel.

---

### 🧾 Metadata

* **`__v`**  
  Mongoose internal version key.

---

## 📌 Indexes

* **Index on `affiliateId`**  
  Improves affiliate-level lookups and reporting.

* **Unique Sparse Index on `endpoint`**  
  Ensures unique tracking endpoints when defined.

---

## 🔗 Relationships

* **`affiliateChannels.affiliateId → affiliates._id`**
* **`affiliateChannels.banners.bannerId → banners._id`**
* **`transactions.affiliateChannelId → affiliateChannels._id`**
* **`players._id → affiliateChannels.qFtdPlayerIds[]`**

---

## ℹ️ Notes

* Metrics are **incrementally updated** from the transactions collection
* Channel earnings are recalculated based on deal configuration
* Deactivating a channel stops new attribution but preserves historical data
* QCPA channels require qualification before payouts are counted
