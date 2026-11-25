-- Northvale University portal - database schema and fictional sample data.
-- Idempotent: safe to run at every application start-up.

CREATE TABLE IF NOT EXISTS departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(120) NOT NULL UNIQUE,
    head        VARCHAR(120),
    building    VARCHAR(60),
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS announcements (
    id            SERIAL PRIMARY KEY,
    title         VARCHAR(200) NOT NULL,
    body          TEXT NOT NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    published_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_announcements_published
    ON announcements (published_at DESC);

INSERT INTO departments (name, head, building, description) VALUES
 ('Computer Science', 'Prof. Amel Kaci', 'Block A',
  'Software engineering, artificial intelligence, networks and cloud computing. Home of the Cloud & Distributed Systems Lab.'),
 ('Electrical Engineering', 'Prof. Karim Benali', 'Block B',
  'Power systems, electronics, embedded systems and telecommunications.'),
 ('Mathematics', 'Dr. Nadia Haddad', 'Block C',
  'Pure and applied mathematics, statistics and operations research.'),
 ('Economics & Management', 'Dr. Yanis Mansouri', 'Block D',
  'Economics, finance, accounting and business management programmes.'),
 ('Languages & Literature', 'Dr. Lina Ferhat', 'Block E',
  'English, French and Arabic language studies, translation and literature.')
ON CONFLICT (name) DO NOTHING;

INSERT INTO announcements (title, body, department_id, published_at)
SELECT t.title, t.body, d.id, NOW() - t.age
FROM (VALUES
  ('Welcome to the 2026/2027 academic year',
   'Classes start on Sunday. Timetables are available at the student office and on this portal.',
   NULL, INTERVAL '10 days'),
  ('Cloud Computing project deadline',
   'Groups must submit their report, source code and video demonstration before December 4.',
   'Computer Science', INTERVAL '6 days'),
  ('Library extended opening hours',
   'During the exam period the central library is open from 08:00 to 22:00, including Saturdays.',
   NULL, INTERVAL '3 days'),
  ('Embedded Systems workshop',
   'A hands-on Arduino and Raspberry Pi workshop takes place on Thursday in Lab B-12.',
   'Electrical Engineering', INTERVAL '1 day')
) AS t(title, body, dept, age)
LEFT JOIN departments d ON d.name = t.dept
WHERE NOT EXISTS (SELECT 1 FROM announcements);
