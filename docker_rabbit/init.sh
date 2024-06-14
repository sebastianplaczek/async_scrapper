#!/bin/bash
set -e

# Dodanie użytkownika
rabbitmqctl add_user user1 user1 || true

# Nadanie użytkownikowi roli administratora
rabbitmqctl set_user_tags user1 administrator

# Dodanie vhost
rabbitmqctl add_vhost vhost1 || true

# Nadanie uprawnień użytkownikowi do vhost
rabbitmqctl set_permissions -p vhost1 user1 ".*" ".*" ".*"

# Sprawdzenie, czy użytkownik istnieje
rabbitmqctl list_users

# Sprawdzenie, czy vhost istnieje
rabbitmqctl list_vhosts

# Sprawdzenie uprawnień użytkownika
rabbitmqctl list_permissions -p vhost1