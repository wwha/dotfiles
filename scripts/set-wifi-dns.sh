#!/bin/zsh
#
# Script Name: set_dns.sh
# Description: Set wifi dns to manual or dhcp
# Author: wwha
# Date Created: 2024-12-07
# Last Modified: 2024-12-07
#
# Usage: set_dns.sh [options]
# Options:
#   -h, --help     Show this help message
#   -v, --version  Show version information

# Strict mode
set -euo pipefail
IFS=$'\n\t'

# Script version
VERSION="1.0.0"

# Colors for output
autoload -U colors && colors

# Helper functions
print_error() { echo "${fg[red]}ERROR:${reset_color} $1" >&2 }
print_warning() { echo "${fg[yellow]}WARNING:${reset_color} $1" >&2 }
print_info() { echo "${fg[green]}INFO:${reset_color} $1" }
print_debug() { echo "${fg[blue]}DEBUG:${reset_color} $1" }

# Usage information
usage() {
    cat << HELP
Usage: ${0:t} [options]

Options:
    -h, --help     Show this help message
    -v, --version  Show version information
    -d, --debug    Enable debug output
    manual         Set dns to manual
    dhcp           Set dns to dhcp
HELP
}

# Version information
version() {
    echo "${0:t} version $VERSION"
}

# Main function
main() {
    local -a args
    local debug=0

    # Parse arguments
    while (( $# > 0 )); do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--version)
                version
                exit 0
                ;;
            -d|--debug)
                debug=1
                shift
                continue
                ;;
            dhcp)
                sudo networksetup -setdhcp "Wi-Fi"
                sudo networksetup -setdnsservers "Wi-Fi" "empty"
                ;;
            manual)
                sudo networksetup -setmanual "Wi-Fi" 10.99.1.143 255.255.255.0 10.99.1.189
                sudo networksetup -setdnsservers "Wi-Fi" 198.18.0.2
                ;;
            --)
                shift
                args+=("$@")
                break
                ;;
            -*)
                print_error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                args+=("$1")
                ;;
        esac
        shift
    done

    # Export debug setting
    export DEBUG=$debug

    print_info "Script started"

    # Your script logic here

    print_info "Script completed"
}

# # Execute main function
# main "$@" || {
#     print_error "Script failed"
#     exit 1
# }
# Run main function if script is not sourced
if [[ ! -o NO_EXEC ]]; then
    main "$@"
fi
