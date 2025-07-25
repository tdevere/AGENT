# Bible API Docker Deployment and Client Guide

This guide explains how to **self-host the Bible API server** using Docker (with Docker Compose on Windows 11) and how to build a **command-line Python client** that interacts with all the API’s endpoints. The instructions assume you have Docker Desktop installed (using WSL2 backend on Windows 11) and basic familiarity with command-line usage. The output of the client will be in JSON format for easy integration in scripts or automated environments.

## Prerequisites

* **Docker Desktop** (Windows 11) – Ensure it’s installed and running, with Linux containers enabled.
* **Git** (optional) – To clone repositories.
* (Optional) **Python 3** on your system – Only needed if you plan to run the client outside of Docker.

> **Note:** The Bible API requires a database (MySQL/MariaDB) and Redis cache. We will use Docker containers for these. The Bible text data will be imported into the database via a provided script.

## Setting Up the Bible API Server (Docker Compose)

Follow these steps to set up the Bible API server in Docker. We will create a Docker Compose file defining three services: **MySQL**, **Redis**, and the **Bible API web app** (a Ruby/Sinatra application).

### 1. Project Structure

Create a new directory for your project (this will be your new GitHub repo). Inside it, create the following files:

* `docker-compose.yml` – Define the services and their configuration.
* `Dockerfile` – Instructions to build the Bible API app image.

Your directory structure should look like:

```
/bible-api-selfhost
├── Dockerfile
└── docker-compose.yml
```

### 2. Write the Docker Compose Configuration

Open a text editor and create **`docker-compose.yml`** with the content below. This defines three services: a MySQL database, a Redis server, and the Bible API app. It also sets up a network and persistent storage for the database.

```yaml
version: "3.9"

services:
  db:
    image: mysql:8.0         # MySQL database for Bible API
    environment:
      MYSQL_ROOT_PASSWORD: example                # root password (required by MySQL image)
      MYSQL_DATABASE: bible_api                   # initial database name to create
      MYSQL_USER: bibleuser                       # non-root username for the app
      MYSQL_PASSWORD: biblepass                   # password for the above user
    volumes:
      - bible_db_data:/var/lib/mysql              # persistent data storage for MySQL
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine      # Redis cache
    volumes:
      - redis_data:/data       # persist Redis data (optional)

  api:
    build: .                   # build using Dockerfile in current directory
    depends_on:
      - db
      - redis
    environment:
      # Database and Redis connection URLs for the app
      DATABASE_URL: "mysql2://bibleuser:biblepass@db/bible_api"
      REDIS_URL: "redis://redis:6379"
      RACK_ENV: production     # run in production mode (Sinatra)
    ports:
      - "4567:4567"            # expose API on http://localhost:4567
    # Command to run the server; bind to 0.0.0.0 so it’s accessible outside container
    command: bundle exec ruby app.rb -o 0.0.0.0 -p 4567

volumes:
  bible_db_data:
  redis_data:
```

**Notes:**

