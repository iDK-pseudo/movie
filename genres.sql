create table userdata (
	username text not null primary key,
	email text not null unique,
	password text not null,
	name text not null
);