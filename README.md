# Inter

Live streaming platform for content creators.

Compatible with all WHIP streaming clients.

## Usage

> The contents of this section are derived from _Installation / How to Run_ Instructions in _Inter Part B Documentation_ as of this commit.

### Prerequisites

- Docker

### Cloning code

Clone the GitHub repository with `git` or [`gh`](https://cli.github.com).

```shell
git clone https://github.com/BaulkhamHillsHS/SE_Project_Matthew_Li --depth 1

# or
gh repo clone BaulkhamHillsHS/SE_Project_Matthew_Li -- --depth 1
```

### Creating the database

Use the schema at `./db/schema.sql` to create a SQLite3 database `.db` file.

### Environment variables

Create a public-private key pair for the [VAPID](https://datatracker.ietf.org/doc/html/rfc8292) process by using a trusted key generator such as the NPM [`web-push`](https://www.npmjs.com/package/web-push) `generate-vapid-keys` CLI:

```sh
pnpm dlx web-push generate-vapid-keys
```

Modify the public key in `./frontend/.env` to match the generated public key.
Set backend environment variables by writing the following to `./backend/.env`:

```env
EMOTE_SET=
DATABASE_PATH=
STREAM_WS_AUTH_KEY=
PRIVATE_VAPID_KEY=
```

and appending the following information on each line respectively:

- the ID of an emote set to be combined with the default global emote set, as an ASCII-encoded ULID in accordance with [https://github.com/ulid/spec](https://github.com/ulid/spec).
- the location of the database file either as

  an absolute path, or

  a relative path with respect to the `./backend` directory; for instance, the path to a database at `./db/database.db` is specified as `../db/database.db`.

- a cryptographically secure secret key for verifying user identity on the stream communication WebSocket endpoint with at least 256 bits of entropy.
- the generated [VAPID](https://datatracker.ietf.org/doc/html/rfc8292) private key associated with the generated public key.

### Starting the container and accessing the PWA

Run the following command to build an image and start the container.

```shell
docker compose up --build
```

Navigate to `localhost` or the server machine's internal LAN IP address at port 5001 to access the PWA.

## Internals

Internal documentation can be found in the Wiki section of this repository.
