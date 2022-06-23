create extension if not exists "uuid-ossp";
create table if not exists shop_units
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
create table if not exists snapshot
(
    uuid     uuid ,
    name     text not null,
    type     text not null,
    parentId uuid references shop_units(uuid) on delete cascade default null,
    date     timestamp,
    price    integer
);