* The **MySQL** service uses environment variables to set up the database on first run. We create a database named `bible_api` and a user `bibleuser` with password `biblepass`. The Bible API app will use this user to connect.
* The **Redis** service uses the default configuration (no password, default port 6379) since this is a local deployment.
* The **API** service will be built from our custom Dockerfile (in the same directory). It depends on `db` and `redis` so that those start first. We pass `DATABASE_URL` and `REDIS_URL` environment variables pointing to the other containers (the hostnames `db` and `redis` are automatically resolved via Docker Compose networking). We also publish port 4567 to the host so you can access the API at **[http://localhost:4567](http://localhost:4567)**.
* The `command` for the API uses `bundle exec ruby app.rb -o 0.0.0.0 -p 4567` to start the Sinatra app, binding to all interfaces on port 4567. This ensures the server is reachable from outside the container (by default Sinatra might bind to localhost inside container only).

### 3. Write the Dockerfile for the API Service

Next, create the **`Dockerfile`**. This will build an image for the Bible API Ruby application, including all dependencies (Ruby gems and the Bible data).

```dockerfile
# Use an official Ruby image (slim variant for smaller size)
FROM ruby:3.3.6-slim

# Install build dependencies (for gems) and MySQL client library
RUN apt-get update && \
    apt-get install -y build-essential libmysqlclient-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone the Bible API source code (includes submodule with Bible texts)
RUN git clone --recursive https://github.com/seven1m/bible_api.git /app

# Install Bundler and the required Ruby gems
RUN gem install bundler && bundle install

# Expose the port (for documentation; actual binding is done in docker-compose)
EXPOSE 4567

# Default command (will be overridden by docker-compose command)
CMD ["bundle", "exec", "ruby", "app.rb", "-o", "0.0.0.0", "-p", "4567"]
```

**What this Dockerfile does:**

* **Base Image:** It starts from `ruby:3.3.6-slim`, which contains Ruby 3.3 (the version specified by the app) in a minimal Debian environment. (Ruby 3.3.x is required per the app’s Gemfile.)
* **Packages:** Installs system packages needed to compile gems and communicate with MySQL. The `mysql2` gem needs MySQL client libraries, so we install `libmysqlclient-dev` (this also pulls in the MySQL client library). We also install build tools for any native gem compilation.
* **Source Code:** Clones the official Bible API repository from GitHub into the image (including its submodules with open Bible texts). This contains the Ruby app code and data.
* **Bundler:** Installs Ruby Bundler and then runs `bundle install` to install all gem dependencies (Sinatra, Puma, mysql2, etc.). This includes the script for importing Bible texts and all code needed.
* **Expose/Command:** Documents port 4567 and sets a default command to run the app. (We override the command in Compose to ensure it starts correctly, but this is a safe default.)

### 4. Build and Launch the Containers

Now that you have `docker-compose.yml` and `Dockerfile` ready, you can build the application image and start all the services:

1. **Open a terminal** in the project directory (where the compose file is).
2. **Build the images** and start the services:

   ```bash
   docker compose up -d --build
   ```

   This will:

   * Build the `api` image using the Dockerfile (downloading the Ruby base image and then cloning the app and installing gems). This step may take a few minutes on first build.
   * Start the MySQL (`db`) and Redis (`redis`) containers, then start the `api` container. We run in detached mode (`-d`) so that it runs in the background.
3. **Verify containers are running:** Use `docker compose ps` to see the status. You should see `db`, `redis`, and `api` services all up. Give MySQL a few seconds to finish initialization (the healthcheck will retry until MySQL is ready).

At this point, the database is empty and the API server might not yet serve verses. In fact, the app may return a message or error if you query it now, because the Bible texts are not imported yet. In the app’s instructions, after setting up the database you must run the import script to load the Bible data. We will do that next.

### 5. Import Bible Data into the Database

The Bible API comes with an `import.rb` script that loads all the Bible verses (from the submodule data) into the MySQL database. We need to run this once inside the `api` container. Once imported, the data will persist in the MySQL volume.

Run the import by executing the following command in your terminal:

```bash
docker compose exec api bundle exec ruby import.rb
```

This command opens a one-time session in the running `api` container and executes the import script. You should see output as it processes books and chapters. This may take a few minutes as it inserts all verses into the MySQL database. (There are many thousands of verses to import.)

**Tip:** The above command uses the environment variables we set (DATABASE\_URL, REDIS\_URL) inside the container. It’s equivalent to the manual steps in the original README, which created the DB and ran the import script. We have already created the DB and user via the MySQL container’s env, so the script should connect and populate the `bible_api` database.

Once this finishes, the data is loaded. The MySQL data volume (`bible_db_data`) ensures that if you restart the containers later, you **do not need to re-import** unless you deliberately remove the volume. (The imported data is stored persistently.)

### 6. Verify the API Server

Now everything should be set up. Let’s verify that the API is serving requests:

* **Check logs:** You can view logs from the API service with `docker compose logs -f api`. You should see that the Sinatra/Puma server started without errors. It might log incoming requests as you test it.

* **Test a verse lookup:** Try querying a known verse using curl or a browser. For example, John 3:16 is a popular verse:

  ```bash
  curl http://localhost:4567/John+3:16
  ```

  You should receive a JSON response containing the verse text and metadata. For example (formatted for readability):

  ```json
  {
    "reference": "John 3:16",
    "verses": [
      {
        "book_id": "JHN",
        "book_name": "John",
        "chapter": 3,
        "verse": 16,
        "text": "For God so loved the world, that he gave his one and only Son, ...\n"
      }
    ],
    "text": "For God so loved the world, that he gave his one and only Son, ...\n",
    "translation_id": "web",
    "translation_name": "World English Bible",
    "translation_note": "Public Domain"
  }
  ```

  If you see a JSON with the verse text, congratulations – your API server is up and running! 🎉

  > **Note:** By default the API uses the **World English Bible (WEB)** translation for verses. You can specify a different translation by adding a `translation` query parameter. For example:
  > `http://localhost:4567/John+3:16?translation=kjv`
  > would return the verse from the King James Version instead of WEB. The Bible API supports multiple translations such as KJV, ASV, etc., in addition to the default WEB.

* **Test other endpoints:** The API has a structured “data” endpoint as well. For example:

  * List available translations:

    ```bash
    curl http://localhost:4567/data
    ```

    This should return a JSON array of translations with their identifiers, names, and languages.
  * List books of a translation (e.g., WEB):

    ```bash
    curl http://localhost:4567/data/web
    ```

    You should get JSON data listing the books in that translation.
  * Get chapters of a book (e.g., the Gospel of John in WEB):

    ```bash
    curl http://localhost:4567/data/web/JHN
    ```

    This returns information on the book of John, likely including a list of chapters or related links.
  * Get an entire chapter’s verses (e.g., John chapter 3):

    ```bash
    curl http://localhost:4567/data/web/JHN/3
    ```

    This should return the verses in John chapter 3 as a JSON array.
  * Random verse:

    ```bash
    curl http://localhost:4567/data/web/random
    ```

    (Each call returns a random verse from the whole Bible in WEB translation.)
    The random endpoint can be filtered by specifying book IDs or `OT`/`NT`. For example, `/data/web/random/JHN` gives a random verse from the book of John, and `/data/web/random/NT` gives a random verse from the New Testament.

These manual tests confirm that the server is working. You now have a fully functional Bible API server running locally in Docker.

## Building the API Client (Python CLI)

Next, we will create a **command-line client** that can interact with the API server and perform all supported operations. We’ll use Python (which the user prefers, and is a good choice for quick scripting) and ensure the client runs in a headless environment (no GUI, pure CLI) and outputs JSON.

### 1. Choosing Python vs Node

Both Python and Node.js could be used to build a CLI client. Given that you’re more familiar with Python and want a straightforward command-line tool producing JSON output, we will proceed with **Python**. Python has an advantage of a simple syntax and a rich ecosystem (we’ll use the `requests` library for HTTP calls). We will also use a slim Python Docker image to keep the environment lightweight, as you suggested (the official `python:3.x-slim` images are suitable).

### 2. Creating the Python Client Script

Inside your project directory (e.g., `bible-api-selfhost`), create a new folder for the client or just a new file. For clarity, let’s create a **`client`** directory to hold the client code. Inside it, create **`client.py`** – this will be the CLI program. Also create a **`requirements.txt`** to list Python dependencies (we only need `requests` for now).

Project structure update:

```
/bible-api-selfhost
├── Dockerfile
├── docker-compose.yml
└── client/
    ├── client.py
    └── requirements.txt
```

**`client/requirements.txt`:**

```text
requests
```

Now, open **`client.py`** and add the following code:

```python
#!/usr/bin/env python3
import argparse
import requests
import sys
import json

# Default server URL (inside Docker, use service name; outside Docker, use localhost)
DEFAULT_SERVER_URL = "http://api:4567"

# Setup command-line argument parsing
parser = argparse.ArgumentParser(description="Bible API CLI Client")
subparsers = parser.add_subparsers(dest="command", required=True, help="Operation to perform")

# Sub-command: verse (get a specific verse or passage by reference)
verse_parser = subparsers.add_parser("verse", help="Retrieve verse/passage by reference")
verse_parser.add_argument("reference", help="Bible reference (e.g. 'John 3:16' or 'Genesis 1:1-3')")
verse_parser.add_argument("--translation", "-t", default=None, help="Translation ID (default: WEB)")

# Sub-command: translations (list all translations)
subparsers.add_parser("translations", help="List available Bible translations")

# Sub-command: books (list books of a translation)
books_parser = subparsers.add_parser("books", help="List books for a translation")
books_parser.add_argument("--translation", "-t", default="web", help="Translation ID (default: web)")

# Sub-command: chapters (list chapters of a given book)
chapters_parser = subparsers.add_parser("chapters", help="List chapters for a book in a translation")
chapters_parser.add_argument("book", help="Book ID (e.g. GEN, JHN, etc.)")
chapters_parser.add_argument("--translation", "-t", default="web", help="Translation ID (default: web)")

# Sub-command: random (get a random verse, optionally constrained to books or testament)
random_parser = subparsers.add_parser("random", help="Get a random verse")
random_group = random_parser.add_mutually_exclusive_group()
random_group.add_argument("--books", help="Comma-separated book IDs for limiting the range (e.g. GEN,EXO or JHN)")
random_group.add_argument("--testament", choices=["OT", "NT"], help="Limit to Old Testament or New Testament")

# Global option for specifying server base URL (for flexibility)
parser.add_argument("--server", default=DEFAULT_SERVER_URL, help=f"Base URL of the Bible API server (default: {DEFAULT_SERVER_URL})")

# Parse the arguments
args = parser.parse_args()

# Determine base server URL
base_url = args.server.rstrip("/")  # remove trailing slash if any

try:
    if args.command == "verse":
        # Construct endpoint for verse lookup (user input style)
        ref = args.reference.replace(" ", "+")  # space to plus for URL
        url = f"{base_url}/{ref}"
        if args.translation:
            # Append translation param if provided
            url += f"?translation={args.translation}"
        response = requests.get(url)
    elif args.command == "translations":
        url = f"{base_url}/data"
        response = requests.get(url)
    elif args.command == "books":
        url = f"{base_url}/data/{args.translation}"
        response = requests.get(url)
    elif args.command == "chapters":
        # Book ID and translation
        trans = args.translation
        book = args.book
        url = f"{base_url}/data/{trans}/{book}"
        response = requests.get(url)
    elif args.command == "random":
        # Base random URL
        url = f"{base_url}/data"
        # Use specified translation or default to 'web'
        trans = "web"
        # Check if the API server base might include translation (if base is /data already or not)
        # We'll explicitly include translation for clarity
        url += f"/{trans}/random"
        if args.books:
            # e.g. /data/web/random/JHN or multiple books
            url += f"/{args.books}"
        elif args.testament:
            # /data/web/random/OT or /NT
            url += f"/{args.testament}"
        response = requests.get(url)
    else:
        parser.error("Unknown command")  # This should not happen due to required=True

    # If we got a response, handle it
    if not response.ok:
        print(f"Error: HTTP {response.status_code}", file=sys.stderr)
        sys.exit(1)
    data = response.json()
    # Print the JSON response to stdout (pretty-print with indent for readability)
    print(json.dumps(data, indent=2))
except requests.RequestException as e:
    print(f"Request failed: {e}", file=sys.stderr)
    sys.exit(1)
```

**Explanation of the client script:**

* We use Python’s `argparse` to create a CLI with subcommands:

  * `verse` – Retrieve a specific verse or passage by reference (e.g., "John 3:16" or a range like "John 3:16-18"). This maps to the user-friendly reference API. We allow an optional `--translation` (e.g., `--translation kjv`). If no translation is given, the server’s default (WEB) is used.
  * `translations` – List all available translations. This calls the `/data` endpoint which returns all translations (identifier, name, language).
  * `books` – List the books for a given translation (default is "web" if not specified). This calls `/data/<translation>` which returns all books of that translation.
  * `chapters` – List chapters for a specified book in a translation. This calls `/data/<translation>/<BookID>` (for example, `/data/web/JHN` for the Book of John) to retrieve info about that book, including chapters.
  * `random` – Get a random verse. By default it will return a random verse from the entire Bible (using the default translation). You can constrain the random selection by book or testament: use `--books "MAT,MRK,LUK,JHN"` to get a random verse from a set of books, or `--testament OT`/`NT` to get a random verse from only the Old or New Testament.
* The script also provides a global `--server` option. This allows specifying the base URL of the API server. It defaults to `"http://api:4567"`, which is the hostname if the client is run inside Docker Compose (since the compose service for the API is named `api`). If you plan to run the client **outside** of Docker (e.g., on your host machine), you can use `--server http://localhost:4567` to point it to the correct address.
* We use the `requests` library to perform HTTP GET requests to the API endpoints based on the command. The JSON response is then printed to stdout using Python’s `json.dumps` with indentation for readability. This way, the output is valid JSON that can be piped to other tools or simply read by the user.
* Basic error handling is included: if the HTTP response is not OK (e.g., 404 or 500), it prints an error to stderr and exits with a non-zero status. If the request fails (e.g., connection error), it also prints an error message.
* The script is meant to be simple and does not do extensive validation beyond what the API does. It assumes the server will handle bad inputs (e.g., unknown references) by returning an error or empty result.

### 3. Containerizing the Python Client (Optional)

To run this client in a headless, automated environment, it's convenient to have it containerized as well. We can use a lightweight Docker image for Python.

Create a **`Dockerfile`** for the client (for example, `client/Dockerfile`) with the following content:

```dockerfile
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the client script
COPY client.py .

# Default entrypoint to run the client
ENTRYPOINT ["python", "client.py"]
```

This uses Python 3.11 slim image, installs `requests` from `requirements.txt`, and copies the `client.py`. The entrypoint is set to run the client script, so that any arguments passed to the container will be forwarded to `client.py`.

Now, integrate this into your Docker Compose setup. Edit your `docker-compose.yml` to add a service for the client. For example:

```yaml
  client:
    build: 
      context: ./client    # build using Dockerfile in client directory
    depends_on:
      - api                # ensure API service is up before using client
    networks:
      - default            # uses the default network, can reach "api" service
    # No ports needed since it will be used via `docker compose run`
    # The ENTRYPOINT in Dockerfile handles the command execution
```

We add a `client` service that will be built from the `client/` directory. We don't need to run it as a long-running service; instead, we will invoke it on-demand with `docker compose run`. We also set it to depend on the `api` service so that the API is running when we use the client.

### 4. Using the Client

With the client container built, you can run it to perform various operations. Since we declared an entrypoint, we can invoke subcommands directly. Here are some examples of how to use the client:

* **List translations:**

  ```bash
  docker compose run --rm client translations
  ```

  This will output a JSON array of available Bible translations (with their `identifier`, `name`, and `language`). For example, you’ll see entries like `"identifier": "kjv", "name": "King James Version", "language": "English"`, etc., including the default `"web"` (World English Bible).

* **List books of a translation:**

  ```bash
  docker compose run --rm client books --translation kjv
  ```

  This will fetch all books in the King James Version. The JSON output will likely contain an array of books (each with an `id` like GEN, EXO, MAT, etc., and possibly the name). If you omit `--translation`, it defaults to `web`. For example, try:

  ```bash
  docker compose run --rm client books  
  ```

  to list books in the default translation (WEB).

* **List chapters of a book:**

  ```bash
  docker compose run --rm client chapters JHN --translation web
  ```

  This queries the chapters in the book of John (JHN) for the WEB translation. The output JSON will show information about the book of John, presumably including the number of chapters or a list of chapter indices available. (If you look at this JSON, you should see how chapters are represented. The Bible API’s structured `/data` endpoints typically include links or chapter numbers for navigation.)

* **Fetch a specific verse or passage:**

  ```bash
  docker compose run --rm client verse "John 3:16-17"
  ```

  This will call the API to retrieve John 3:16-17. The output will be JSON containing the reference and verses in that range. By default this uses WEB translation; to specify another translation, add `-t` (or `--translation`), for example:

  ```bash
  docker compose run --rm client verse "John 3:16" -t kjv
  ```

  This asks for John 3:16 in King James Version. Under the hood, the client is calling the endpoint `/John+3:16?translation=kjv` on the API. The API expects a reference string and optional translation code, exactly what our client provides.

* **Fetch a whole chapter or multiple verses:** You can use the `verse` command for that as well, by specifying a range or just the chapter without verse numbers. For example:

  ```bash
  docker compose run --rm client verse "Jude 1"
  ```

  Jude has only one chapter, so this might be interpreted as the first verse of Jude by default (due to how the API handles single-chapter books). If you wanted the whole book of Jude, you'd need a special parameter (the API supports a flag for single-chapter books as mentioned in the docs, but our client doesn’t expose that toggle explicitly; it can still be accessed by adding the query parameter `single_chapter_book_matching=indifferent` via the reference string if needed).

* **Get a random verse:**

  ```bash
  docker compose run --rm client random
  ```

  This will return a random verse from the entire Bible (default translation WEB). The JSON output includes the translation info and a `random_verse` object with book, chapter, verse, and text. You can also limit the range:

  * Random from specific books:

    ```bash
    docker compose run --rm client random --books JHN,MAT
    ```

    (This would give a random verse from either John or Matthew.)
  * Random from New Testament only:

    ```bash
    docker compose run --rm client random --testament NT
    ```

    These options correspond to API calls like `/data/web/random/JHN,MAT` or `/data/web/random/NT`.

**Note:** When running via Docker Compose as above, we use `docker compose run --rm client ...` which will spin up a temporary container for the client, execute the command, then remove the container (`--rm`). The client container is on the same Docker network as the API, so it can reach the API by the service name `api` (which is why our default `--server` is `http://api:4567`). If you run the client on your host machine instead, use `--server http://localhost:4567` to direct it to your local API server.

### 5. (Optional) Running the Client Locally

If you prefer to run the client directly on your host (outside Docker), you can do so as well:

* Ensure you have Python 3 installed on your system.
* Install the requests library: `pip install requests`.
* Set the `SERVER_URL` environment variable or use the `--server` option to point to your running API (e.g., `http://localhost:4567`).
* Run the script with the desired subcommand, e.g.:

  ```bash
  python client.py verse "Genesis 1:1-3" --server http://localhost:4567
  ```

This should output the JSON for Genesis 1:1-3 from the default translation.

---

You now have both the server and client set up. The **Bible API server** is running in a Dockerized environment, serving JSON data for scripture queries, and the **Python client** provides a convenient way to fetch data from the command line. The client supports all operations exposed by the API – getting specific verses or passages by reference (with optional translation), listing translations, listing books and chapters, and retrieving random verses.

With these tools, you can integrate Bible verse retrieval into scripts or applications easily. For example, you might call the client from a shell script or a CI pipeline to fetch a verse of the day, etc. The output being JSON makes it easy to parse programmatically or format as needed.

Feel free to commit this code to your GitHub repository. You might include this README (or integrate these instructions into your repo’s README) so others (or future you) can follow the setup. Happy coding, and enjoy exploring the Bible API! 📖🚀
