# Orbit Commerce — Operational Close Workbook Cleanup

## Overview

This document describes the data-cleaning and consolidation steps performed in Excel to standardize Orbit Commerce’s global operational close workbook. The workbook contained inconsistent region names, mixed date formats, currency strings in numeric fields, and missing expense values.

The goal was to prepare the dataset for filtering and compute total variance for specific operational criteria.

---

## Step 1: Clean Record ID (Trim Whitespace)

**New Column:** `Clean Record ID`

**Formula (H2):**

```excel
=TRIM(A2)
```

**Purpose:**

* Removes leading/trailing spaces.
* Ensures consistent identifiers for matching and auditing.

---

## Step 2: Standardize Region Names

**New Column:** `Clean Region`

A lookup table was created to map aliases to canonical names.

### Lookup Table (K:L)

| Alias                                         | Canonical            |
| --------------------------------------------- | -------------------- |
| APAC                                          | Asia Pacific         |
| Asia-Pacific                                  | Asia Pacific         |
| AsiaPac                                       | Asia Pacific         |
| E.U.                                          | Europe               |
| EU                                            | Europe               |
| LAT AM                                        | Latin America        |
| MEA                                           | Middle East & Africa |
| N. America                                    | North America        |
| North-Am                                      | North America        |
| *(additional aliases included as discovered)* |                      |

**Formula (I2):**

```excel
=TRIM(XLOOKUP(B2,$K$2:$K$26,$L$2:$L$26,B2))
```

**Purpose:**

* Normalizes regional naming.
* Ensures accurate grouping and filtering.

---

## Step 3: Convert Closing Period to Valid Dates

The dataset contained mixed date formats:

* `YYYY-MM-DD`
* `DD/MM/YYYY`
* `Mon DD, YYYY`
* `YYYY Qn` (fiscal quarter)

**New Column:** `Clean Date`

**Formula (J2):**

```excel
=LET(
x,TRIM(C2),
IF(ISNUMBER(SEARCH("Q",x)),
    EOMONTH(DATE(LEFT(x,4),RIGHT(x,1)*3,1),0),
IF(ISNUMBER(SEARCH("-",x)),
    DATE(LEFT(x,4),MID(x,6,2),RIGHT(x,2)),
IF(ISNUMBER(SEARCH(",",x)),
    DATEVALUE(x),
    DATE(RIGHT(x,4),MID(x,4,2),LEFT(x,2))
)))
```

**Logic:**

* Quarter codes converted to last day of quarter.
* ISO dates parsed directly.
* Textual month formats parsed with `DATEVALUE`.
* DD/MM/YYYY parsed manually to avoid locale errors.

---

## Step 4: Clean Revenue Column

Revenue values contained currency symbols, commas, and text.

**New Column:** `Clean Revenue`

**Formula (M2):**

```excel
=VALUE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(TRIM(D2),"USD",""),"$",""),",","")," ",""))
```

**Purpose:**

* Removes `$`, `USD`, commas, and spaces.
* Converts text to numeric values.

---

## Step 5: Clean Expense Column (with 37% Rule)

If expenses were missing or marked `USD TBD`, they were imputed as **37% of revenue**.

**New Column:** `Clean Expense`

**Formula (N2):**

```excel
=IF(OR(TRIM(E2)="",TRIM(E2)="USD TBD"),
   K2*0.37,
   VALUE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(TRIM(E2),"USD",""),"$",""),",","")," ",""))
)
```

**Purpose:**

* Cleans currency formatting.
* Ensures no missing values for variance calculations.

---

## Step 6: Extract Ops Category from Notes

Ops Notes format: `Category|Team|FiscalQuarter`

**New Column:** `Ops Category`

**Formula (S2):**

```excel
=IFERROR(TRIM(LEFT(F2,FIND("|",F2)-1)),F2)
```

**Purpose:**

* Extracts the first component (category).
* Enables category-based filtering.

---

## Step 7: Calculate Variance

Variance = Revenue − Expense

**New Column:** `Variance`

**Formula (T2):**

```excel
=M2-N2
```

---

## Step 8: Filter Required Records

Apply filters:

* **Region:** Asia Pacific
* **Ops Category:** Fulfillment
* **Date:** ≤ 16 Feb 2024

---

## Step 9: Compute Total Variance (Filtered Rows Only)

**Formula:**

```excel
=SUBTOTAL(9,T2:T651)
```

**Purpose:**

* Sums only visible (filtered) rows.
* Returns total operational variance.

---


