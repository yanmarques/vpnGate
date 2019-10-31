create table request(
    id bigint primary key not null,
    email varchar(30) unique not null,
    accepted boolean not null default false,
    created_at date not null default CURRENT_TIMESTAMP
);