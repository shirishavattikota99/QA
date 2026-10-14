# Transactions Collection Documentation

## Collection: `transactions`

**Description**  
The `transactions` collection stores all financial and gameplay-related monetary events.  
Each document represents a **single atomic transaction** and is the **source of truth for time-based financial analysis**.

---

## Collection Fields

### 🔑 Core Identifiers

* **`transactionHash`**  
  Unique transaction identifier across the platform.  
  *Usage:* Deduplication, reconciliation, and auditing

* **`_id`**  
  MongoDB ObjectId uniquely identifying the transaction document.

---

### 👤 Player & Geography

* **`playerId`**  
  Reference to the player who initiated or received the transaction.  
  *Usage:* Player-level analytics and joins

* **`countryId`**  
  Reference to the player’s registered country.  
  *Usage:* Geographic reporting and compliance

---

### ⏱️ Time & Status

* **`timestamp`**  
  Date and time when the transaction occurred (ISO format).  
  *Usage:* Time-based filtering and aggregation

* **`status`**  
  Current processing state of the transaction.  
  *Values:* Pending, Initiated, Success, Failed, Rejected, Cancelled, Refunded, Chargeback  
  *Usage:* Operational and financial filtering

---

### 🧭 Transaction Classification

* **`source`**  
  Origin of the transaction.  
  *Values:* Payment, Game, Admin, Affiliate, Kiosk, Automate, Coupon, Self, Sports

* **`type`**  
  Financial action performed.  
  *Values:* Deposit, Withdraw, Credit, Debit, Bet, Win, Rollback  
  *Usage:* Behavioral and financial categorization

* **`amountType`**  
  Balance type affected by the transaction.  
  *Values:* Real, Bonus, Real_Bonus

---

### 💰 Amounts & Balances

* **`amount`**  
  Monetary value of the transaction.

* **`baseCurrencyAmount`**  
  Transaction amount converted to the system base currency (EUR).  
  *Usage:* Unified financial reporting

* **`closingRealBalance`**  
  Player’s real-money balance after the transaction.

* **`closingBonusBalance`**  
  Player’s bonus balance after the transaction.

* **`closingWinningBalance`**  
  Player’s winnings balance after the transaction.

---

### 💱 Currency Details

* **`playerCurrency`**  
  Currency code of the player’s wallet.

* **`depositCurrency`**  
  Currency used during deposit (if different from wallet currency).

* **`depositCurrencyAmount`**  
  Original amount before currency conversion.

---

### 🎁 Bonus & Promotions

* **`bonusName`**  
  Identifier of the bonus promotion associated with the transaction.

* **`isFtd`**  
  Indicates whether the transaction is the player’s first-ever deposit (FTD).

* **`isQftd`**  
  Indicates whether the player qualifies as a Qualified First Time Depositor (QFTD).

---

### 🔄 Rollbacks & References

* **`rollbackTransactionId`**  
  Reference to the original transaction being reversed.

* **`depositTransactionId`**  
  Reference to the deposit transaction linked to a bonus or credit.

---

### 💳 Payment Information

* **`paymentGatewayId`**  
  Reference to the payment gateway used for processing.

* **`paymentMethod`**  
  Payment method such as Card, Crypto, Bank, etc.

* **`paymentVia`**  
  Intermediate service or routing provider.

* **`cardLastFourDigits`**  
  Masked card identifier (last four digits only).

* **`paymentCryptoAddress`**  
  Wallet address used for crypto transactions.

* **`cryptoNetwork`**  
  Blockchain network (e.g., TRC20, ERC20, BEP20).

---

### 🎮 Game & Provider

* **`gameId`**  
  Reference to the game associated with the transaction.

* **`masterProviderId`**  
  Reference to the game or content provider.

---

### 🤝 Affiliate Attribution

* **`affiliateId`**  
  Reference to the affiliate associated with the transaction.

* **`affiliateChannelId`**  
  Reference to the affiliate channel responsible for the referral.

---

### 🧾 Audit & Metadata

* **`auditId`**  
  Reference to the audit record for compliance tracking.

* **`json`**  
  Raw provider or gateway response data.

* **`notes`**  
  Administrative or operational remarks.

* **`errorReason`**  
  Failure reason in case of unsuccessful transactions.

---

### 🔐 Security & Device

* **`ipAddress`**  
  IP address recorded at transaction time.

* **`device`**  
  Device or user-agent information.

---

## 🔗 Relationships

* **`transactions.playerId → players._id`**
* **`transactions.countryId → countries._id`**
* **`transactions.gameId → games._id`**
* **`transactions.paymentGatewayId → paymentGateways._id`**
* **`transactions.affiliateId → affiliates._id`**
* **`transactions.affiliateChannelId → affiliateChannels._id`**
* **`transactions.rollbackTransactionId → transactions._id`**
* **`transactions.depositTransactionId → transactions._id`**

---

## ℹ️ Notes

* This collection is **fully time-series**
* All financial analytics should be derived from this collection
* Player lifetime metrics are **aggregated into the players collection**
