# Player Categorizations Collection Documentation

## Collection: `playerCategorizations`

**Description**  
The `playerCategorizations` collection defines logical groupings used to segment players based on predefined business rules, behavioral metrics, or lifecycle stages. These categorizations are used for CRM targeting, promotions, reporting, and player lifecycle management.

---

## Collection Fields

### Categorization Identity & Definition

* **`_id`**  
  MongoDB ObjectId uniquely identifying the player categorization record.  
  **Usage:** Primary key reference across player segmentation logic

* **`categorizationName`**  
  Human-readable name of the player category (e.g., `VIP`, `High Roller`, `Newcomer`).  
  **Usage:** Display in dashboards, CRM tools, and reports

* **`categorizationLevel`**  
  Internal tier or level identifier used to rank categories hierarchically.  
  **Usage:** Priority ordering and escalation logic

---

### Visual & UI Metadata

* **`categorizationColor`**  
  Hex code or color name representing the category visually.  
  **Usage:** UI labels, dashboards, and analytics visualizations

---

### Aggregated Metrics

* **`totalPlayers`**  
  Number of players currently assigned to this category.  
  **Usage:** Monitoring category size and distribution  
  **Note:** Automatically maintained by the categorization engine

---

### Timestamps

* **`createdAt`**  
  Timestamp when the player categorization was created.

* **`updatedAt`**  
  Timestamp when the player categorization was last updated.

---

## Relationships

* `playerCategorizations._id` → `players.categorizationId` *(if linked)*

---

## Notes

* Categories are typically assigned via automated rules or scheduled jobs  
* A player may belong to one or multiple categories depending on business logic  
* `totalPlayers` reflects current assignment state, not historical membership  
* Category colors should remain consistent for clear UI recognition
