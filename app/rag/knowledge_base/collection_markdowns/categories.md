# Categories Collection Documentation

## Collection: `categories`

**Description**  
The `categories` collection defines logical groupings used to organize games within the platform. Categories are used for game discovery, UI navigation, filtering, reporting, and provider-based grouping in both player-facing and administrative interfaces.

---

## Collection Fields

### Category Identity & Definition

* **`_id`**  
  MongoDB ObjectId uniquely identifying the category record.  
  **Usage:** Primary key reference across game and provider mappings

* **`name`**  
  Display name of the category (e.g., Slots, Roulette, Top Games).  
  **Usage:** UI grouping, filtering, and reporting

* **`index`**  
  Numeric sorting order for category display.  
  **Usage:** Visual ordering in dashboards and game lobbies  
  **Note:** Lower values appear first

---

### Operational Status

* **`status`**  
  Operational state of the category.  
  **Values:** `Pending`, `Active`, `Inactive`  
  **Usage:** Controls visibility of categories and associated games

---

### Provider Association

* **`providerIds`**  
  List of providers associated with this category.  
  **Type:** Array of references → `providers._id`  
  **Usage:** Determines which providers contribute games to the category

---

### Timestamps

* **`createdAt`**  
  Timestamp when the category record was created.

* **`updatedAt`**  
  Timestamp of the last update to the category record.

---

## Relationships

* `categories._id` → `games.categoryIds`  
* `categories.providerIds` → `providers._id`

---

## Notes

* Categories may group games across multiple providers  
* Category visibility directly affects game discoverability  
* Sorting behavior should rely on the `index` field  
* Deactivating a category hides all associated games from UI
