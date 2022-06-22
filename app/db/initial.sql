CREATE extension IF NOT EXISTS "uuid-ossp";
create table shop_units
(
    uuid     uuid unique
        constraint items_pk
            primary key,
    name     text not null,
    type     text not null,
    parentId uuid references shop_units (uuid) on delete cascade default null,
    date     timestamp,
    price    integer default null
);
create table snapshot
(
    uuid     uuid ,
    name     text not null,
    type     text not null,
    parentId uuid ,
    date     timestamp,
    price    integer
);


