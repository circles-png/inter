# Inter

Live streaming platform for content creators.

Compatible with all WHIP streaming clients.

## Usage

1. Clone this repository, either with `git`

    ```bash
    git clone https://github.com/BaulkhamHillsHS/SE_Project_Matthew_Li
    ```

    or [`gh`](https://cli.github.com).

    ```bash
    gh repo clone BaulkhamHillsHS/SE_Project_Matthew_Li
    ```

2. Ensure you have [Python 3.13](https://www.python.org/downloads/) or higher, [Node.js 25](https://nodejs.org/en/download/current), and [pnpm](https://pnpm.io) installed.
3. In `./frontend`, install dependencies with:

    ```bash
    pnpm i
    ```

4. In `./backend`, install dependencies with:

    ```bash
    poetry install
    ```

5. Add environment variables in `./backend/.env`
   - `EMOTE_SET` - the ID of an additional 7TV emote set to load from
   - `DATABASE_PATH` - the path of the SQLite3 database  relative to `./backend`
6. To run the application, execute `./scripts/run.nu`.
7. Open your web browser and navigate to `http://localhost:5001` to access the frontend interface.

### via Github Actions

1. Download an artifact from the latest workflow run and unzip.
2. `cd` into its backend folder,
3. `poetry install` or `python -m pip install -r requirements.txt` to install dependencies.
4. Run with `PROD=1 poetry run hypercorn "src/inter:create_app()" -b 0.0.0.0:5001`.

## Internals

Internal documentation can be found in the Wiki section of this repository.
