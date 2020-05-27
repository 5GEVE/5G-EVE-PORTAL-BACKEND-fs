-- Where the database scripts live
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "cube";
CREATE EXTENSION IF NOT EXISTS "earthdistance";

DROP TABLE IF EXISTS filedata;
DROP TABLE IF EXISTS sitedata;
DROP TABLE IF EXISTS filetosite;

CREATE TABLE filedata (
    _id 			    uuid DEFAULT uuid_generate_v4 (),
    filename	        VARCHAR NOT NULL,
    creator             VARCHAR NOT NULL,
    created_at          TIMESTAMP NOT NULL,
    updated_at          TIMESTAMP NOT NULL,

    PRIMARY KEY(_id)
);

CREATE TABLE sitedata (
    _id 			    uuid DEFAULT uuid_generate_v4 (),
    sitename            VARCHAR NOT NULL UNIQUE,
    PRIMARY KEY(_id)
);

CREATE TABLE filetosite (
    _id 			    uuid DEFAULT uuid_generate_v4 (),
    file_id             uuid NOT NULL,
    site_id             uuid NOT NULL,
    _status         VARCHAR NOT NULL,
    PRIMARY KEY(_id)
);