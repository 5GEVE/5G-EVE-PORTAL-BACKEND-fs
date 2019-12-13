-- Where the database scripts live
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "cube";
CREATE EXTENSION IF NOT EXISTS "earthdistance";

DROP TABLE IF EXISTS bzuser;

CREATE TABLE uploaded_file (
    _id 			  uuid DEFAULT uuid_generate_v4 (),
    name 		    VARCHAR NOT NULL,
    sites           VARCHAR[],
    PRIMARY KEY(_id),
    CONSTRAINT FK_user_email FOREIGN KEY (user_email) REFERENCES user(email)
);

CREATE TABLE user (
    _id 			  uuid DEFAULT uuid_generate_v4 (),
    email 		    VARCHAR NOT NULL,
    roles           VARCHAR[],
    groups          VARCHAR[],
    PRIMARY KEY(_id)
);
