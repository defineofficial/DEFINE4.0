# EventReach web

This folder receives the code generated from the Figma designs (Next.js and Tailwind).

## Rules for generated code

- One screen per branch, named `ui/<screen-name>`, for example `ui/organizer-new-campaign`.
- Do not hand-edit generated files without telling the screen's owner (F1 organizer flow, F2 dashboard, F3 registration and payment).
- The owner checks the result against Figma before it is merged.

## Talking to the API

Set the base URL in `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the mock API first (see the root README). Every screen can fetch real-looking data from day one.

Build screens against `docs/openapi.json`. To get typed API calls:

```bash
npx openapi-typescript ../docs/openapi.json -o src/api/schema.d.ts
```

When B2 or B1 replaces a mock endpoint with real logic, the field names stay the same, so nothing in the screens changes.

## Useful mock links for the registration page

The mock API has these personal links ready (replace `localhost:3000` with your web address):

| Link | Person | Language | Stage |
|---|---|---|---|
| `/r/tok_ct_001` | Anjali Menon | Malayalam | registered (unpaid) |
| `/r/tok_ct_002` | Rahul Nair | Malayalam | paid |
| `/r/tok_ct_004` | Arjun Verma | Hindi | invited |
| `/r/tok_ct_008` | Kiran Rao | English | registered (unpaid) |
| `/r/tok_ct_005` | Meera Iyer | Tamil | responded |

Use `/r/not-a-real-token` to design the "link not valid" state.
