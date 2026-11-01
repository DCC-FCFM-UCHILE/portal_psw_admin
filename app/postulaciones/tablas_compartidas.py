from django.db import connection

DDL = """
CREATE TABLE IF NOT EXISTS commons_rulesapplications (
    id bigserial PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    short_description varchar(200) NOT NULL,
    document varchar(100) NOT NULL,
    deal varchar(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS applications_announcement (
    id bigserial PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    start date NOT NULL,
    "end" date NOT NULL,
    semester varchar(2) NOT NULL,
    year integer NOT NULL,
    rules_id bigint NOT NULL REFERENCES commons_rulesapplications(id)
);

CREATE TABLE IF NOT EXISTS applications_organization (
    id bigserial PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    organization_line varchar(50) NULL,
    rut varchar(50) NOT NULL,
    name varchar(200) NULL
);

CREATE TABLE IF NOT EXISTS applications_unit (
    id bigserial PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    name varchar(200) NULL,
    logo varchar(100) NULL,
    is_veto boolean NOT NULL DEFAULT false,
    organization_id bigint NULL REFERENCES applications_organization(id)
);

CREATE TABLE IF NOT EXISTS applications_candidate (
    id bigserial PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    email varchar(50) NOT NULL,
    names varchar(100) NULL,
    organization_id bigint NOT NULL REFERENCES applications_organization(id)
);

CREATE TABLE IF NOT EXISTS applications_application (
    id bigserial PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    title varchar(100) NOT NULL,
    short_description varchar(200) NULL,
    file varchar(100) NOT NULL,
    status varchar(2) NOT NULL DEFAULT 'CR',
    is_notified boolean NOT NULL DEFAULT false,
    announcement_id bigint NOT NULL REFERENCES applications_announcement(id),
    candidate_id bigint NOT NULL REFERENCES applications_candidate(id),
    unit_id bigint NULL REFERENCES applications_unit(id)
);

CREATE TABLE IF NOT EXISTS applications_approvedproject (
    id bigserial PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    title varchar(100) NOT NULL,
    description text NULL,
    semester varchar(10) NULL,
    year integer NULL,
    aux varchar(100) NULL,
    is_visible boolean NOT NULL DEFAULT false,
    "order" integer NULL,
    application_id bigint NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS applications_member (
    id bigserial PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    name varchar(100) NOT NULL,
    is_visible boolean NOT NULL DEFAULT false,
    project_id bigint NOT NULL REFERENCES applications_approvedproject(id)
);
"""


def crear():
    with connection.cursor() as cursor:
        cursor.execute(DDL)
