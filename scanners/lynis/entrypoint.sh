set -euo pipefail
IFS=' ' read -r -a targets <<< "${TARGET_CONTAINERS:-}"
if [ ${#targets[@]} -eq 0 ]; then
  exit 1


  local name="$1"
    target-fedora)
      ;;
      docker exec "$name" sh -c "dnf -y update && dnf -y install epel-release && dnf -y install lynis"
    target-debian|target-ubuntu)
      ;;
      echo "Unknown container $name for Lynis install" >&2
      ;;
}
audit_container() {
  local logfile="/reports/lynis/${name}.log"
  if ! docker exec "$name" lynis audit system --quiet --logfile /tmp/lynis.log --report-file /tmp/lynis-report.dat; then
    return 1
  docker cp "${name}:/tmp/lynis.log" "$logfile" >/dev/null 2>&1 || docker exec "$name" cat /tmp/lynis.log > "$logfile"
}
status=0
for target in "${targets[@]}"; do
    status=1
  fi
    status=1
done
exit $status
