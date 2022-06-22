CREATE extension IF NOT EXISTS "uuid-ossp";
create table users
(
    id              serial
        constraint users_pk
            primary key,
    login           text not null,
    hashed_password text not null,
    company_name text not null,
    unique (login)
);
create table items
(
    uuid     uuid unique
        constraint items_pk
            primary key,
    name     text not null,
    type     text not null,
    parentId uuid references items (uuid) on delete cascade default null,
    date     timestamp,
    price    integer default null
);


