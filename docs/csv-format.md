# Contact list format (CSV)

This is what the organizer uploads in step 4 of the campaign flow. It is also the brief for the designers: the import screen must show the report described at the bottom.

Starter files: `docs/samples/sample-contacts.csv` (all valid) and `docs/samples/sample-contacts-with-errors.csv` (every kind of problem). The numbers in them are placeholders. Replace them with numbers of people who agreed to receive test calls before anyone makes a real call.

## Columns

| Column | Required | Accepted names | Notes |
|---|---|---|---|
| name | Yes | name, full name, contact name | Up to 100 characters. Any script works (Hindi, Malayalam, Tamil) |
| phone | Yes | phone, mobile, mobile number, phone number, contact number, number | See phone formats below |
| language | No | language, lang, preferred language | `en`, `hi`, `ml`, `ta`, or the names English, Hindi, Malayalam, Tamil |
| segment | No | segment, group, category | Free text, for example Students, Faculty, Alumni. Empty becomes General |
| email | No | email, email address, mail | Used for the email channel |

Column order does not matter. Extra columns are ignored. Capital letters, spaces and underscores in headers do not matter.

## Phone formats that work

All of these become `+919876543210`:
`9876543210`, `98765 43210`, `+91 98765-43210`, `09876543210`, `919876543210`, `(98765) 43210`, `0091 98765 43210`.

Numbers from other countries work when they start with `+` and have 8 to 15 digits, for example `+44 7700 900123`.

## File rules

- Save as **CSV UTF-8**. In Excel: File, Save As, "CSV UTF-8 (Comma delimited)". Other formats damage Hindi, Malayalam and Tamil names, and the upload is refused with an explanation.
- Commas, semicolons and tabs are all accepted as separators.
- Up to 5000 people and 2 MB per file.
- In Excel, format the phone column as **Text** before typing numbers. Otherwise long numbers can turn into `9.8765E+09`, and the importer will flag them.
- Blank lines are ignored.
- Row numbers in messages match the spreadsheet: the header is row 1, the first person is row 2.

## What happens to each row

| Situation | Result |
|---|---|
| Everything fine | Imported |
| Name missing, or phone invalid or missing | **Skipped**, listed under errors with the reason |
| Same number twice in the file | The second one is **skipped**: "Duplicate of row N" |
| Number already in this campaign | **Skipped**: "Already in this campaign." Uploading the same file again adds nobody |
| Number that opted out in any campaign | **Skipped**: "This number has opted out." |
| Language missing or not supported yet | **Imported** with the default language, listed under warnings |
| Email looks invalid | **Imported** without the email, listed under warnings |

## The import report (what the screen shows)

`POST /campaigns/{id}/audience` returns:

```json
{
  "total_rows": 10,
  "imported": 5,
  "skipped": 5,
  "errors": [
    { "row": 5, "field": "name", "message": "Name is missing." },
    { "row": 6, "field": "phone", "message": "Phone number has 8 digits. Expected 10, or 12 with the country code 91." }
  ],
  "warnings": [
    { "row": 3, "field": "email", "message": "Email looks invalid and was left out." }
  ],
  "languages_found": { "ml": 1, "hi": 1, "ta": 1, "en": 2 },
  "segments_found": { "Students": 1, "Faculty": 1, "Alumni": 1, "Guests": 1, "General": 1 }
}
```

Suggested screen layout:

1. A summary line: "5 of 10 people imported, 5 skipped".
2. Two small tables: languages found and segments found, so the organizer sees whether the list looks right.
3. An errors table (row, what is wrong, how to fix it), clearly marked as skipped.
4. A warnings table, marked as imported but worth checking.
5. A "Download the starter file" link (`GET /audience/template.csv`) and a "Fix the file and upload again" button. Re-uploading is safe.

If the whole file cannot be read, the API returns an error with a plain sentence (for example "Missing required column: phone. Columns found: name, city."). Show that sentence as is.

## Privacy notes

- The report and every API response show only masked numbers (`+91 90••• ••013`).
- Numbers are stored as a salted hash for duplicate and opt-out checks. The real database also keeps an encrypted copy, because calls need it.
- Uploading a list is recorded in the audit log in the real version.
