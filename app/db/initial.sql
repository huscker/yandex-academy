create extension if not exists "uuid-ossp";
create table if not exists shop_units
(
    id     uuid unique
        constraint items_pk
            primary key,
    name     text not null,
    type     text not null,
    parentId uuid references shop_units (id) on delete cascade default null,
    date     timestamp with time zone,
    price    integer default null
);
create table if not exists snapshot
(
    id     uuid references shop_units(id) on delete cascade,
    name     text not null,
    type     text not null,
    parentId uuid references shop_units(id) on delete cascade default null,
    date     timestamp with time zone,
    price    integer
);


