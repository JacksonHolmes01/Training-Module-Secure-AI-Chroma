# Install & Verify Docker

This lab runs Chroma and its gateway inside **Docker containers**. A container is a lightweight, isolated package that includes a program and everything it needs to run.

Using a container means:
- you do not install Chroma or NGINX directly on your computer
- everyone in the class runs the exact same version
- you can delete everything and start over with one command

---

## Install Docker

Pick **one** option.

### Option A: Docker Desktop (macOS, Windows, Linux)
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Install it and open it
3. Wait until it says Docker is running

On Windows, open Docker Desktop **Settings → Resources → WSL Integration** and turn it on for Ubuntu.

### Option B: Colima (macOS, free and command-line only)
If you use Homebrew, run:

```bash
brew install colima docker docker-compose
colima start --cpu 4 --memory 8
```

Then tell Docker where the Compose plugin lives:

```bash
mkdir -p ~/.docker
echo '{"cliPluginsExtraDirs":["/opt/homebrew/lib/docker/cli-plugins"]}' > ~/.docker/config.json
```

> Colima only shares your **home folder** with containers. Keep this project somewhere inside your home folder (for example `~/labs`), not in `/tmp`.

---

## Verify Docker is installed

Run:

```bash
docker version
```

### What success looks like
You should see two sections: **Client** and **Server**.

If you only see **Client** and an error such as `Cannot connect to the Docker daemon`, Docker is installed but not running. Start Docker Desktop (or run `colima start`) and try again.

---

## Verify Docker Compose is installed

Run:

```bash
docker compose version
```

### What success looks like
You should see a version number, for example:

```
Docker Compose version v2.x.x
```

If you see `docker: 'compose' is not a docker command`, Compose is missing. Reinstall Docker Desktop, or repeat the Colima step that writes `~/.docker/config.json`.

---

## Verify Docker can run a container

Run:

```bash
docker run --rm hello-world
```

### What success looks like
You should see a message that starts with:

```
Hello from Docker!
```

This confirms Docker can download images and run containers.

---

## Verify git, openssl, curl, and python3

You will also use:
- `git` to download the lab
- `openssl` to generate tokens and a TLS certificate
- `curl` to send requests
- `python3` to read JSON responses

```bash
git --version
openssl version
curl --version | head -1
python3 --version
```

Each should print a version number. On Ubuntu/WSL, install any that are missing with `sudo apt update && sudo apt install -y git openssl curl python3`.

Next: [Project Setup](03-project-setup.md)
