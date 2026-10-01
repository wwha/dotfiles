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
