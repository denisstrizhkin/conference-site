#!/usr/bin/env sh

img_name="conference-site"
http_port=8080

build() {
    podman build -f container/Containerfile --tag "${img_name}" .
}

run() {
    podman run --rm -it \
        -p "${http_port}:80" \
        -v "${img_name}-db:/data" \
        "${img_name}:latest"
}

create_volume() {
    podman volume create "${img_name}-db"
}

$1
