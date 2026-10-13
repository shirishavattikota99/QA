# Countries Collection Documentation

## Collection: `countries`

**Description**  
The `countries` collection stores geographic, regulatory, currency, and localization metadata for supported countries on the platform. It is used for player registration eligibility, compliance enforcement, currency configuration, localization defaults, and region-based segmentation.

---

## Collection Fields

### Country Identity & Status

* **`_id`**  
  MongoDB ObjectId uniquely identifying the country record.  
  **Usage:** Primary key reference across collections

* **`name`**  
  Official country name.  
  **Usage:** Player registration, localization, and regional configuration

* **`status`**  
  Operational availability of the country on the platform.  
  **Values:** `Pending`, `Active`, `Inactive`  
  **Usage:** Controls registration and gameplay eligibility

---

### Currency Configuration

* **`currencyCode`**  
  ISO 4217 three-letter currency code (e.g., USD, EUR, INR).  
  **Usage:** Monetary transactions and wallet configuration

* **`currencyName`**  
  Full name of the country’s currency.  
  **Usage:** Informational and UI display

* **`currencySymbol`**  
  Symbol representing the country’s currency (e.g., $, €, ₹).  
  **Usage:** Financial formatting in UI

---

### Localization & Geography

* **`countryCapital`**  
  Capital city of the country.  
  **Usage:** Metadata and informational reference

* **`countryLanguage`**  
  Primary spoken language (full name).  
  **Usage:** Localization defaults and content adaptation

* **`countryLanguageCode`**  
  Short language code (e.g., `en`, `fr`, `de`, `zh-CN`).  
  **Usage:** Mapped to i18n system language configuration

---

### ISO & Regulatory Codes

* **`countryCode`**  
  ISO 3166-1 alpha-2 country code (e.g., US, IN, GB).  
  **Usage:** Compliance validation and geographic routing

* **`countryCodeAlpha3`**  
  ISO 3166-1 alpha-3 country code.  
  **Usage:** Standardized integrations and reporting

* **`countryIsoCode`**  
  Numeric ISO 3166 country identifier.  
  **Usage:** External system mappings

---

### Contact & Visual Metadata

* **`phoneCode`**  
  International dialing prefix (e.g., +1, +44, +91).  
  **Usage:** Phone number validation and formatting

* **`flagEmoji`**  
  Unicode emoji representing the national flag.  
  **Usage:** Visual indicators in UI

* **`flagUrl`**  
  URL to the country’s flag image asset.  
  **Usage:** Dashboards and client applications

---

### Timezone Configuration

* **`timezone`**  
  Primary timezone identifier (e.g., `Asia/Kolkata`).  
  **Usage:** Default time normalization

* **`timezones`**  
  List of all supported timezone identifiers for the country.  
  **Usage:** Multi-timezone country support

---

## Relationships

* `countries._id` → `players.countryId`

---

## Notes

* Country status directly impacts player onboarding eligibility  
* Currency fields define default wallet behavior  
* Timezone values are critical for accurate reporting and activity analysis  
* Localization defaults fall back to `countryLanguageCode` where applicable
