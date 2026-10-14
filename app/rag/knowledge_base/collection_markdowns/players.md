# Players Collection Documentation

## Collection: `players`

**Description**
The `players` collection stores player profile information, wallet snapshot values, and lifetime aggregate metrics. It is primarily used for player segmentation, reporting, and operational filtering.

---

## Collection Fields

### Profile & Identity

* **`countryId`**
  Reference to the player's registered country.
  *Usage:* Geographic segmentation and reporting
  *Type:* Static profile attribute

* **`username`**
  Unique human-readable identifier assigned to the player.
  *Usage:* Authentication and identification
  *Note:* Not used for analytics

* **`currency`**
  ISO 3-letter currency code representing the player's primary wallet currency.
  *Usage:* Applies to balances and lifetime aggregates

* **`status`**
  Current account state such as `Active`, `Inactive`, or `Fraud`.
  *Usage:* Operational filtering

---

### 💰 Wallet Snapshot Fields (Current State)

> These fields represent the **latest state only** and are **not time-series**

* **`totalBalance`**
  Current total balance across real, bonus, and winnings

* **`realBalance`**
  Current withdrawable real-money balance

* **`bonusBalance`**
  Current bonus balance subject to wagering conditions

* **`totalWithdrawPendingAmount`**
  Total withdrawal amount currently under processing

---

### 📊 Lifetime Aggregate Metrics (Pre-aggregated)

> ⚠️ These fields are **NOT time-filterable**

#### Deposits & Withdrawals

* **`totalDepositAmount`**
  Lifetime sum of all successful deposits

* **`totalWithdrawAmount`**
  Lifetime sum of all completed withdrawals

* **`totalDepositCount`**
  Lifetime count of successful deposits

* **`totalWithdrawCount`**
  Lifetime count of completed withdrawals

---

#### Bonus Metrics

* **`totalBonusCreditAmount`**
  Lifetime total of all bonus credits received

* **`totalBonusBetAmount`**
  Lifetime sum of all bets placed using bonus funds

* **`totalBonusWinAmount`**
  Lifetime sum of winnings from bonus-funded bets

* **`totalBonusBetCount`**
  Lifetime count of bonus-funded bets

* **`totalBonusWinCount`**
  Lifetime count of winning bonus bets

---

#### Real Money Betting/Waggering Metrics

* **`totalRealBetAmount`**
  Lifetime sum of all wager amounts placed using real funds
  *Note:* Not suitable for time-based analysis

* **`totalRealWinAmount`**
  Lifetime sum of winnings from real-money bets

* **`totalRealBetCount`**
  Lifetime count of real-money bets placed

* **`totalRealWinCount`**
  Lifetime count of winning real-money bets

---

### ⏱️ last activity & Metadata Fields

* **`lastDepositAt`**
  Timestamp of the most recent successful deposit
  *Usage:* Recency-based filtering only

* **`lastWithdrawAt`**
  Timestamp of the most recent withdrawal
  *Usage:* Recency-based filtering only

* **`createdAt`**
  Timestamp when the player account was created

* **`updatedAt`**
  Timestamp of the last update to the player document

---

## 🔗 Relationships

* **`players.countryId → countries._id`**
  The `countryId` field references the primary key of the `countries` collection.

---

## ℹ️ Notes

* Lifetime metrics are **pre-aggregated**
* Snapshot fields reflect **current state only**
* Time-based analysis should rely on **transaction-level collections**, not this collection
