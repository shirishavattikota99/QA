# Payment Gateways Collection Documentation

## Collection: `paymentGateways`

**Description**  
The `paymentGateways` collection stores configuration, availability rules, and fee structures for all payment gateway integrations on the platform. It is used to control how deposits and withdrawals are routed, restricted, priced, and exposed to players based on geography, currency, and depositor type.

---

## Collection Fields

### Gateway Identity & Configuration

* **`_id`**  
  MongoDB ObjectId uniquely identifying the payment gateway record.  
  **Usage:** Primary key reference across collections

* **`name`**  
  Human-readable name of the payment gateway.  
  **Usage:** Display in dashboards and transaction modules

* **`processor`**  
  Processor identifier used for routing payments through the correct integration service.  
  **Usage:** Integration selection and payment execution  
  **Examples:** CapitalManagement, GateCharge, GumBallPay, UZOpay, PayTechno, QuantumPay, Payofix, BlockBee, SmilePayz, Pragmatic, BlockSystems, EzzyGate, FreedomPay, Slikair, Paysecure, Superbit, Cash, Neosurf, Paysafe, Finvert, Paydot, Paympire, AstroPay, KwidPay, PayPound

---

### Depositor Support & Status

* **`depositorType`**  
  Category of depositors supported by the gateway.  
  **Values:** `FTD`, `Recurring`  
  **Usage:** Funnel and payment eligibility control

* **`status`**  
  Operational status of the payment gateway.  
  **Values:** `Pending`, `Active`, `Inactive`  
  **Usage:** Controls availability for player transactions

---

### Payment Methods Configuration

* **`methods`**  
  Array of payment method configurations supported by the gateway.  
  **Usage:** Defines currency, country, crypto, and fee rules per method

#### Methods Sub-Fields

* **`methods.method`**  
  Name of the payment method (e.g., Visa, MasterCard, BTC, USDT).

* **`methods.isAllCurrencies`**  
  Indicates whether the method supports all platform currencies.  
  **Type:** Boolean

* **`methods.supportedCurrencies`**  
  List of supported currency codes if not all currencies are allowed.

* **`methods.isCryptoCurrency`**  
  Indicates whether the method supports cryptocurrency payments.  
  **Type:** Boolean

* **`methods.cryptoNetworks`**  
  List of supported blockchain networks (e.g., ERC20, TRC20, BEP20).

* **`methods.isWorldwide`**  
  Indicates whether the method is available in all countries.  
  **Type:** Boolean

* **`methods.allowedCountries`**  
  List of references to allowed countries.  
  **Type:** Reference → `countries._id`

* **`methods.blockedCountries`**  
  List of references to blocked countries.  
  **Type:** Reference → `countries._id`

---

### Fees & Financial Controls

* **`methods.successFeePercent`**  
  Percentage fee applied to successful transactions.  
  **Usage:** Settlement and accounting

* **`methods.transactionFeeAmount`**  
  Fixed fee applied per transaction.

* **`methods.refundFeeAmount`**  
  Fee applied when a refund is processed.

* **`methods.chargebackFeeAmount`**  
  Fee applied when a chargeback occurs.

* **`rollingReservePercent`**  
  Percentage of funds held as rolling reserve.  
  **Usage:** Chargeback and risk protection

* **`rollingReserveReturnDays`**  
  Number of days after which rolling reserve funds are released.

---

### Timestamps

* **`createdAt`**  
  Timestamp when the payment gateway record was created.

* **`updatedAt`**  
  Timestamp of the last update to the payment gateway record.
  
---

## Relationships

* `paymentGateways.methods.allowedCountries` → `countries._id`  
* `paymentGateways.methods.blockedCountries` → `countries._id`

---

## Notes

* Gateway and method status directly control player payment availability  
* Country and currency rules are evaluated per payment method  
* Crypto payments require both `isCryptoCurrency` and valid `cryptoNetworks`  
* Rolling reserve settings impact settlement cash flow and accounting
