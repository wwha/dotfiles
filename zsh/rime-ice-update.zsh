# Monthly Rime Ice update reminder, similar to oh-my-zsh's update prompt.
rime_ice_update() {
    local rime_plum_dir="$HOME/Library/Rime/plum"

    if [[ ! -x "$rime_plum_dir/rime-install" ]]; then
        echo "Rime plum installer not found at $rime_plum_dir/rime-install"
        return 1
    fi

    (
        cd "$rime_plum_dir" || exit 1
        bash rime-install iDvel/rime-ice:others/recipes/full
    )
}

_rime_ice_update_check() {
    [[ -o interactive ]] || return

    local update_file="${XDG_CACHE_HOME:-$HOME/.cache}/rime-ice-update-last"
    local update_frequency_days=30
    local now last_update elapsed_days reply

    now=$(date +%s)
    if [[ -f "$update_file" ]]; then
        last_update=$(<"$update_file")
    else
        last_update=0
    fi

    if ! [[ "$last_update" == <-> ]]; then
        last_update=0
    fi

    elapsed_days=$(( (now - last_update) / 86400 ))
    (( elapsed_days < update_frequency_days )) && return

    echo "Rime Ice configurations have not been checked for updates in $elapsed_days days."
    printf "Update now? [y/N] "
    read -r reply

    case "$reply" in
        [Yy]*)
            rime_ice_update && mkdir -p "${update_file:h}" && date +%s >| "$update_file"
            ;;
        *)
            mkdir -p "${update_file:h}" && date +%s >| "$update_file"
            ;;
    esac
}

_rime_ice_update_check
