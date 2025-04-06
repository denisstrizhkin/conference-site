# Student Conference Website

This is a website for a student conference. Students can create
accounts and provide basic info about themselves. Admins can monitor
created accounts, delete and manage them. Students can also submit different forms
with a possibility of future edits. Same for admins but they can see forms of all the users.

## How to run

### Get uv

You need `uv` to use this project. You can get it
[here](https://github.com/astral-sh/uv).

tl;dr:

- Linux & MacOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: I am sorry for your loss. 😔😭💀 (no I am not)

### Get the repo

Clone it ^_^

```console
> git clone https://github.com/denisstrizhkin/conference-site.git
```

Enter the directory ( • ⩊ • )

```console
> cd conference-site
```

### Prepare the environment

Install the required python version (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧

```console
> uv python install $(cat ./.python-version)
```

Install the deps Σ(°ロ°)

```console
> uv sync --dev
```

Activate the virtual Python evironment (o_O) !

```console
> source .venv/bin/activate
```

### Setup the SQLite database

Run `alembic` migrations to setup tables in the database.
This also gives you the `admin@example.com - admin` user which you can use for
administrative purposes. You **should** readjust admin user credentials for security.

```console
alembic upgrade head
```

### Finally

You can hopefully start it if I am not a moron (^_<)〜☆

```console
> fastapi dev src/main.py
```
