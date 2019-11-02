create table request(
    id bigint primary key,
    email varchar(30) unique not null,
    accepted boolean not null default false,
    created_at date not null default CURRENT_TIMESTAMP
);

create table vote_request(
    ip_address varchar(4) not null,
    request_id bigint not null,
    primary key (ip_address, request_id)
);