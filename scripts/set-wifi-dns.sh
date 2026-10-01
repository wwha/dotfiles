#!/bin/zsh
#
# Script Name: set_dns.sh
# Description: Set wifi dns to manual or dhcp
# Author: wwha
# Date Created: 2024-12-07
# Last Modified: 2024-12-07
#
# Usage: set-wifi-dns.sh dhcp <interface>
#        set-wifi-dns.sh manual <interface> <address> <subnet-mask> <router> <dns> [dns ...]

# Strict mode
set -euo pipefail
IFS=$'\n\t'

# Script version
VERSION="1.0.0"

print_error() { print -u2 -- "ERROR: $1" }

# Usage information
usage() {
    cat << HELP
Usage: ${0:t} dhcp <interface>
       ${0:t} manual <interface> <address> <subnet-mask> <router> <dns> [dns ...]

Options:
    -h, --help     Show this help message
    -v, --version  Show version information
HELP
}

# Version information
version() {
    echo "${0:t} version $VERSION"
}

# Main function
main() {
    local mode=${1:-}
    case "$mode" in
        -h|--help) usage; return 0 ;;
        -v|--version) version; return 0 ;;
        dhcp)
            (( $# == 2 )) || { print_error 'dhcp requires exactly one interface name'; return 2; }
            [[ "$2" != -* && "$2" != *$'\n'* ]] || { print_error 'invalid interface name'; return 2; }
            sudo networksetup -setdhcp "$2"
            sudo networksetup -setdnsservers "$2" empty
            ;;
        manual)
            (( $# >= 6 )) || { print_error 'manual requires interface, address, subnet mask, router, and at least one DNS server'; return 2; }
            local interface=$2 value octet
            shift 2
            [[ "$interface" != -* && "$interface" != *$'\n'* ]] || { print_error 'invalid interface name'; return 2; }
            for value in "$@"; do
                [[ "$value" == <->.<->.<->.<-> ]] || { print_error "invalid IPv4 address: $value"; return 2; }
                for octet in ${(s:.:)value}; do
                    (( 10#$octet <= 255 )) || { print_error "invalid IPv4 address: $value"; return 2; }
                done
            done
            local address=$1 subnet=$2 router=$3
            shift 3
            sudo networksetup -setmanual "$interface" "$address" "$subnet" "$router"
            sudo networksetup -setdnsservers "$interface" "$@"
            ;;
        *) print_error 'expected dhcp or manual'; usage >&2; return 2 ;;
    esac
}

main "$@"
