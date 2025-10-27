#!/usr/bin/env bash
set -euo pipefail

IFS=' ' read -r -a targets <<< "${TARGET_CONTAINERS:-}"

if [ ${#targets[@]} -eq 0 ]; then
  echo "No target containers provided via TARGET_CONTAINERS" >&2
  exit 1
fi

mkdir -p /reports/openscap

scan_container() {
  local name="$1"
  local datastream
  local profile="xccdf_org.ssgproject.content_profile_standard"

  case "$name" in
    target-fedora)
      datastream="/usr/share/xml/scap/ssg/content/ssg-fedora-ds.xml"
      ;;
    target-debian)
      datastream="/usr/share/xml/scap/ssg/content/ssg-debian12-ds.xml"
      ;;
    target-centos)
      datastream="/usr/share/xml/scap/ssg/content/ssg-centos9-ds.xml"
      ;;
    target-ubuntu)
      datastream="/usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml"
      ;;
    *)
      echo "No datastream known for ${name}, skipping" >&2
      return 1
      ;;
  esac

  if [ ! -f "$datastream" ]; then
    echo "Datastream $datastream not found for ${name}, skipping" >&2
    return 1
  fi

  local result="/reports/openscap/${name}.xml"
  local report="/reports/openscap/${name}.html"

  echo "[OpenSCAP] Scanning ${name} using ${datastream}" >&2

  if ! oscap-docker container "$name" xccdf eval \
      --profile "$profile" \
      --fetch-remote-resources \
      --results "$result" \
      --report "$report" \
      "$datastream"; then
    echo "OpenSCAP scan failed for ${name}" >&2
    return 1
  fi
}

status=0

for target in "${targets[@]}"; do
  if ! scan_container "$target"; then
    status=1
  fi
done

exit $status
