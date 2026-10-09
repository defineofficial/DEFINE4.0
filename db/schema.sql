-- EventReach schema v1 (PostgreSQL 14+)
-- Matches docs/data-model.md. Run once on an empty database.
-- The database must use UTF8 encoding, or Hindi, Malayalam and Tamil names will not save.
-- Keep this file plain ASCII.

CREATE TYPE outcome AS ENUM (
  'pending', 'confirmed', 'declined', 'callback',
  'no_answer', 'voicemail', 'opted_out', 'wrong_number', 'failed'
);
CREATE TYPE stage AS ENUM ('invited', 'responded', 'registered', 'paid', 'attended');
CREATE TYPE channel AS ENUM ('call', 'sms', 'email', 'whatsapp', 'instagram');
CREATE TYPE campaign_status AS ENUM ('draft', 'ready', 'running', 'completed');

CREATE TABLE organizers (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email         text NOT NULL UNIQUE,
  name          text NOT NULL,
  role          text NOT NULL DEFAULT 'organizer' CHECK (role IN ('organizer', 'admin')),
  password_hash text NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE templates (
  key              text PRIMARY KEY,
  name             text NOT NULL,
  description      text NOT NULL,
  variables        jsonb NOT NULL DEFAULT '[]',
  keypad_options   jsonb NOT NULL DEFAULT '[]',
  requires_payment boolean NOT NULL DEFAULT false,
  default_channels channel[] NOT NULL DEFAULT '{call}'
);

CREATE TABLE campaigns (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organizer_id  uuid NOT NULL REFERENCES organizers(id),
  template_key  text NOT NULL REFERENCES templates(key),
  name          text NOT NULL,
  status        campaign_status NOT NULL DEFAULT 'draft',
  event         jsonb,                       -- title, starts_at, venue, city, fee_inr, capacity...
  languages     text[] NOT NULL DEFAULT '{}',
  channels      channel[] NOT NULL DEFAULT '{call}',
  poster_path   text,                        -- private storage path, served by signed URL
  voice_note_path text,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE translations (
  campaign_id         uuid NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  language            text NOT NULL,
  call_script         text NOT NULL,
  voicemail_script    text NOT NULL,
  email_subject       text,
  email_body          text,
  whatsapp_text       text,
  social_caption      text,
  back_translation_en text,
  approved            boolean NOT NULL DEFAULT false,
  PRIMARY KEY (campaign_id, language)
);

CREATE TABLE contacts (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organizer_id  uuid NOT NULL REFERENCES organizers(id),
  name          text NOT NULL,
  phone_enc     bytea NOT NULL,              -- encrypted E.164 number
  phone_hash    text NOT NULL,               -- salted hash, used for dedupe and opt-out matching
  phone_masked  text NOT NULL,               -- masked for display, the only form the API returns
  email         text,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organizer_id, phone_hash)
);

CREATE TABLE campaign_contacts (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id        uuid NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  contact_id         uuid NOT NULL REFERENCES contacts(id),
  language           text NOT NULL,
  segment            text NOT NULL DEFAULT 'General',
  stage              stage NOT NULL DEFAULT 'invited',
  last_outcome       outcome NOT NULL DEFAULT 'pending',
  attempts           int NOT NULL DEFAULT 0,
  registration_token text NOT NULL UNIQUE,   -- random, unguessable, goes in the personal link
  UNIQUE (campaign_id, contact_id)
);
CREATE INDEX ON campaign_contacts (campaign_id, language);
CREATE INDEX ON campaign_contacts (campaign_id, segment);
CREATE INDEX ON campaign_contacts (campaign_id, last_outcome);

CREATE TABLE call_attempts (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_contact_id uuid NOT NULL REFERENCES campaign_contacts(id) ON DELETE CASCADE,
  attempt_no          int NOT NULL,
  provider_call_id    text,                  -- Exotel call SID
  status              text NOT NULL,         -- answered, no_answer, busy, voicemail, failed
  language_used       text,
  started_at          timestamptz NOT NULL DEFAULT now(),
  duration_seconds    int,
  recording_path      text,
  delete_after        timestamptz            -- recordings removed after this date
);

CREATE TABLE responses (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_contact_id uuid NOT NULL REFERENCES campaign_contacts(id) ON DELETE CASCADE,
  channel             channel NOT NULL,
  raw_input           text,                  -- keypad digit or recognized speech
  outcome             outcome NOT NULL,
  created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE registrations (
  campaign_contact_id uuid PRIMARY KEY REFERENCES campaign_contacts(id) ON DELETE CASCADE,
  name                text NOT NULL,
  email               text,
  party_size          int NOT NULL DEFAULT 1,
  consented_at        timestamptz NOT NULL,  -- required, no registration without consent
  created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE payments (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_contact_id uuid NOT NULL REFERENCES campaign_contacts(id) ON DELETE CASCADE,
  provider_order_id   text NOT NULL UNIQUE,
  amount_inr          int NOT NULL,
  status              text NOT NULL DEFAULT 'created',   -- created, paid, failed, refunded
  paid_at             timestamptz
);

CREATE TABLE opt_outs (
  phone_hash  text PRIMARY KEY,
  source      text NOT NULL,                 -- keypad_9, reply_stop, manual
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_log (
  id         bigserial PRIMARY KEY,
  actor_id   uuid REFERENCES organizers(id),
  action     text NOT NULL,                  -- upload_contacts, export_contacts, view_recording
  object     text,
  at         timestamptz NOT NULL DEFAULT now()
);
