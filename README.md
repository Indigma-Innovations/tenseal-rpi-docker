# TenSEAL on Raspberry Pi ARM64 with Docker

A minimal Docker-based setup for building and running TenSEAL on a 64-bit Raspberry Pi without requiring `sudo` access or host-level build dependencies.

The image builds TenSEAL from source because precompiled ARM64 Python wheels are not currently provided.

## Features

- Native ARM64/aarch64 build
- TenSEAL 0.3.17
- Python 3.11
- CKKS support
- No host-level compiler or `sudo` required
- Reusable Docker base image
- Supports running local Python scripts through bind mounts
- Optional ARM64 wheel export

## Requirements

- Raspberry Pi with a 64-bit operating system
- `aarch64`/`arm64` architecture
- Docker access as a non-root user
- Git

Verify the architecture:

```bash
uname -m
docker version --format '{{.Server.Arch}}'
```

Expected output:

```
aarch64
arm64
```

## Repository structure

```
.
├── Dockerfile.tenseal
├── main.py
├── README.md
└── LICENSE
```

## Build the TenSEAL image

For Raspberry Pis with limited memory, use one compilation job:

```bash
docker build \
  --progress=plain \
  --build-arg BUILD_JOBS=1 \
  -f Dockerfile.tenseal \
  -t tenseal-rpi:0.3.17 \
  .
```

Compilation can take some time because TenSEAL, Microsoft SEAL and their native dependencies are built from source.

## Verify the installation

```bash
docker run --rm tenseal-rpi:0.3.17 python -c '
import platform
import tenseal as ts
print("Architecture:", platform.machine())
print("TenSEAL:", ts.__version__)
context = ts.context(
    ts.SCHEME_TYPE.CKKS,
    poly_modulus_degree=8192,
    coeff_mod_bit_sizes=[60, 40, 40, 60],
)
context.global_scale = 2**40
encrypted = ts.ckks_vector(context, [1.0, 2.0])
print((encrypted + 1.0).decrypt())
'
```

Example output:

```
Architecture: aarch64
TenSEAL: 0.3.17
[1.9999999999, 3.0000000013]
```

Small deviations from exact values are expected because CKKS performs approximate arithmetic.

## Run the local example

The source file remains directly on the Raspberry Pi and is mounted into the container:

```bash
docker run --rm -it \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "$PWD:/app" \
  -w /app \
  tenseal-rpi:0.3.17 \
  python main.py
```

You can edit `main.py` normally and rerun this command without rebuilding the image.

## Use it as an application base image

Another Dockerfile can inherit from the locally built image:

```dockerfile
FROM tenseal-rpi:0.3.17

WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## Export the ARM64 wheel

If the Dockerfile contains the `wheel` build target:

```bash
DOCKER_BUILDKIT=1 docker build \
  --target wheel \
  --build-arg BUILD_JOBS=1 \
  --output type=local,dest=./dist \
  -f Dockerfile.tenseal \
  .
```

The generated wheel is compatible with ARM64 and the corresponding CPython version.

## Transfer the image to another Raspberry Pi

Export:

```bash
docker save tenseal-rpi:0.3.17 | gzip > tenseal-rpi-0.3.17.tar.gz
```

Import on another ARM64 Raspberry Pi:

```bash
gzip -dc tenseal-rpi-0.3.17.tar.gz | docker load
```

## Troubleshooting

### Build process is killed

Messages such as `Killed`, `cc1plus: fatal error` or exit code `137` normally indicate insufficient memory.

Use:

```bash
--build-arg BUILD_JOBS=1
```

### NEON instruction set not supported

This commonly indicates a 32-bit ARM operating system. The recommended setup requires a 64-bit kernel reporting `aarch64`.

### Python version error

TenSEAL 0.3.17 requires Python 3.11 or newer. This repository uses `python:3.11-slim-bookworm`.

## Upstream project

TenSEAL is developed by OpenMined:

- https://github.com/OpenMined/TenSEAL

