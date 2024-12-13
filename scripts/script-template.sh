#!/bin/zsh
#
# Script Name: script-template.sh
# Description: Template for shell scripts
# Author: $(git config user.name)
# Date Created: $(date +%Y-%m-%d)
# Last Modified: $(date +%Y-%m-%d)
#
# Usage: script-template.sh [options]
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
    if (( $debug == 1 )); then
        print_debug "Debug mode enabled"
    fi

    # Your script logic here


    if (( ${#args} == 0 )); then
        print_warning "No arguments provided"
    else
        print_info "Arguments: ${args[@]}"
    fi

    print_info "Script completed"
}

# Run main function if script is not sourced
if [[ ! -o NO_EXEC ]]; then
    main "$@"
fi
