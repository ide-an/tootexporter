create table users (
  id                        bigserial not null,
  access_token              varchar(255),
  mastodon_id               bigint,
  created_at                timestamp not null,
  updated_at                timestamp not null,
  constraint pk_users primary key (id))
;
create unique index idx_users_mastodon_id on users (mastodon_id);

create table snapshots (
  id                        bigserial not null,
  owner                     bigint,
  snap_type                 varchar(16), -- toot or fav
  snap_start                timestamp not null,
  snap_end                  timestamp not null,
  status                    varchar(16), -- wait or doing or done
  bucket                    varchar(255), -- AWS S3 bucket
  key                       varchar(255), -- AWS S3 key
  created_at                timestamp not null,
  updated_at                timestamp not null,
  constraint pk_snapshots primary key (id))
;
alter table snapshots add constraint fk_snapshots_owner foreign key (owner) references users (id);
